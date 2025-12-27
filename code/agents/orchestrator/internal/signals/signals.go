package signals

import (
	"regexp"
	"sort"
	"strings"
)

type Signals struct {
	Algorithms []string
	Numbers    []string
	HexStrings []string
	Base64     []string
	IPs        []string
}

var (
	hexRe    = regexp.MustCompile(`\b(?:0x)?[0-9a-fA-F]{8,}\b`)
	base64Re = regexp.MustCompile(`\b[A-Za-z0-9+/]{12,}={0,2}\b`)
	numberRe = regexp.MustCompile(`\b\d{2,}\b`)
	ipRe     = regexp.MustCompile(`\b(?:\d{1,3}\.){3}\d{1,3}\b`)
)

var algoList = []string{
	"aes", "rsa", "des", "3des", "blowfish", "twofish", "chacha20",
	"sha1", "sha256", "sha512", "md5", "bcrypt", "scrypt", "argon2",
	"pbkdf2", "base64", "hex", "hmac", "ecdsa", "ed25519",
}

func Analyze(text string) Signals {
	lowered := strings.ToLower(text)
	algorithms := map[string]struct{}{}
	for _, algo := range algoList {
		if strings.Contains(lowered, algo) {
			algorithms[algo] = struct{}{}
		}
	}

	var algos []string
	for algo := range algorithms {
		algos = append(algos, algo)
	}
	sort.Strings(algos)

	return Signals{
		Algorithms: algos,
		Numbers:    dedupe(numberRe.FindAllString(text, -1)),
		HexStrings: dedupe(hexRe.FindAllString(text, -1)),
		Base64:     dedupe(base64Re.FindAllString(text, -1)),
		IPs:        dedupe(ipRe.FindAllString(text, -1)),
	}
}

func (s Signals) Map() map[string]string {
	out := map[string]string{}
	if len(s.Algorithms) > 0 {
		out["algorithm"] = s.Algorithms[0]
	}
	if len(s.Numbers) > 0 {
		out["number"] = s.Numbers[0]
	}
	if len(s.HexStrings) > 0 {
		out["hex"] = s.HexStrings[0]
	}
	if len(s.Base64) > 0 {
		out["base64"] = s.Base64[0]
	}
	if len(s.IPs) > 0 {
		out["ip"] = s.IPs[0]
	}
	return out
}

func dedupe(items []string) []string {
	seen := map[string]struct{}{}
	out := make([]string, 0, len(items))
	for _, item := range items {
		if _, ok := seen[item]; ok {
			continue
		}
		seen[item] = struct{}{}
		out = append(out, item)
	}
	return out
}
