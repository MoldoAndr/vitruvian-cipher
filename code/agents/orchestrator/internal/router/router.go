package router

import (
	"strings"

	"orchestrator/internal/model"
	"orchestrator/internal/signals"
)

type Route struct {
	Intents       []string
	Agent         string
	Operation     string
	Slots         map[string][]string
	OptionalSlots map[string]struct{}
}

type Router struct {
	routes          []Route
	intentThreshold float64
	entityThreshold float64
}

func New(routes []Route, intentThreshold, entityThreshold float64) *Router {
	return &Router{
		routes:          routes,
		intentThreshold: intentThreshold,
		entityThreshold: entityThreshold,
	}
}

func (r *Router) Match(intent string) (Route, bool) {
	lowered := strings.ToLower(intent)
	for _, route := range r.routes {
		for _, candidate := range route.Intents {
			if strings.ToLower(candidate) == lowered {
				return route, true
			}
		}
	}
	return Route{}, false
}

func (r *Router) ShouldUseFastPath(intent model.IntentResult) bool {
	return intent.Confidence >= r.intentThreshold
}

func (r *Router) BuildParams(
	route Route,
	entities []model.Entity,
	sig signals.Signals,
	rawText string,
	normalizedText string,
	conversationID string,
	summary string,
	state map[string]string,
) (map[string]any, []string) {
	entityMap := buildEntityMap(entities, r.entityThreshold)
	sigMap := sig.Map()
	params := map[string]any{}
	var missing []string

	for field, candidates := range route.Slots {
		value, ok := resolveSlot(field, candidates, entityMap, sigMap, rawText, normalizedText, conversationID, summary, state)
		if !ok {
			if _, optional := route.OptionalSlots[field]; !optional {
				missing = append(missing, field)
			}
			continue
		}
		params[field] = value
	}

	return params, missing
}

func buildEntityMap(entities []model.Entity, threshold float64) map[string]model.Entity {
	out := map[string]model.Entity{}
	for _, ent := range entities {
		if ent.Confidence < threshold {
			continue
		}
		key := strings.ToLower(ent.Type)
		existing, ok := out[key]
		if !ok || ent.Confidence > existing.Confidence {
			out[key] = ent
		}
	}
	return out
}

func resolveSlot(
	field string,
	candidates []string,
	entities map[string]model.Entity,
	sigMap map[string]string,
	rawText string,
	normalizedText string,
	conversationID string,
	summary string,
	state map[string]string,
) (string, bool) {
	for _, candidate := range candidates {
		candidate = strings.TrimSpace(candidate)
		if candidate == "" {
			continue
		}
		if strings.HasPrefix(candidate, "$") {
			switch strings.ToLower(candidate) {
			case "$text":
				return rawText, rawText != ""
			case "$normalized":
				return normalizedText, normalizedText != ""
			case "$summary":
				return summary, summary != ""
			case "$conversation_id":
				return conversationID, conversationID != ""
			}
			if strings.HasPrefix(strings.ToLower(candidate), "$state:") {
				key := strings.TrimSpace(candidate[len("$state:"):])
				if key == "" {
					continue
				}
				if state != nil {
					if value, ok := state[key]; ok && strings.TrimSpace(value) != "" {
						return value, true
					}
				}
			}
			continue
		}
		if ent, ok := entities[strings.ToLower(candidate)]; ok {
			return ent.Value, ent.Value != ""
		}
		if sigVal, ok := sigMap[strings.ToLower(candidate)]; ok {
			return sigVal, sigVal != ""
		}
	}

	switch strings.ToLower(field) {
	case "input", "query", "text", "message":
		if rawText != "" {
			return rawText, true
		}
	}
	return "", false
}
