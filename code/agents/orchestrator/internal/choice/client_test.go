package choice

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestClientIntentAndEntities(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var payload map[string]any
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			t.Fatalf("invalid payload: %v", err)
		}
		op := payload["operation"]
		text := payload["input_text"]
		if text != "hello" {
			t.Fatalf("unexpected input_text: %v", text)
		}
		switch op {
		case "intent_extraction":
			_ = json.NewEncoder(w).Encode(map[string]any{
				"status":    "ok",
				"operation": "intent_extraction",
				"result": map[string]any{
					"label": "greet",
					"score": 0.9,
					"all_predictions": []map[string]any{
						{"label": "greet", "score": 0.9},
					},
				},
			})
		case "entity_extraction":
			_ = json.NewEncoder(w).Encode(map[string]any{
				"status":    "ok",
				"operation": "entity_extraction",
				"result": map[string]any{
					"entities": []map[string]any{
						{"entity": "GREETING", "score": 0.8, "text": "hello", "start": 0, "end": 5},
					},
					"count": 1,
				},
			})
		default:
			w.WriteHeader(http.StatusBadRequest)
			return
		}
	}))
	defer server.Close()

	client := New(server.URL, 0)
	intent, err := client.Intent(context.Background(), "hello")
	if err != nil {
		t.Fatalf("intent failed: %v", err)
	}
	if intent.Label != "greet" || intent.Confidence != 0.9 {
		t.Fatalf("unexpected intent: %#v", intent)
	}

	entities, err := client.Entities(context.Background(), "hello")
	if err != nil {
		t.Fatalf("entities failed: %v", err)
	}
	if len(entities) != 1 || entities[0].Type != "GREETING" {
		t.Fatalf("unexpected entities: %#v", entities)
	}
}
