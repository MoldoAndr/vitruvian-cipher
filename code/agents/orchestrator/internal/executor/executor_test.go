package executor

import (
	"context"
	"sync"
	"testing"

	"orchestrator/internal/agents"
	"orchestrator/internal/model"
)

type stubAgent struct {
	name  string
	mu    sync.Mutex
	calls []string
}

func (s *stubAgent) Name() string {
	return s.name
}

func (s *stubAgent) Execute(ctx context.Context, operation string, params map[string]any) (any, error) {
	s.mu.Lock()
	s.calls = append(s.calls, operation)
	s.mu.Unlock()
	return map[string]any{"op": operation}, nil
}

func TestExecutorRunsDependencies(t *testing.T) {
	agent := &stubAgent{name: "test"}
	pool := agents.NewPool([]agents.Agent{agent})
	exec := New(pool, 2)

	plan := model.ExecutionPlan{
		Steps: []model.ExecutionStep{
			{Agent: "test", Operation: "step1", Params: map[string]any{}},
			{Agent: "test", Operation: "step2", Params: map[string]any{}, DependsOn: []int{0}},
			{Agent: "test", Operation: "step3", Params: map[string]any{}, DependsOn: []int{0, 1}},
		},
	}

	results, err := exec.Run(context.Background(), plan)
	if err != nil {
		t.Fatalf("executor failed: %v", err)
	}
	if len(results) != 3 {
		t.Fatalf("expected 3 results, got %d", len(results))
	}
	if results[0].Operation != "step1" || results[1].Operation != "step2" || results[2].Operation != "step3" {
		t.Fatalf("unexpected result operations: %#v", results)
	}
}
