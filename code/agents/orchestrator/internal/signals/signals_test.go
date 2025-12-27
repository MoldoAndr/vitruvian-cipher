package signals

import "testing"

func TestAnalyzeSignals(t *testing.T) {
	text := "Use AES-256 on 0xdeadbeef with base64 U0FMVVQxMjM0NTY= and ip 192.168.1.1 size 2048"
	out := Analyze(text)

	if len(out.Algorithms) == 0 || out.Algorithms[0] != "aes" {
		t.Fatalf("expected aes algorithm, got %v", out.Algorithms)
	}
	if len(out.HexStrings) == 0 {
		t.Fatalf("expected hex string")
	}
	if len(out.Base64) == 0 {
		t.Fatalf("expected base64 match")
	}
	if len(out.IPs) == 0 || out.IPs[0] != "192.168.1.1" {
		t.Fatalf("expected ip address, got %v", out.IPs)
	}
	found := false
	for _, val := range out.Numbers {
		if val == "2048" {
			found = true
			break
		}
	}
	if !found {
		t.Fatalf("expected number match, got %v", out.Numbers)
	}

	mapped := out.Map()
	if mapped["algorithm"] != "aes" {
		t.Fatalf("expected algorithm map to aes, got %v", mapped["algorithm"])
	}
}
