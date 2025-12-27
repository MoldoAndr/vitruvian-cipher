package router

import (
	"testing"

	"orchestrator/internal/signals"
)

func TestResolveSlotFromState(t *testing.T) {
	route := Route{
		Slots: map[string][]string{
			"conversation_id": {"$state:theory_conversation_id"},
		},
		OptionalSlots: map[string]struct{}{},
	}

	params, missing := New(nil, 0.9, 0.6).BuildParams(
		route,
		nil,
		signals.Signals{},
		"",
		"",
		"c1",
		"",
		map[string]string{"theory_conversation_id": "rag-1"},
	)
	if len(missing) != 0 {
		t.Fatalf("unexpected missing slots: %v", missing)
	}
	if params["conversation_id"] != "rag-1" {
		t.Fatalf("expected state conversation id, got %v", params["conversation_id"])
	}
}
