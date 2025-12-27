package agents

import "context"

type Agent interface {
	Name() string
	Execute(ctx context.Context, operation string, params map[string]any) (any, error)
}

type AgentResult struct {
	Agent     string
	Operation string
	Output    any
}
