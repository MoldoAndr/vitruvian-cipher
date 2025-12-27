package agents

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"
)

type Operation struct {
	Method string
	Path   string
}

type HTTPAgent struct {
	name       string
	baseURL    string
	operations map[string]Operation
	http       *http.Client
}

func NewHTTPAgent(name, baseURL string, ops map[string]Operation, timeout time.Duration) *HTTPAgent {
	transport := &http.Transport{
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 20,
		IdleConnTimeout:     90 * time.Second,
	}
	return &HTTPAgent{
		name:       name,
		baseURL:    strings.TrimRight(baseURL, "/"),
		operations: ops,
		http: &http.Client{
			Transport: transport,
			Timeout:   timeout,
		},
	}
}

func (a *HTTPAgent) Name() string {
	return a.name
}

func (a *HTTPAgent) Execute(ctx context.Context, operation string, params map[string]any) (any, error) {
	op, ok := a.operations[operation]
	if !ok {
		return nil, fmt.Errorf("operation %q not supported by %s", operation, a.name)
	}
	if op.Method == "" {
		op.Method = http.MethodPost
	}
	payload, err := json.Marshal(params)
	if err != nil {
		return nil, fmt.Errorf("marshal payload: %w", err)
	}
	req, err := http.NewRequestWithContext(ctx, op.Method, a.baseURL+op.Path, bytes.NewReader(payload))
	if err != nil {
		return nil, fmt.Errorf("build request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := a.http.Do(req)
	if err != nil {
		return nil, fmt.Errorf("agent request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, fmt.Errorf("agent %s status: %s", a.name, resp.Status)
	}

	var out any
	dec := json.NewDecoder(resp.Body)
	dec.UseNumber()
	if err := dec.Decode(&out); err != nil {
		return nil, fmt.Errorf("decode agent response: %w", err)
	}
	return out, nil
}
