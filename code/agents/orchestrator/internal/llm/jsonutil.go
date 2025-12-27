package llm

import (
	"encoding/json"
	"errors"
	"strings"
)

func ExtractJSON[T any](raw string, target *T) error {
	trimmed := strings.TrimSpace(raw)
	if trimmed == "" {
		return errors.New("empty response")
	}
	if json.Unmarshal([]byte(trimmed), target) == nil {
		return nil
	}
	start := strings.Index(trimmed, "{")
	if start == -1 {
		return errors.New("no json object found")
	}
	depth := 0
	for i := start; i < len(trimmed); i++ {
		switch trimmed[i] {
		case '{':
			depth++
		case '}':
			depth--
			if depth == 0 {
				segment := trimmed[start : i+1]
				if err := json.Unmarshal([]byte(segment), target); err != nil {
					return err
				}
				return nil
			}
		}
	}
	return errors.New("unterminated json object")
}
