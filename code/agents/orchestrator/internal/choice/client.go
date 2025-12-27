package choice

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

type Client struct {
	baseURL string
	http    *http.Client
}

func New(baseURL string, timeout time.Duration) *Client {
	return &Client{
		baseURL: strings.TrimRight(baseURL, "/"),
		http: &http.Client{
			Timeout: timeout,
		},
	}
}

func (c *Client) Intent(ctx context.Context, text string) (model.IntentResult, error) {
	payload := map[string]any{
		"operation":  "intent_extraction",
		"input_text": text,
	}
	var resp struct {
		Status    string `json:"status"`
		Operation string `json:"operation"`
		Result    struct {
			Label string  `json:"label"`
			Score float64 `json:"score"`
			All   []struct {
				Label string  `json:"label"`
				Score float64 `json:"score"`
			} `json:"all_predictions"`
		} `json:"result"`
		Message string `json:"message"`
	}

	if err := c.post(ctx, "/predict", payload, &resp); err != nil {
		return model.IntentResult{}, err
	}
	if resp.Status != "ok" {
		return model.IntentResult{}, fmt.Errorf("choice maker intent error: %s", resp.Message)
	}
	candidates := make([]model.IntentCandidate, 0, len(resp.Result.All))
	for _, item := range resp.Result.All {
		candidates = append(candidates, model.IntentCandidate{Label: item.Label, Score: item.Score})
	}
	return model.IntentResult{Label: resp.Result.Label, Confidence: resp.Result.Score, Candidates: candidates}, nil
}

func (c *Client) Entities(ctx context.Context, text string) ([]model.Entity, error) {
	payload := map[string]any{
		"operation":  "entity_extraction",
		"input_text": text,
	}
	var resp struct {
		Status    string `json:"status"`
		Operation string `json:"operation"`
		Result    struct {
			Entities []struct {
				Entity string  `json:"entity"`
				Score  float64 `json:"score"`
				Text   string  `json:"text"`
				Start  int     `json:"start"`
				End    int     `json:"end"`
			} `json:"entities"`
			Count int `json:"count"`
		} `json:"result"`
		Message string `json:"message"`
	}

	if err := c.post(ctx, "/predict", payload, &resp); err != nil {
		return nil, err
	}
	if resp.Status != "ok" {
		return nil, fmt.Errorf("choice maker entity error: %s", resp.Message)
	}
	out := make([]model.Entity, 0, len(resp.Result.Entities))
	for _, ent := range resp.Result.Entities {
		out = append(out, model.Entity{
			Type:       ent.Entity,
			Value:      ent.Text,
			Confidence: ent.Score,
			Start:      ent.Start,
			End:        ent.End,
		})
	}
	return out, nil
}

func (c *Client) post(ctx context.Context, path string, payload any, out any) error {
	body, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("marshal payload: %w", err)
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+path, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("build request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	res, err := c.http.Do(req)
	if err != nil {
		return fmt.Errorf("choice maker request: %w", err)
	}
	defer res.Body.Close()
	if res.StatusCode < 200 || res.StatusCode >= 300 {
		return fmt.Errorf("choice maker status: %s", res.Status)
	}
	dec := json.NewDecoder(res.Body)
	if err := dec.Decode(out); err != nil {
		return fmt.Errorf("decode response: %w", err)
	}
	return nil
}
