package llm

import "testing"

type sample struct {
	Value string `json:"value"`
}

func TestExtractJSON(t *testing.T) {
	input := "prefix {\"value\":\"ok\"} suffix"
	var out sample
	if err := ExtractJSON(input, &out); err != nil {
		t.Fatalf("extract failed: %v", err)
	}
	if out.Value != "ok" {
		t.Fatalf("unexpected value: %s", out.Value)
	}
}

func TestExtractJSONNoObject(t *testing.T) {
	var out sample
	if err := ExtractJSON("no json here", &out); err == nil {
		t.Fatalf("expected error for missing JSON")
	}
}
