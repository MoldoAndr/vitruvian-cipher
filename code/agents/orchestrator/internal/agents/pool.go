package agents

import (
	"context"
	"fmt"
)

type Pool struct {
	agents map[string]Agent
}

func NewPool(agents []Agent) *Pool {
	pool := &Pool{agents: map[string]Agent{}}
	for _, agent := range agents {
		pool.agents[agent.Name()] = agent
	}
	return pool
}

func (p *Pool) Execute(ctx context.Context, agentName, operation string, params map[string]any) (any, error) {
	agent, ok := p.agents[agentName]
	if !ok {
		return nil, fmt.Errorf("agent %q not found", agentName)
	}
	return agent.Execute(ctx, operation, params)
}

func (p *Pool) Names() []string {
	names := make([]string, 0, len(p.agents))
	for name := range p.agents {
		names = append(names, name)
	}
	return names
}
