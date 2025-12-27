package llm

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"strings"
	"time"
)

type GeminiClient struct {
	baseURL string
	apiKey  string
	http    *http.Client
}

func NewGemini(baseURL, apiKey string, timeout time.Duration) *GeminiClient {
	if baseURL == "" {
		baseURL = "https://generativelanguage.googleapis.com/v1beta"
	}
	transport := &http.Transport{
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 20,
		IdleConnTimeout:     90 * time.Second,
	}
	return &GeminiClient{
		baseURL: strings.TrimRight(baseURL, "/"),
		apiKey:  apiKey,
		http: &http.Client{
			Transport: transport,
			Timeout:   timeout,
		},
	}
}

func (c *GeminiClient) Name() string {
	return "gemini"
}

func (c *GeminiClient) Generate(ctx context.Context, req Request) (Response, error) {
	apiKey := req.APIKey
	if apiKey == "" {
		apiKey = c.apiKey
	}
	if apiKey == "" {
		return Response{}, fmt.Errorf("gemini api key missing")
	}
	var contents []map[string]any
	for _, msg := range req.Messages {
		role := "user"
		if msg.Role == "assistant" {
			role = "model"
		}
		contents = append(contents, map[string]any{
			"role":  role,
			"parts": []map[string]string{{"text": msg.Content}},
		})
	}

	payload := map[string]any{
		"contents": contents,
		"generationConfig": map[string]any{
			"temperature": req.Temperature,
		},
	}
	if req.MaxTokens > 0 {
		payload["generationConfig"].(map[string]any)["maxOutputTokens"] = req.MaxTokens
	}
	if req.System != "" {
		payload["systemInstruction"] = map[string]any{
			"parts": []map[string]string{{"text": req.System}},
		}
	}

	raw, err := json.Marshal(payload)
	if err != nil {
		return Response{}, fmt.Errorf("gemini marshal: %w", err)
	}

	endpoint := fmt.Sprintf("%s/models/%s:generateContent", c.baseURL, url.PathEscape(req.Model))
	endpoint = endpoint + "?key=" + url.QueryEscape(apiKey)

	request, err := http.NewRequestWithContext(ctx, http.MethodPost, endpoint, bytes.NewReader(raw))
	if err != nil {
		return Response{}, fmt.Errorf("gemini request: %w", err)
	}
	request.Header.Set("Content-Type", "application/json")

	resp, err := c.http.Do(request)
	if err != nil {
		return Response{}, fmt.Errorf("gemini call: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return Response{}, fmt.Errorf("gemini status: %s", resp.Status)
	}

	var decoded struct {
		Candidates []struct {
			Content struct {
				Parts []struct {
					Text string `json:"text"`
				} `json:"parts"`
			} `json:"content"`
		} `json:"candidates"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&decoded); err != nil {
		return Response{}, fmt.Errorf("gemini decode: %w", err)
	}
	if len(decoded.Candidates) == 0 || len(decoded.Candidates[0].Content.Parts) == 0 {
		return Response{}, fmt.Errorf("gemini empty response")
	}
	return Response{Content: decoded.Candidates[0].Content.Parts[0].Text, Raw: decoded}, nil
}
