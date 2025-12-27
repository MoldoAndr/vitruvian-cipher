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

type AnthropicClient struct {
	baseURL string
	apiKey  string
	http    *http.Client
}

func NewAnthropic(baseURL, apiKey string, timeout time.Duration) *AnthropicClient {
	if baseURL == "" {
		baseURL = "https://api.anthropic.com/v1"
	}
	transport := &http.Transport{
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 20,
		IdleConnTimeout:     90 * time.Second,
	}
	return &AnthropicClient{
		baseURL: strings.TrimRight(baseURL, "/"),
		apiKey:  apiKey,
		http: &http.Client{
			Transport: transport,
			Timeout:   timeout,
		},
	}
}

func (c *AnthropicClient) Name() string {
	return "anthropic"
}

func (c *AnthropicClient) Generate(ctx context.Context, req Request) (Response, error) {
	apiKey := req.APIKey
	if apiKey == "" {
		apiKey = c.apiKey
	}
	if apiKey == "" {
		return Response{}, fmt.Errorf("anthropic api key missing")
	}
	messages := make([]model.Message, 0, len(req.Messages))
	for _, msg := range req.Messages {
		if msg.Role == "system" {
			continue
		}
		messages = append(messages, msg)
	}

	payload := map[string]any{
		"model":       req.Model,
		"max_tokens":  maxTokens(req.MaxTokens, 1024),
		"temperature": req.Temperature,
		"messages":    messages,
	}
	if req.System != "" {
		payload["system"] = req.System
	}

	raw, err := json.Marshal(payload)
	if err != nil {
		return Response{}, fmt.Errorf("anthropic marshal: %w", err)
	}

	request, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+"/messages", bytes.NewReader(raw))
	if err != nil {
		return Response{}, fmt.Errorf("anthropic request: %w", err)
	}
	request.Header.Set("Content-Type", "application/json")
	request.Header.Set("x-api-key", apiKey)
	request.Header.Set("anthropic-version", "2023-06-01")

	resp, err := c.http.Do(request)
	if err != nil {
		return Response{}, fmt.Errorf("anthropic call: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return Response{}, fmt.Errorf("anthropic status: %s", resp.Status)
	}

	var decoded struct {
		Content []struct {
			Type string `json:"type"`
			Text string `json:"text"`
		} `json:"content"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&decoded); err != nil {
		return Response{}, fmt.Errorf("anthropic decode: %w", err)
	}
	if len(decoded.Content) == 0 {
		return Response{}, fmt.Errorf("anthropic empty response")
	}
	return Response{Content: decoded.Content[0].Text, Raw: decoded}, nil
}

func maxTokens(value, fallback int) int {
	if value > 0 {
		return value
	}
	return fallback
}
