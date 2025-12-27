package llm

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
)

func TestOllamaUsesRequestAPIKey(t *testing.T) {
	key := os.Getenv("TEST_OLLAMA_KEY")
	if key == "" {
		key = "test-ollama-key"
	}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/chat" {
			t.Fatalf("unexpected path: %s", r.URL.Path)
		}
		auth := r.Header.Get("Authorization")
		if auth != "Bearer "+key {
			t.Fatalf("missing or invalid auth header")
		}
		var payload map[string]any
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			t.Fatalf("invalid request body: %v", err)
		}
		if payload["model"] != "llama-test" {
			t.Fatalf("unexpected model: %v", payload["model"])
		}
		_ = json.NewEncoder(w).Encode(map[string]any{
			"message": map[string]any{"role": "assistant", "content": "ok"},
		})
	}))
	defer server.Close()

	client := NewOllama("ollama_local", server.URL, "fallback", 0)
	resp, err := client.Generate(context.Background(), Request{
		Model:  "llama-test",
		APIKey: key,
	})
	if err != nil {
		t.Fatalf("generate failed: %v", err)
	}
	if resp.Content != "ok" {
		t.Fatalf("unexpected response: %s", resp.Content)
	}
}
