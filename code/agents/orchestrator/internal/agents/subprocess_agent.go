package agents

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os/exec"
	"time"
)

type CommandSpec struct {
	Command string
	Args    []string
	Timeout time.Duration
}

type SubprocessAgent struct {
	name  string
	specs map[string]CommandSpec
}

func NewSubprocessAgent(name string, specs map[string]CommandSpec) *SubprocessAgent {
	return &SubprocessAgent{
		name:  name,
		specs: specs,
	}
}

func (a *SubprocessAgent) Name() string {
	return a.name
}

func (a *SubprocessAgent) Execute(ctx context.Context, operation string, params map[string]any) (any, error) {
	spec, ok := a.specs[operation]
	if !ok {
		return nil, fmt.Errorf("subprocess op %q not found for %s", operation, a.name)
	}
	payload, err := json.Marshal(params)
	if err != nil {
		return nil, fmt.Errorf("marshal payload: %w", err)
	}

	execCtx := ctx
	if spec.Timeout > 0 {
		var cancel context.CancelFunc
		execCtx, cancel = context.WithTimeout(ctx, spec.Timeout)
		defer cancel()
	}

	cmd := exec.CommandContext(execCtx, spec.Command, spec.Args...)
	cmd.Stdin = bytes.NewReader(payload)
	var out bytes.Buffer
	var stderr bytes.Buffer
	cmd.Stdout = &out
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		return nil, fmt.Errorf("subprocess %s failed: %w: %s", a.name, err, stderr.String())
	}

	var decoded any
	if err := json.Unmarshal(out.Bytes(), &decoded); err != nil {
		return nil, fmt.Errorf("subprocess %s invalid JSON: %w", a.name, err)
	}
	return decoded, nil
}
