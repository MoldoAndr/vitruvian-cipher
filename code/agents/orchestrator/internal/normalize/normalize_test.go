package normalize

import "testing"

func TestTextNormalization(t *testing.T) {
	input := "  Hello\r\nworld\t  test\r  "
	expected := "Hello world test"
	if got := Text(input); got != expected {
		t.Fatalf("expected %q, got %q", expected, got)
	}
}
