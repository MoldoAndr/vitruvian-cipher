package llm

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"orchestrator/internal/model"
)

type OllamaClient struct {
	name    string
	baseURL string
	apiKey  string
	http    *http.Client
}

func NewOllama(name, baseURL, apiKey string, timeout time.Duration) *OllamaClient {
	transport := &http.Transport{
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 20,
		IdleConnTimeout:     90 * time.Second,
	}
	return &OllamaClient{
		name:    name,
		baseURL: strings.TrimRight(baseURL, "/"),
		apiKey:  apiKey,
		http: &http.Client{
			Transport: transport,
			Timeout:   timeout,
		},
	}
}

func (c *OllamaClient) Name() string {
	return c.name
}

func (c *OllamaClient) Generate(ctx context.Context, req Request) (Response, error) {
	apiKey := req.APIKey
	if apiKey == "" {
		apiKey = c.apiKey
	}
	payload := map[string]any{
		"model":    req.Model,
		"messages": req.Messages,
		"stream":   false,
		"options": map[string]any{
			"temperature": req.Temperature,
		},
	}
	if req.System != "" {
		payload["messages"] = append([]model.Message{{Role: "system", Content: req.System}}, req.Messages...)
	}

	raw, err := json.Marshal(payload)
	if err != nil {
		return Response{}, fmt.Errorf("ollama marshal: %w", err)
	}
	request, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+"/api/chat", bytes.NewReader(raw))
	if err != nil {
		return Response{}, fmt.Errorf("ollama request: %w", err)
	}
	request.Header.Set("Content-Type", "application/json")
	if apiKey != "" {
		request.Header.Set("Authorization", "Bearer "+apiKey)
	}

	resp, err := c.http.Do(request)
	if err != nil {
		return Response{}, fmt.Errorf("ollama call: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return Response{}, fmt.Errorf("ollama status: %s", resp.Status)
	}

	var decoded struct {
		Message model.Message `json:"message"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&decoded); err != nil {
		return Response{}, fmt.Errorf("ollama decode: %w", err)
	}
	return Response{Content: decoded.Message.Content, Raw: decoded}, nil
}
