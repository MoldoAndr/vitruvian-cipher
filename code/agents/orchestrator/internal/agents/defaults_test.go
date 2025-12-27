package agents

import "testing"

func TestNormalizeOperation(t *testing.T) {
	if NormalizeOperation("password_checker", "evaluate_strength") != "score" {
		t.Fatalf("expected evaluate_strength to map to score")
	}
	if NormalizeOperation("prime_checker", "primality_test") != "isprime" {
		t.Fatalf("expected primality_test to map to isprime")
	}
	if NormalizeOperation("unknown", "score") != "score" {
		t.Fatalf("expected passthrough for unknown agent")
	}
}

func TestSupportsOperation(t *testing.T) {
	if !SupportsOperation("password_checker", "score") {
		t.Fatalf("expected score to be supported")
	}
	if SupportsOperation("password_checker", "evaluate_strength") {
		t.Fatalf("expected evaluate_strength to be unsupported before normalization")
	}
}
