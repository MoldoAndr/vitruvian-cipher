package llm

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
)

func TestGeminiUsesRequestAPIKey(t *testing.T) {
	key := os.Getenv("TEST_GEMINI_KEY")
	if key == "" {
		key = "test-gemini-key"
	}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/models/gemini-test:generateContent" {
			t.Fatalf("unexpected path: %s", r.URL.Path)
		}
		if r.URL.Query().Get("key") != key {
			t.Fatalf("missing or invalid key query param")
		}
		_ = json.NewEncoder(w).Encode(map[string]any{
			"candidates": []map[string]any{
				{"content": map[string]any{"parts": []map[string]string{{"text": "ok"}}}},
			},
		})
	}))
	defer server.Close()

	client := NewGemini(server.URL, "fallback", 0)
	resp, err := client.Generate(context.Background(), Request{
		Model:  "gemini-test",
		APIKey: key,
	})
	if err != nil {
		t.Fatalf("generate failed: %v", err)
	}
	if resp.Content != "ok" {
		t.Fatalf("unexpected response: %s", resp.Content)
	}
}
