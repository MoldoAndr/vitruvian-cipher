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

type OpenAIClient struct {
	baseURL string
	apiKey  string
	http    *http.Client
}

func NewOpenAI(baseURL, apiKey string, timeout time.Duration) *OpenAIClient {
	if baseURL == "" {
		baseURL = "https://api.openai.com/v1"
	}
	transport := &http.Transport{
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 20,
		IdleConnTimeout:     90 * time.Second,
	}
	return &OpenAIClient{
		baseURL: strings.TrimRight(baseURL, "/"),
		apiKey:  apiKey,
		http: &http.Client{
			Transport: transport,
			Timeout:   timeout,
		},
	}
}

func (c *OpenAIClient) Name() string {
	return "openai"
}

func (c *OpenAIClient) Generate(ctx context.Context, req Request) (Response, error) {
	apiKey := req.APIKey
	if apiKey == "" {
		apiKey = c.apiKey
	}
	if apiKey == "" {
		return Response{}, fmt.Errorf("openai api key missing")
	}
	messages := make([]model.Message, 0, len(req.Messages)+1)
	if req.System != "" {
		messages = append(messages, model.Message{Role: "system", Content: req.System})
	}
	messages = append(messages, req.Messages...)

	payload := map[string]any{
		"model":       req.Model,
		"messages":    messages,
		"temperature": req.Temperature,
	}
	if req.MaxTokens > 0 {
		payload["max_tokens"] = req.MaxTokens
	}
	if strings.EqualFold(req.ResponseFormat, "json") {
		payload["response_format"] = map[string]any{"type": "json_object"}
	}

	raw, err := json.Marshal(payload)
	if err != nil {
		return Response{}, fmt.Errorf("openai marshal: %w", err)
	}

	request, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+"/chat/completions", bytes.NewReader(raw))
	if err != nil {
		return Response{}, fmt.Errorf("openai request: %w", err)
	}
	request.Header.Set("Content-Type", "application/json")
	request.Header.Set("Authorization", "Bearer "+apiKey)

	resp, err := c.http.Do(request)
	if err != nil {
		return Response{}, fmt.Errorf("openai call: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return Response{}, fmt.Errorf("openai status: %s", resp.Status)
	}

	var decoded struct {
		Choices []struct {
			Message model.Message `json:"message"`
		} `json:"choices"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&decoded); err != nil {
		return Response{}, fmt.Errorf("openai decode: %w", err)
	}
	if len(decoded.Choices) == 0 {
		return Response{}, fmt.Errorf("openai empty response")
	}
	return Response{Content: decoded.Choices[0].Message.Content, Raw: decoded}, nil
}
