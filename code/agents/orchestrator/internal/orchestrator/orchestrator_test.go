package orchestrator

import (
	"testing"

	"orchestrator/internal/model"
)

func TestResolveAPIKeyPriority(t *testing.T) {
	selection := model.LLMSelection{
		Provider: "openai",
		APIKey:   "primary",
		APIKeys: map[string]string{
			"openai":    "map-primary",
			"anthropic": "map-anth",
		},
	}

	if key := resolveAPIKey(selection, "openai", "fallback"); key != "map-primary" {
		t.Fatalf("expected map key, got %q", key)
	}
	if key := resolveAPIKey(selection, "anthropic", "fallback"); key != "map-anth" {
		t.Fatalf("expected map key for anthropic, got %q", key)
	}
	if key := resolveAPIKey(selection, "gemini", "fallback"); key != "fallback" {
		t.Fatalf("expected fallback key, got %q", key)
	}

	selection.APIKeys = nil
	if key := resolveAPIKey(selection, "openai", "fallback"); key != "primary" {
		t.Fatalf("expected primary key, got %q", key)
	}
}

func TestResolveModelOverridePriority(t *testing.T) {
	selection := model.LLMSelection{
		Provider:      "ollama_cloud",
		Model:         "primary-model",
		PlannerModel:  "primary-planner",
		Models:        map[string]string{"ollama_cloud": "map-model", "openai": "map-openai"},
		PlannerModels: map[string]string{"ollama_cloud": "map-planner", "openai": "map-plan-openai"},
	}

	if value := resolveModelOverride(selection, "ollama_cloud", "responder"); value != "map-model" {
		t.Fatalf("expected map model override, got %q", value)
	}
	if value := resolveModelOverride(selection, "ollama_cloud", "planner"); value != "map-planner" {
		t.Fatalf("expected map planner override, got %q", value)
	}
	if value := resolveModelOverride(selection, "openai", "responder"); value != "map-openai" {
		t.Fatalf("expected map override for openai responder, got %q", value)
	}
	if value := resolveModelOverride(selection, "openai", "planner"); value != "map-plan-openai" {
		t.Fatalf("expected map override for openai planner, got %q", value)
	}

	selection.Models = nil
	selection.PlannerModels = nil
	if value := resolveModelOverride(selection, "ollama_cloud", "responder"); value != "primary-model" {
		t.Fatalf("expected primary model override, got %q", value)
	}
	if value := resolveModelOverride(selection, "ollama_cloud", "planner"); value != "primary-planner" {
		t.Fatalf("expected primary planner override, got %q", value)
	}

	if value := resolveModelOverride(selection, "openai", "responder"); value != "" {
		t.Fatalf("expected no override for openai responder, got %q", value)
	}
}
