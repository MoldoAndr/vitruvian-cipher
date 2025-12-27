package agents

import "strings"

var DefaultOperations = map[string]map[string]Operation{
	"password_checker": {
		"score": {Method: "POST", Path: "/score"},
	},
	"crypto_god": {
		"detect": {Method: "POST", Path: "/detect"},
	},
	"prime_checker": {
		"isprime": {Method: "POST", Path: "/isprime"},
	},
	"theory_specialist": {
		"generate": {Method: "POST", Path: "/generate"},
	},
}

var OperationAliases = map[string]map[string]string{
	"password_checker": {
		"evaluate_strength": "score",
		"password_strength": "score",
		"check_password":    "score",
		"strength":          "score",
		"score_password":    "score",
	},
	"crypto_god": {
		"detect_cipher":   "detect",
		"cipher_detect":   "detect",
		"identify_cipher": "detect",
	},
	"prime_checker": {
		"primality_test": "isprime",
		"factor":         "isprime",
		"factorization":  "isprime",
	},
	"theory_specialist": {
		"ask":    "generate",
		"query":  "generate",
		"answer": "generate",
	},
}

func NormalizeOperation(agentName, operation string) string {
	agentName = strings.ToLower(strings.TrimSpace(agentName))
	operation = strings.ToLower(strings.TrimSpace(operation))
	if operation == "" {
		return operation
	}
	if aliases, ok := OperationAliases[agentName]; ok {
		if mapped, ok := aliases[operation]; ok {
			return mapped
		}
	}
	return operation
}

func SupportsOperation(agentName, operation string) bool {
	agentName = strings.ToLower(strings.TrimSpace(agentName))
	operation = strings.ToLower(strings.TrimSpace(operation))
	ops, ok := DefaultOperations[agentName]
	if !ok {
		return false
	}
	_, ok = ops[operation]
	return ok
}
