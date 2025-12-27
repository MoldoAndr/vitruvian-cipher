package orchestrator

import (
	"testing"

	"orchestrator/internal/model"
)

func TestExtractTheoryOutput(t *testing.T) {
	outputs := []model.AgentResult{{
		Agent:     "theory_specialist",
		Operation: "generate",
		Output: map[string]any{
			"answer":          "hello",
			"conversation_id": "conv-1",
			"sources": []any{
				map[string]any{
					"chunk_id":        "chunk-1",
					"relevance_score": 0.9,
					"preview":         "preview text",
					"metadata":        map[string]any{"source": "doc"},
				},
			},
		},
	}}

	answer, sources, conv := extractTheoryOutput(outputs)
	if answer != "hello" {
		t.Fatalf("unexpected answer: %s", answer)
	}
	if conv != "conv-1" {
		t.Fatalf("unexpected conversation id: %s", conv)
	}
	if len(sources) != 1 {
		t.Fatalf("expected 1 source, got %d", len(sources))
	}
	if sources[0].ChunkID != "chunk-1" {
		t.Fatalf("unexpected chunk id: %s", sources[0].ChunkID)
	}
}
