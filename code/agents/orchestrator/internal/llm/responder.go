package llm

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"orchestrator/internal/model"
)

const responderSystemPrompt = "" +
	"You are a cryptography assistant. Use the tool outputs to answer the user. " +
	"Be clear, concise, and conversational. If clarification is required, ask one focused question."

const responderUserPrompt = "" +
	"User request: %s\n" +
	"Conversation summary: %s\n" +
	"Detected intent: %s (confidence: %.2f)\n" +
	"Entities: %s\n" +
	"Tool outputs (JSON): %s\n"

type Responder struct {
	registry *Registry
}

func NewResponder(registry *Registry) *Responder {
	return &Responder{registry: registry}
}

func (r *Responder) Generate(ctx context.Context, provider string, req Request, info ResponseInfo) (string, error) {
	client, err := r.registry.Get(provider)
	if err != nil {
		return "", err
	}

	payload, _ := json.Marshal(info.AgentOutputs)
	req.System = responderSystemPrompt
	req.ResponseFormat = "text"
	req.Messages = []model.Message{{
		Role: "user",
		Content: fmt.Sprintf(
			responderUserPrompt,
			info.UserText,
			defaultString(info.Summary, "(none)"),
			defaultString(info.IntentLabel, "unknown"),
			info.IntentConfidence,
			formatEntities(info.Entities),
			string(payload),
		),
	}}

	response, err := client.Generate(ctx, req)
	if err != nil {
		return "", err
	}

	return strings.TrimSpace(response.Content), nil
}

type ResponseInfo struct {
	UserText         string
	Summary          string
	IntentLabel      string
	IntentConfidence float64
	Entities         []model.Entity
	AgentOutputs     []model.AgentResult
}
