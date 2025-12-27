package llm

import (
	"context"
	"fmt"
	"strings"

	"orchestrator/internal/model"
)

const plannerSystemPrompt = "" +
	"You are an orchestration planner for a cryptography assistant. " +
	"Produce a compact JSON execution plan. Output only JSON with keys: " +
	"reasoning, needs_synthesis, steps." +
	"Each step has: agent, operation, params, depends_on (optional array of step indexes)."

const plannerUserPrompt = "" +
	"User request: %s\n" +
	"Conversation summary: %s\n" +
	"Detected intent: %s (confidence: %.2f)\n" +
	"Entities: %s\n" +
	"Signals: %s\n" +
	"Available agents: %s\n" +
	"Allowed operations per agent: %s\n" +
	"If a single agent can answer, return one step. If clarification is needed, return zero steps and set needs_synthesis=false with reasoning asking for missing info."

type Planner struct {
	registry *Registry
}

func NewPlanner(registry *Registry) *Planner {
	return &Planner{registry: registry}
}

func (p *Planner) BuildPlan(ctx context.Context, provider string, req Request, info PlanInfo) (model.ExecutionPlan, error) {
	client, err := p.registry.Get(provider)
	if err != nil {
		return model.ExecutionPlan{}, err
	}
	req.System = plannerSystemPrompt
	req.ResponseFormat = "json"
	req.Messages = []model.Message{{
		Role: "user",
		Content: fmt.Sprintf(
			plannerUserPrompt,
			info.UserText,
			defaultString(info.Summary, "(none)"),
			defaultString(info.IntentLabel, "unknown"),
			info.IntentConfidence,
			formatEntities(info.Entities),
			formatSignals(info.Signals),
			strings.Join(info.Agents, ", "),
			formatOperations(info.AgentOperations),
		),
	}}

	response, err := client.Generate(ctx, req)
	if err != nil {
		return model.ExecutionPlan{}, err
	}

	var plan model.ExecutionPlan
	if err := ExtractJSON(response.Content, &plan); err != nil {
		return model.ExecutionPlan{}, fmt.Errorf("planner json parse: %w", err)
	}

	return plan, nil
}

type PlanInfo struct {
	UserText         string
	Summary          string
	IntentLabel      string
	IntentConfidence float64
	Entities         []model.Entity
	Signals          map[string]string
	Agents           []string
	AgentOperations  map[string][]string
}

func formatEntities(entities []model.Entity) string {
	if len(entities) == 0 {
		return "(none)"
	}
	parts := make([]string, 0, len(entities))
	for _, ent := range entities {
		parts = append(parts, fmt.Sprintf("%s=%s(%.2f)", ent.Type, ent.Value, ent.Confidence))
	}
	return strings.Join(parts, "; ")
}

func formatSignals(sig map[string]string) string {
	if len(sig) == 0 {
		return "(none)"
	}
	parts := make([]string, 0, len(sig))
	for key, val := range sig {
		parts = append(parts, fmt.Sprintf("%s=%s", key, val))
	}
	return strings.Join(parts, "; ")
}

func formatOperations(ops map[string][]string) string {
	if len(ops) == 0 {
		return "(none)"
	}
	parts := make([]string, 0, len(ops))
	for agent, list := range ops {
		parts = append(parts, fmt.Sprintf("%s: %s", agent, strings.Join(list, ", ")))
	}
	return strings.Join(parts, " | ")
}

func defaultString(value, fallback string) string {
	if strings.TrimSpace(value) == "" {
		return fallback
	}
	return value
}
