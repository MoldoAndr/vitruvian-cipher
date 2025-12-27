package router

import (
	"testing"

	"orchestrator/internal/model"
	"orchestrator/internal/signals"
)

func TestBuildParamsUsesFallbackText(t *testing.T) {
	route := Route{
		Intents:   []string{"password_check"},
		Agent:     "password_checker",
		Operation: "score",
		Slots: map[string][]string{
			"password": {"password", "$text"},
		},
		OptionalSlots: map[string]struct{}{},
	}

	engine := New([]Route{route}, 0.8, 0.6)
	entities := []model.Entity{{Type: "password", Value: "ignored", Confidence: 0.3}}

	params, missing := engine.BuildParams(route, entities, signals.Signals{}, "rawpass", "rawpass", "c1", "", nil)
	if len(missing) != 0 {
		t.Fatalf("expected no missing slots, got %v", missing)
	}
	if params["password"] != "rawpass" {
		t.Fatalf("expected fallback to raw text, got %v", params["password"])
	}
}

func TestBuildParamsMissingSlot(t *testing.T) {
	route := Route{
		Intents:   []string{"primality_test"},
		Agent:     "prime_checker",
		Operation: "isprime",
		Slots: map[string][]string{
			"number": {"number"},
		},
		OptionalSlots: map[string]struct{}{},
	}

	engine := New([]Route{route}, 0.8, 0.6)
	params, missing := engine.BuildParams(route, nil, signals.Signals{}, "text", "text", "c1", "", nil)
	if len(params) != 0 {
		t.Fatalf("expected no params, got %v", params)
	}
	if len(missing) != 1 || missing[0] != "number" {
		t.Fatalf("expected missing number slot, got %v", missing)
	}
}
