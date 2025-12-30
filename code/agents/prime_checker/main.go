package main

import (
	"bytes"
	"container/list"
	"context"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"math/bits"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"

	bolt "go.etcd.io/bbolt"
)

const (
	defaultPort              = "5000"
	defaultDBPath            = "/app/data/prime_cache.db"
	defaultMaxDigits         = 1000
	defaultMaxBodyBytes      = 1 << 20
	defaultCacheSize         = 10000
	defaultYAFUPath          = "/usr/local/bin/yafu"
	defaultYAFUWorkDir       = "/opt/math/yafu"
	defaultYAFUPrimeTimeout  = 5 * time.Second
	defaultYAFUFactorTimeout = 8 * time.Second
	defaultYAFUConcurrency   = 2
	defaultYAFUFactorDigits  = 60
	defaultFactorDBTimeout   = 10 * time.Second
	defaultFactorDBRetries   = 2
	defaultFactorDBBackoff   = 500 * time.Millisecond
	defaultSmallFactorLimit  = uint64(1_000_000_000_000)
	defaultHealthCacheTTL    = 30 * time.Second
)

var (
	digitOnly = regexp.MustCompile(`^\d+$`)
)

var ErrYAFUFactorsUnavailable = errors.New("yafu factors unavailable")

type Config struct {
	Port                string
	DBPath              string
	MaxDigits           int
	MaxBodyBytes        int64
	CacheSize           int
	YAFUPath            string
	YAFUWorkDir         string
	YAFUPrimeTimeout    time.Duration
	YAFUFactorTimeout   time.Duration
	YAFUConcurrency     int
	YAFUFactorMaxDigits int
	FactorDBTimeout     time.Duration
	FactorDBRetries     int
	FactorDBBackoff     time.Duration
	SmallFactorLimit    uint64
	HealthCacheTTL      time.Duration
	EnableFactorDB      bool
}

type PrimeResult struct {
	Number    string   `json:"number,omitempty"`
	IsPrime   bool     `json:"is_prime"`
	Factors   []string `json:"factors,omitempty"`
	Source    string   `json:"source,omitempty"`
	Cached    bool     `json:"cached,omitempty"`
	LatencyMs int64    `json:"latency_ms,omitempty"`
	Note      string   `json:"note,omitempty"`
}

type HistoryItem struct {
	Number    string   `json:"number"`
	IsPrime   bool     `json:"is_prime"`
	Factors   []string `json:"factors,omitempty"`
	Source    string   `json:"source,omitempty"`
	UpdatedAt int64    `json:"updated_at"`
	HitCount  int      `json:"hit_count"`
}

type ErrorResponse struct {
	Error string `json:"error"`
}

type Server struct {
	cfg       Config
	store     *Store
	cache     *LRUCache
	yafuSem   chan struct{}
	factordb  *FactorDBClient
	health    *HealthChecker
	startedAt time.Time
}

func main() {
	cfg := loadConfig()

	store, err := NewStore(cfg.DBPath)
	if err != nil {
		log.Fatalf("store init failed: %v", err)
	}

	cache := NewLRUCache(cfg.CacheSize)
	yafuSem := make(chan struct{}, cfg.YAFUConcurrency)

	factordb := NewFactorDBClient(cfg.FactorDBTimeout, cfg.FactorDBRetries, cfg.FactorDBBackoff)

	srv := &Server{
		cfg:       cfg,
		store:     store,
		cache:     cache,
		yafuSem:   yafuSem,
		factordb:  factordb,
		health:    &HealthChecker{},
		startedAt: time.Now(),
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/isprime", srv.handleIsPrime)
	mux.HandleFunc("/health", srv.handleHealth)
	mux.HandleFunc("/stats", srv.handleStats)
	mux.HandleFunc("/history", srv.handleHistory)

	httpServer := &http.Server{
		Addr:              ":" + cfg.Port,
		Handler:           corsMiddleware(loggingMiddleware(mux)),
		ReadTimeout:       10 * time.Second,
		ReadHeaderTimeout: 5 * time.Second,
		WriteTimeout:      20 * time.Second,
		IdleTimeout:       60 * time.Second,
		MaxHeaderBytes:    1 << 20,
	}

	log.Printf("Prime checker starting on :%s", cfg.Port)
	if err := httpServer.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
		log.Fatalf("server failed: %v", err)
	}
}

func loadConfig() Config {
	cfg := Config{
		Port:                envString("PORT", defaultPort),
		DBPath:              envString("DB_PATH", defaultDBPath),
		MaxDigits:           envInt("MAX_DIGITS", defaultMaxDigits),
		MaxBodyBytes:        envInt64("MAX_BODY_BYTES", defaultMaxBodyBytes),
		CacheSize:           envInt("CACHE_SIZE", defaultCacheSize),
		YAFUPath:            envString("YAFU_PATH", defaultYAFUPath),
		YAFUWorkDir:         envString("YAFU_WORKDIR", defaultYAFUWorkDir),
		YAFUPrimeTimeout:    envDuration("YAFU_PRIME_TIMEOUT_MS", defaultYAFUPrimeTimeout),
		YAFUFactorTimeout:   envDuration("YAFU_FACTOR_TIMEOUT_MS", defaultYAFUFactorTimeout),
		YAFUConcurrency:     envInt("YAFU_CONCURRENCY", defaultYAFUConcurrency),
		YAFUFactorMaxDigits: envInt("YAFU_FACTOR_MAX_DIGITS", defaultYAFUFactorDigits),
		FactorDBTimeout:     envDuration("FACTORDB_TIMEOUT_MS", defaultFactorDBTimeout),
		FactorDBRetries:     envInt("FACTORDB_RETRIES", defaultFactorDBRetries),
		FactorDBBackoff:     envDuration("FACTORDB_BACKOFF_MS", defaultFactorDBBackoff),
		SmallFactorLimit:    envUint64("SMALL_FACTOR_LIMIT", defaultSmallFactorLimit),
		HealthCacheTTL:      envDuration("HEALTH_CACHE_TTL_MS", defaultHealthCacheTTL),
		EnableFactorDB:      envBool("ENABLE_FACTORDB", true),
	}

	if cfg.YAFUConcurrency < 1 {
		cfg.YAFUConcurrency = 1
	}
	if cfg.CacheSize < 0 {
		cfg.CacheSize = 0
	}
	return cfg
}

func envString(key, def string) string {
	if val := strings.TrimSpace(os.Getenv(key)); val != "" {
		return val
	}
	return def
}

func envInt(key string, def int) int {
	val := strings.TrimSpace(os.Getenv(key))
	if val == "" {
		return def
	}
	parsed, err := strconv.Atoi(val)
	if err != nil {
		return def
	}
	return parsed
}

func envInt64(key string, def int64) int64 {
	val := strings.TrimSpace(os.Getenv(key))
	if val == "" {
		return def
	}
	parsed, err := strconv.ParseInt(val, 10, 64)
	if err != nil {
		return def
	}
	return parsed
}

func envUint64(key string, def uint64) uint64 {
	val := strings.TrimSpace(os.Getenv(key))
	if val == "" {
		return def
	}
	parsed, err := strconv.ParseUint(val, 10, 64)
	if err != nil {
		return def
	}
	return parsed
}

func envBool(key string, def bool) bool {
	val := strings.TrimSpace(os.Getenv(key))
	if val == "" {
		return def
	}
	parsed, err := strconv.ParseBool(val)
	if err != nil {
		return def
	}
	return parsed
}

func envDuration(key string, def time.Duration) time.Duration {
	val := strings.TrimSpace(os.Getenv(key))
	if val == "" {
		return def
	}
	ms, err := strconv.Atoi(val)
	if err != nil || ms < 0 {
		return def
	}
	return time.Duration(ms) * time.Millisecond
}

func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		log.Printf("%s %s %s", r.Method, r.URL.Path, time.Since(start))
	})
}

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}

		next.ServeHTTP(w, r)
	})
}

func (s *Server) handleIsPrime(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeJSON(w, http.StatusMethodNotAllowed, ErrorResponse{Error: "Method not allowed"})
		return
	}

	start := time.Now()
	ctx := r.Context()

	r.Body = http.MaxBytesReader(w, r.Body, s.cfg.MaxBodyBytes)
	defer r.Body.Close()

	number, err := decodeNumber(r.Body)
	if err != nil {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: err.Error()})
		return
	}

	number, err = validateNumber(number, s.cfg.MaxDigits)
	if err != nil {
		writeJSON(w, http.StatusBadRequest, ErrorResponse{Error: err.Error()})
		return
	}

	if res, ok := s.cache.Get(number); ok {
		res.Number = number
		res.Cached = true
		res.LatencyMs = time.Since(start).Milliseconds()
		writeJSON(w, http.StatusOK, res)
		return
	}

	if res, ok, dbErr := s.store.Get(number); dbErr == nil && ok {
		res.Number = number
		res.Cached = true
		res.LatencyMs = time.Since(start).Milliseconds()
		s.cache.Add(number, res)
		writeJSON(w, http.StatusOK, res)
		return
	} else if dbErr != nil {
		log.Printf("db read error for %s: %v", number, dbErr)
	}

	res, err := s.computePrime(ctx, number)
	if err != nil {
		writeJSON(w, http.StatusBadGateway, ErrorResponse{Error: err.Error()})
		return
	}

	res.Number = number
	res.LatencyMs = time.Since(start).Milliseconds()

	if storeErr := s.store.Put(number, res); storeErr != nil {
		log.Printf("db write error for %s: %v", number, storeErr)
	}
	s.cache.Add(number, res)

	writeJSON(w, http.StatusOK, res)
}

func (s *Server) computePrime(ctx context.Context, number string) (PrimeResult, error) {
	if n, ok := parseUint64(number); ok {
		if n <= 3 {
			return PrimeResult{IsPrime: n >= 2, Source: "local"}, nil
		}
		if n <= s.cfg.SmallFactorLimit {
			factors := factorSmall(n)
			if len(factors) == 1 {
				return PrimeResult{IsPrime: true, Source: "local"}, nil
			}
			return PrimeResult{IsPrime: false, Factors: uint64SliceToStrings(factors), Source: "local"}, nil
		}
		if isPrime64(n) {
			return PrimeResult{IsPrime: true, Source: "local"}, nil
		}
	}

	if res, err := s.checkWithYAFU(ctx, number); err == nil {
		return res, nil
	} else if errors.Is(err, ErrYAFUFactorsUnavailable) {
		if s.cfg.EnableFactorDB {
			fdbRes, fdbErr := s.factordb.Query(ctx, number)
			if fdbErr == nil {
				if fdbRes.IsPrime {
					log.Printf("FactorDB returned prime for %s after YAFU composite", number)
					return res, nil
				}
				return fdbRes, nil
			}
			log.Printf("FactorDB fallback failed for %s: %v", number, fdbErr)
		}
		return res, nil
	}

	if !s.cfg.EnableFactorDB {
		return PrimeResult{}, fmt.Errorf("local check failed and FactorDB disabled")
	}

	res, err := s.factordb.Query(ctx, number)
	if err != nil {
		return PrimeResult{}, err
	}
	return res, nil
}

func (s *Server) checkWithYAFU(ctx context.Context, number string) (PrimeResult, error) {
	if _, err := os.Stat(s.cfg.YAFUPath); err != nil {
		return PrimeResult{}, fmt.Errorf("YAFU not available")
	}

	primeCtx, cancel := context.WithTimeout(ctx, s.cfg.YAFUPrimeTimeout)
	defer cancel()

	if err := s.acquireYAFU(primeCtx); err != nil {
		return PrimeResult{}, err
	}
	stdout, stderr, exitCode, err := runYAFU(primeCtx, s.cfg.YAFUPath, s.cfg.YAFUWorkDir, fmt.Sprintf("isprime(%s)", number))
	s.releaseYAFU()
	if err != nil {
		log.Printf("YAFU isprime error: %v", err)
		return PrimeResult{}, err
	}
	if exitCode != 0 {
		return PrimeResult{}, fmt.Errorf("YAFU isprime failed: %s", stderr)
	}

	isPrime, isComposite := parseYAFUPrime(stdout)
	if isPrime {
		return PrimeResult{IsPrime: true, Source: "yafu"}, nil
	}
	if !isComposite {
		return PrimeResult{}, fmt.Errorf("YAFU returned unknown result")
	}

	if len(number) > s.cfg.YAFUFactorMaxDigits {
		return PrimeResult{IsPrime: false, Source: "yafu", Note: "Composite; factors skipped"}, ErrYAFUFactorsUnavailable
	}

	factorCtx, cancelFactor := context.WithTimeout(ctx, s.cfg.YAFUFactorTimeout)
	defer cancelFactor()

	if err := s.acquireYAFU(factorCtx); err != nil {
		return PrimeResult{}, err
	}
	factorOut, factorErr, factorExit, err := runYAFU(factorCtx, s.cfg.YAFUPath, s.cfg.YAFUWorkDir, fmt.Sprintf("factor(%s)", number))
	s.releaseYAFU()
	if err != nil {
		log.Printf("YAFU factor error: %v", err)
		return PrimeResult{IsPrime: false, Source: "yafu", Note: "Composite; factorization failed"}, ErrYAFUFactorsUnavailable
	}
	if factorExit != 0 {
		if factorErr != "" {
			log.Printf("YAFU factor stderr: %s", factorErr)
		}
		return PrimeResult{IsPrime: false, Source: "yafu", Note: "Composite; factorization failed"}, ErrYAFUFactorsUnavailable
	}

	factors := parseYAFUFactors(factorOut)
	if len(factors) == 0 {
		return PrimeResult{IsPrime: false, Source: "yafu", Note: "Composite; factors unavailable"}, ErrYAFUFactorsUnavailable
	}
	return PrimeResult{IsPrime: false, Factors: factors, Source: "yafu"}, nil
}

func (s *Server) acquireYAFU(ctx context.Context) error {
	select {
	case s.yafuSem <- struct{}{}:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

func (s *Server) releaseYAFU() {
	select {
	case <-s.yafuSem:
	default:
	}
}

func runYAFU(ctx context.Context, path, workDir, command string) (string, string, int, error) {
	cmd := execCommand(ctx, path)
	cmd.Dir = workDir
	cmd.Stdin = strings.NewReader(command + "\n")
	cmd.Env = append(os.Environ(), "LD_LIBRARY_PATH=/opt/math/gmp/lib:/opt/math/gmp-ecm/lib")

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err := cmd.Run()
	if err != nil {
		if errors.Is(ctx.Err(), context.DeadlineExceeded) {
			return stdout.String(), stderr.String(), -1, fmt.Errorf("YAFU timeout")
		}
		return stdout.String(), stderr.String(), -1, err
	}
	return stdout.String(), stderr.String(), 0, nil
}

func parseYAFUPrime(output string) (bool, bool) {
	if strings.Contains(output, "ans = 1") {
		return true, false
	}
	if strings.Contains(output, "ans = 0") {
		return false, true
	}
	return false, false
}

func parseYAFUFactors(output string) []string {
	var factors []string
	lines := strings.Split(output, "\n")
	factorPattern := regexp.MustCompile(`^(PRP|P)\d+\s*=\s*(\d+)`)
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		if match := factorPattern.FindStringSubmatch(line); len(match) == 3 {
			factors = append(factors, match[2])
		}
	}
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if strings.Contains(strings.ToLower(line), "factor:") {
			parts := strings.Split(line, ":")
			if len(parts) == 2 {
				candidate := strings.TrimSpace(parts[1])
				if digitOnly.MatchString(candidate) {
					factors = append(factors, candidate)
				}
			}
		}
	}
	return factors
}

func parseUint64(number string) (uint64, bool) {
	if len(number) > 20 {
		return 0, false
	}
	val, err := strconv.ParseUint(number, 10, 64)
	if err != nil {
		return 0, false
	}
	return val, true
}

func factorSmall(n uint64) []uint64 {
	if n < 2 {
		return nil
	}
	var factors []uint64
	for n%2 == 0 {
		factors = append(factors, 2)
		n /= 2
	}
	for n%3 == 0 {
		factors = append(factors, 3)
		n /= 3
	}
	for i := uint64(5); i*i <= n; i += 6 {
		for n%i == 0 {
			factors = append(factors, i)
			n /= i
		}
		for n%(i+2) == 0 {
			factors = append(factors, i+2)
			n /= i + 2
		}
	}
	if n > 1 {
		factors = append(factors, n)
	}
	return factors
}

func uint64SliceToStrings(values []uint64) []string {
	out := make([]string, 0, len(values))
	for _, v := range values {
		out = append(out, strconv.FormatUint(v, 10))
	}
	return out
}

func isPrime64(n uint64) bool {
	if n < 2 {
		return false
	}
	if n%2 == 0 {
		return n == 2
	}
	if n%3 == 0 {
		return n == 3
	}
	if n < 25 {
		return true
	}

	// Deterministic bases for 64-bit integers.
	bases := []uint64{2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37}

	d := n - 1
	s := 0
	for d%2 == 0 {
		d /= 2
		s++
	}

	for _, a := range bases {
		if a >= n {
			continue
		}
		x := modPow(a, d, n)
		if x == 1 || x == n-1 {
			continue
		}
		composite := true
		for r := 1; r < s; r++ {
			x = mulMod(x, x, n)
			if x == n-1 {
				composite = false
				break
			}
		}
		if composite {
			return false
		}
	}

	return true
}

func mulMod(a, b, mod uint64) uint64 {
	hi, lo := bits.Mul64(a, b)
	_, rem := bits.Div64(hi, lo, mod)
	return rem
}

func modPow(base, exp, mod uint64) uint64 {
	result := uint64(1)
	base %= mod
	for exp > 0 {
		if exp&1 == 1 {
			result = mulMod(result, base, mod)
		}
		base = mulMod(base, base, mod)
		exp >>= 1
	}
	return result
}

func decodeNumber(reader io.Reader) (string, error) {
	var payload struct {
		Number json.RawMessage `json:"number"`
	}

	dec := json.NewDecoder(reader)
	if err := dec.Decode(&payload); err != nil {
		return "", fmt.Errorf("Invalid JSON payload")
	}
	if len(payload.Number) == 0 {
		return "", fmt.Errorf("Missing 'number' field in JSON payload")
	}
	return parseNumberField(payload.Number)
}

func parseNumberField(raw json.RawMessage) (string, error) {
	trimmed := bytes.TrimSpace(raw)
	if len(trimmed) == 0 || bytes.Equal(trimmed, []byte("null")) {
		return "", fmt.Errorf("Missing 'number' field in JSON payload")
	}

	if trimmed[0] == '"' {
		var val string
		if err := json.Unmarshal(trimmed, &val); err != nil {
			return "", fmt.Errorf("Invalid number field")
		}
		return val, nil
	}

	if bytes.ContainsAny(trimmed, ".eE+-") {
		return "", fmt.Errorf("Input must contain only digits")
	}

	return string(trimmed), nil
}

func validateNumber(number string, maxDigits int) (string, error) {
	number = strings.TrimSpace(number)
	if number == "" {
		return "", fmt.Errorf("Input must contain only digits")
	}
	if !digitOnly.MatchString(number) {
		return "", fmt.Errorf("Input must contain only digits")
	}

	normalized := strings.TrimLeft(number, "0")
	if normalized == "" {
		normalized = "0"
	}

	if normalized == "0" {
		return "", fmt.Errorf("Zero is neither prime nor composite")
	}
	if normalized == "1" {
		return "", fmt.Errorf("One is neither prime nor composite by definition")
	}
	if len(normalized) > maxDigits {
		return "", fmt.Errorf("Number too large (max %d digits)", maxDigits)
	}

	return normalized, nil
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	enc := json.NewEncoder(w)
	if err := enc.Encode(payload); err != nil {
		log.Printf("json encode error: %v", err)
	}
}

type FactorDBClient struct {
	client  *http.Client
	retries int
	backoff time.Duration
}

func NewFactorDBClient(timeout time.Duration, retries int, backoff time.Duration) *FactorDBClient {
	transport := &http.Transport{
		DialContext: (&net.Dialer{
			Timeout:   5 * time.Second,
			KeepAlive: 30 * time.Second,
		}).DialContext,
		MaxIdleConns:        50,
		MaxIdleConnsPerHost: 10,
		IdleConnTimeout:     90 * time.Second,
		TLSHandshakeTimeout: 5 * time.Second,
	}
	return &FactorDBClient{
		client: &http.Client{
			Transport: transport,
			Timeout:   timeout,
		},
		retries: retries,
		backoff: backoff,
	}
}

type factorDBResponse struct {
	Status  string              `json:"status"`
	Factors [][]json.RawMessage `json:"factors"`
}

func (f *FactorDBClient) Query(ctx context.Context, number string) (PrimeResult, error) {
	url := "https://factordb.com/api?query=" + number

	var lastErr error
	for attempt := 0; attempt <= f.retries; attempt++ {
		req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
		if err != nil {
			return PrimeResult{}, err
		}

		resp, err := f.client.Do(req)
		if err != nil {
			lastErr = err
			if attempt < f.retries {
				time.Sleep(f.backoff * time.Duration(1<<attempt))
				continue
			}
			return PrimeResult{}, fmt.Errorf("FactorDB request failed: %v", err)
		}

		if resp.Body == nil {
			return PrimeResult{}, fmt.Errorf("FactorDB empty response")
		}
		if resp.StatusCode != http.StatusOK {
			resp.Body.Close()
			lastErr = fmt.Errorf("FactorDB status %d", resp.StatusCode)
			if attempt < f.retries {
				time.Sleep(f.backoff * time.Duration(1<<attempt))
				continue
			}
			return PrimeResult{}, fmt.Errorf("FactorDB request failed: %v", lastErr)
		}

		var data factorDBResponse
		dec := json.NewDecoder(resp.Body)
		decodeErr := dec.Decode(&data)
		resp.Body.Close()
		if decodeErr != nil {
			lastErr = decodeErr
			if attempt < f.retries {
				time.Sleep(f.backoff * time.Duration(1<<attempt))
				continue
			}
			return PrimeResult{}, fmt.Errorf("FactorDB response parse failed")
		}

		status := strings.ToUpper(strings.TrimSpace(data.Status))
		switch status {
		case "P":
			return PrimeResult{IsPrime: true, Source: "factordb"}, nil
		case "C", "CF", "FF":
			factors := extractFactorDBFactors(data.Factors)
			if len(factors) == 0 {
				return PrimeResult{IsPrime: false, Source: "factordb", Note: "Composite but factors unavailable"}, nil
			}
			if len(factors) == 1 && factors[0] == number {
				return PrimeResult{IsPrime: false, Source: "factordb", Note: "Composite but factors unavailable"}, nil
			}
			return PrimeResult{IsPrime: false, Factors: factors, Source: "factordb"}, nil
		case "U":
			return PrimeResult{}, fmt.Errorf("FactorDB reports unknown status")
		default:
			return PrimeResult{}, fmt.Errorf("FactorDB returned status %s", status)
		}
	}

	if lastErr != nil {
		return PrimeResult{}, fmt.Errorf("FactorDB request failed: %v", lastErr)
	}
	return PrimeResult{}, fmt.Errorf("FactorDB request failed")
}

func extractFactorDBFactors(raw [][]json.RawMessage) []string {
	var factors []string
	for _, pair := range raw {
		if len(pair) < 2 {
			continue
		}
		factorStr, ok := parseFactorDBValue(pair[0])
		if !ok {
			continue
		}
		exp, ok := parseFactorDBExponent(pair[1])
		if !ok || exp < 1 {
			continue
		}
		for i := 0; i < exp; i++ {
			factors = append(factors, factorStr)
		}
	}
	return factors
}

func parseFactorDBValue(raw json.RawMessage) (string, bool) {
	var valStr string
	if err := json.Unmarshal(raw, &valStr); err == nil {
		if digitOnly.MatchString(valStr) {
			return valStr, true
		}
	}
	var valNum json.Number
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber()
	if err := dec.Decode(&valNum); err == nil {
		if digitOnly.MatchString(valNum.String()) {
			return valNum.String(), true
		}
	}
	return "", false
}

func parseFactorDBExponent(raw json.RawMessage) (int, bool) {
	var exp int
	if err := json.Unmarshal(raw, &exp); err == nil {
		return exp, true
	}
	var expStr string
	if err := json.Unmarshal(raw, &expStr); err == nil {
		parsed, err := strconv.Atoi(expStr)
		if err == nil {
			return parsed, true
		}
	}
	return 0, false
}

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	yafuAvailable := false
	if _, err := os.Stat(s.cfg.YAFUPath); err == nil {
		yafuAvailable = true
	}

	factordbOK := false
	if s.cfg.EnableFactorDB {
		factordbOK = s.health.CheckFactorDB(r.Context(), s.factordb, s.cfg.HealthCacheTTL)
	}

	status := "healthy"
	if !yafuAvailable && !factordbOK {
		status = "unhealthy"
	} else if !yafuAvailable || !factordbOK {
		status = "degraded"
	}

	payload := map[string]any{
		"status":              status,
		"yafu_available":      yafuAvailable,
		"factordb_accessible": factordbOK,
		"timestamp":           time.Now().Unix(),
	}

	code := http.StatusOK
	if status == "unhealthy" {
		code = http.StatusServiceUnavailable
	}
	writeJSON(w, code, payload)
}

func (s *Server) handleStats(w http.ResponseWriter, r *http.Request) {
	count, err := s.store.Count()
	if err != nil {
		log.Printf("stats count error: %v", err)
	}

	payload := map[string]any{
		"cache_entries": s.cache.Len(),
		"db_entries":    count,
		"uptime_sec":    int(time.Since(s.startedAt).Seconds()),
	}
	writeJSON(w, http.StatusOK, payload)
}

func (s *Server) handleHistory(w http.ResponseWriter, r *http.Request) {
	limit := envIntFromQuery(r.URL.Query().Get("limit"), 50)
	if limit <= 0 {
		limit = 50
	}
	if limit > 500 {
		limit = 500
	}

	items, err := s.store.History(limit)
	if err != nil {
		log.Printf("history error: %v", err)
		writeJSON(w, http.StatusInternalServerError, ErrorResponse{Error: "History unavailable"})
		return
	}

	writeJSON(w, http.StatusOK, map[string]any{
		"items": items,
	})
}

func envIntFromQuery(val string, def int) int {
	if val == "" {
		return def
	}
	parsed, err := strconv.Atoi(val)
	if err != nil {
		return def
	}
	return parsed
}

type HealthChecker struct {
	mu       sync.Mutex
	lastOK   bool
	lastTime time.Time
}

func (h *HealthChecker) CheckFactorDB(ctx context.Context, client *FactorDBClient, ttl time.Duration) bool {
	h.mu.Lock()
	if time.Since(h.lastTime) < ttl {
		result := h.lastOK
		h.mu.Unlock()
		return result
	}
	h.mu.Unlock()

	testCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	_, err := client.Query(testCtx, "17")
	ok := err == nil

	h.mu.Lock()
	h.lastOK = ok
	h.lastTime = time.Now()
	h.mu.Unlock()

	return ok
}

type Store struct {
	db *bolt.DB
}

var (
	bucketResults  = []byte("results")
	bucketMeta     = []byte("meta")
	bucketCountKey = []byte("count")
)

type storedResult struct {
	IsPrime   bool     `json:"is_prime"`
	Factors   []string `json:"factors,omitempty"`
	Source    string   `json:"source"`
	UpdatedAt int64    `json:"updated_at"`
	HitCount  int      `json:"hit_count"`
}

func NewStore(path string) (*Store, error) {
	dir := filepath.Dir(path)
	if dir != "." {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return nil, err
		}
	}

	db, err := bolt.Open(path, 0o600, &bolt.Options{Timeout: 5 * time.Second})
	if err != nil {
		return nil, err
	}

	store := &Store{db: db}
	if err := store.init(); err != nil {
		_ = db.Close()
		return nil, err
	}
	return store, nil
}

func (s *Store) init() error {
	return s.db.Update(func(tx *bolt.Tx) error {
		if _, err := tx.CreateBucketIfNotExists(bucketResults); err != nil {
			return err
		}
		if _, err := tx.CreateBucketIfNotExists(bucketMeta); err != nil {
			return err
		}
		return nil
	})
}

func (s *Store) Get(number string) (PrimeResult, bool, error) {
	var stored storedResult
	found := false

	err := s.db.View(func(tx *bolt.Tx) error {
		b := tx.Bucket(bucketResults)
		if b == nil {
			return nil
		}
		val := b.Get([]byte(number))
		if val == nil {
			return nil
		}
		found = true
		return json.Unmarshal(val, &stored)
	})
	if err != nil {
		return PrimeResult{}, false, err
	}
	if !found {
		return PrimeResult{}, false, nil
	}
	return PrimeResult{IsPrime: stored.IsPrime, Factors: stored.Factors, Source: stored.Source}, true, nil
}

func (s *Store) Put(number string, res PrimeResult) error {
	now := time.Now().Unix()
	return s.db.Update(func(tx *bolt.Tx) error {
		results := tx.Bucket(bucketResults)
		meta := tx.Bucket(bucketMeta)
		if results == nil || meta == nil {
			return fmt.Errorf("store buckets missing")
		}

		var stored storedResult
		existing := results.Get([]byte(number))
		if existing != nil {
			_ = json.Unmarshal(existing, &stored)
			stored.HitCount++
		} else {
			stored.HitCount = 1
			if err := incrementCount(meta); err != nil {
				return err
			}
		}

		stored.IsPrime = res.IsPrime
		stored.Factors = res.Factors
		stored.Source = res.Source
		stored.UpdatedAt = now

		buf, err := json.Marshal(stored)
		if err != nil {
			return err
		}
		return results.Put([]byte(number), buf)
	})
}

func (s *Store) Count() (int, error) {
	var count int
	err := s.db.View(func(tx *bolt.Tx) error {
		meta := tx.Bucket(bucketMeta)
		if meta == nil {
			return nil
		}
		val := meta.Get(bucketCountKey)
		if val == nil {
			count = 0
			return nil
		}
		if len(val) != 8 {
			return fmt.Errorf("invalid count value")
		}
		count = int(binary.BigEndian.Uint64(val))
		return nil
	})
	return count, err
}

func (s *Store) History(limit int) ([]HistoryItem, error) {
	var items []HistoryItem
	err := s.db.View(func(tx *bolt.Tx) error {
		results := tx.Bucket(bucketResults)
		if results == nil {
			return nil
		}
		return results.ForEach(func(k, v []byte) error {
			var stored storedResult
			if err := json.Unmarshal(v, &stored); err != nil {
				return err
			}
			items = append(items, HistoryItem{
				Number:    string(k),
				IsPrime:   stored.IsPrime,
				Factors:   stored.Factors,
				Source:    stored.Source,
				UpdatedAt: stored.UpdatedAt,
				HitCount:  stored.HitCount,
			})
			return nil
		})
	})
	if err != nil {
		return nil, err
	}

	sort.Slice(items, func(i, j int) bool {
		return items[i].UpdatedAt > items[j].UpdatedAt
	})
	if len(items) > limit {
		items = items[:limit]
	}
	return items, nil
}

func incrementCount(b *bolt.Bucket) error {
	var count uint64
	val := b.Get(bucketCountKey)
	if len(val) == 8 {
		count = binary.BigEndian.Uint64(val)
	}
	count++
	buf := make([]byte, 8)
	binary.BigEndian.PutUint64(buf, count)
	return b.Put(bucketCountKey, buf)
}

type LRUCache struct {
	cap   int
	mu    sync.Mutex
	items map[string]*list.Element
	order *list.List
}

type cacheEntry struct {
	key   string
	value PrimeResult
}

func NewLRUCache(size int) *LRUCache {
	return &LRUCache{
		cap:   size,
		items: make(map[string]*list.Element),
		order: list.New(),
	}
}

func (c *LRUCache) Get(key string) (PrimeResult, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.cap == 0 {
		return PrimeResult{}, false
	}

	if elem, ok := c.items[key]; ok {
		c.order.MoveToFront(elem)
		return elem.Value.(cacheEntry).value, true
	}
	return PrimeResult{}, false
}

func (c *LRUCache) Add(key string, value PrimeResult) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.cap == 0 {
		return
	}

	if elem, ok := c.items[key]; ok {
		elem.Value = cacheEntry{key: key, value: value}
		c.order.MoveToFront(elem)
		return
	}

	elem := c.order.PushFront(cacheEntry{key: key, value: value})
	c.items[key] = elem

	if c.order.Len() > c.cap {
		last := c.order.Back()
		if last != nil {
			c.order.Remove(last)
			delete(c.items, last.Value.(cacheEntry).key)
		}
	}
}

func (c *LRUCache) Len() int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.order.Len()
}

// execCommand isolates exec.CommandContext for testing/patching.
var execCommand = func(ctx context.Context, name string) *exec.Cmd {
	return exec.CommandContext(ctx, name)
}
