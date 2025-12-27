package config

import "testing"

func TestExpandEnvIgnoresDollarTokens(t *testing.T) {
	t.Setenv("TEST_KEY", "secret")
	input := "password: \"$text\"\nkey: \"${TEST_KEY}\""
	out := expandEnv(input)
	if out != "password: \"$text\"\nkey: \"secret\"" {
		t.Fatalf("unexpected expansion: %q", out)
	}
}
