package executor

import (
	"context"
	"fmt"
	"sync"
	"time"

	"golang.org/x/sync/errgroup"

	"orchestrator/internal/agents"
	"orchestrator/internal/model"
)

type Executor struct {
	pool        *agents.Pool
	maxParallel int
}

func New(pool *agents.Pool, maxParallel int) *Executor {
	if maxParallel <= 0 {
		maxParallel = 1
	}
	return &Executor{pool: pool, maxParallel: maxParallel}
}

func (e *Executor) Run(ctx context.Context, plan model.ExecutionPlan) ([]model.AgentResult, error) {
	steps := plan.Steps
	if len(steps) == 0 {
		return nil, nil
	}

	results := make([]model.AgentResult, len(steps))
	status := make([]int, len(steps))
	// 0 pending, 1 running, 2 done

	sem := make(chan struct{}, e.maxParallel)
	var mu sync.Mutex

	for completed := 0; completed < len(steps); {
		ready := nextReadySteps(steps, status)
		if len(ready) == 0 {
			break
		}
		group, groupCtx := errgroup.WithContext(ctx)
		for _, idx := range ready {
			status[idx] = 1
			step := steps[idx]
			sem <- struct{}{}
			idx := idx
			group.Go(func() error {
				defer func() { <-sem }()
				started := time.Now()
				output, err := e.pool.Execute(groupCtx, step.Agent, step.Operation, step.Params)
				if err != nil {
					return fmt.Errorf("step %d (%s/%s) failed: %w", idx, step.Agent, step.Operation, err)
				}
				mu.Lock()
				results[idx] = model.AgentResult{
					Agent:     step.Agent,
					Operation: step.Operation,
					Output:    output,
					Duration:  time.Since(started),
				}
				status[idx] = 2
				mu.Unlock()
				return nil
			})
		}
		if err := group.Wait(); err != nil {
			return nil, err
		}
		completed = countDone(status)
	}

	for i, state := range status {
		if state != 2 {
			return nil, fmt.Errorf("execution incomplete at step %d", i)
		}
	}
	return results, nil
}

func nextReadySteps(steps []model.ExecutionStep, status []int) []int {
	var ready []int
	for idx, step := range steps {
		if status[idx] != 0 {
			continue
		}
		if depsSatisfied(step.DependsOn, status) {
			ready = append(ready, idx)
		}
	}
	return ready
}

func depsSatisfied(deps []int, status []int) bool {
	for _, dep := range deps {
		if dep < 0 || dep >= len(status) {
			return false
		}
		if status[dep] != 2 {
			return false
		}
	}
	return true
}

func countDone(status []int) int {
	done := 0
	for _, state := range status {
		if state == 2 {
			done++
		}
	}
	return done
}
