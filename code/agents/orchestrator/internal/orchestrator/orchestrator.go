package orchestrator

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"strings"
	"time"

	"golang.org/x/sync/errgroup"

	"orchestrator/internal/agents"
	"orchestrator/internal/choice"
	"orchestrator/internal/config"
	"orchestrator/internal/executor"
	"orchestrator/internal/llm"
	"orchestrator/internal/model"
	"orchestrator/internal/normalize"
	"orchestrator/internal/router"
	"orchestrator/internal/signals"
)

type Engine struct {
	cfg       config.Config
	chooser   *choice.Client
	router    *router.Router
	planner   *llm.Planner
	responder *llm.Responder
	executor  *executor.Executor
	registry  *llm.Registry
	pool      *agents.Pool
}

func New(cfg config.Config, chooser *choice.Client, route *router.Router, planner *llm.Planner, responder *llm.Responder, exec *executor.Executor, registry *llm.Registry, pool *agents.Pool) *Engine {
	return &Engine{
		cfg:       cfg,
		chooser:   chooser,
		router:    route,
		planner:   planner,
		responder: responder,
		executor:  exec,
		registry:  registry,
		pool:      pool,
	}
}

func (e *Engine) Handle(ctx context.Context, req model.OrchestrateRequest) (model.OrchestrateResponse, error) {
	if strings.TrimSpace(req.Text) == "" {
		return model.OrchestrateResponse{}, errors.New("text is required")
	}
	if req.ConversationID == "" {
		return model.OrchestrateResponse{}, errors.New("conversation_id is required")
	}
	if strings.TrimSpace(req.LLM.Provider) == "" {
		return model.OrchestrateResponse{}, errors.New("llm.provider is required")
	}

	requestID := req.RequestID
	if requestID == "" {
		requestID = newRequestID()
	}

	normalized := normalize.Text(req.Text)
	sig := signals.Analyze(normalized)
	sigMap := sig.Map()
	summary := ""
	state := map[string]string(nil)
	if req.Context != nil {
		summary = req.Context.Summary
		state = req.Context.State
	}

	intentResult, entities, choiceErr := e.runChoiceMaker(ctx, req.Text)
	if choiceErr != nil {
		intentResult = model.IntentResult{Label: "unknown", Confidence: 0.0}
	}

	response := model.OrchestrateResponse{
		RequestID:      requestID,
		ConversationID: req.ConversationID,
		Success:        true,
		ExecutionPath:  "fast",
		Intent:         &intentResult,
		Entities:       entities,
		AgentsUsed:     []string{},
		Reply:          "",
		Clarification:  false,
	}

	route, ok := e.router.Match(intentResult.Label)
	missing := []string{}
	params := map[string]any{}
	if ok && e.router.ShouldUseFastPath(intentResult) {
		params, missing = e.router.BuildParams(route, entities, sig, req.Text, normalized, req.ConversationID, summary, state)
	} else {
		ok = false
	}

	var plan model.ExecutionPlan
	if ok && len(missing) == 0 {
		plan = model.ExecutionPlan{
			Steps: []model.ExecutionStep{{
				Agent:     route.Agent,
				Operation: route.Operation,
				Params:    params,
			}},
			NeedsSynthesis: true,
		}
	} else {
		response.ExecutionPath = "complex"
		if len(missing) > 0 {
			response.Clarification = true
			response.Reply = e.clarify(ctx, req, intentResult, entities, sigMap, missing)
			if req.Preferences != nil && req.Preferences.Debug {
				response.Diagnostics = map[string]any{
					"missing_slots": missing,
				}
			}
			return response, nil
		}

		planInfo := llm.PlanInfo{
			UserText:         req.Text,
			Summary:          summary,
			IntentLabel:      intentResult.Label,
			IntentConfidence: intentResult.Confidence,
			Entities:         entities,
			Signals:          sigMap,
			Agents:           e.pool.Names(),
			AgentOperations:  agentsOperationMap(),
		}
		builtPlan, err := e.planWithFallback(ctx, req, planInfo)
		if err != nil {
			return model.OrchestrateResponse{}, err
		}
		plan = builtPlan
		if len(plan.Steps) == 0 {
			response.Clarification = true
			response.Reply = e.clarify(ctx, req, intentResult, entities, sigMap, []string{"more_details"})
			return response, nil
		}
	}

	if err := normalizePlan(&plan); err != nil {
		return model.OrchestrateResponse{}, err
	}
	outputs, err := e.executor.Run(ctx, plan)
	if err != nil {
		return model.OrchestrateResponse{}, err
	}
	for _, output := range outputs {
		response.AgentsUsed = append(response.AgentsUsed, output.Agent)
	}

	theoryAnswer, sources, theoryConvID := extractTheoryOutput(outputs)
	if len(sources) > 0 {
		response.Sources = sources
	}
	if theoryConvID != "" {
		response.AgentConversations = map[string]string{
			"theory_specialist": theoryConvID,
		}
	}
	if req.Preferences != nil && req.Preferences.DirectRAG && theoryAnswer != "" {
		response.Reply = theoryAnswer
		response.Clarification = false
	} else {
		responseText, err := e.respond(ctx, req, intentResult, entities, outputs)
		if err != nil {
			return model.OrchestrateResponse{}, err
		}
		response.Reply = responseText
	}

	if req.Preferences != nil && req.Preferences.Debug {
		response.Diagnostics = map[string]any{
			"signals":       sigMap,
			"plan":          plan,
			"choice_error":  errorString(choiceErr),
			"agent_outputs": outputs,
		}
	}

	return response, nil
}

func (e *Engine) runChoiceMaker(ctx context.Context, text string) (model.IntentResult, []model.Entity, error) {
	var intent model.IntentResult
	var entities []model.Entity

	group, ctx := errgroup.WithContext(ctx)
	group.Go(func() error {
		result, err := e.chooser.Intent(ctx, text)
		if err != nil {
			return err
		}
		intent = result
		return nil
	})
	group.Go(func() error {
		result, err := e.chooser.Entities(ctx, text)
		if err != nil {
			return err
		}
		entities = result
		return nil
	})

	if err := group.Wait(); err != nil {
		return model.IntentResult{}, nil, err
	}
	return intent, entities, nil
}

func normalizePlan(plan *model.ExecutionPlan) error {
	for i := range plan.Steps {
		step := &plan.Steps[i]
		step.Agent = strings.ToLower(strings.TrimSpace(step.Agent))
		step.Operation = agents.NormalizeOperation(step.Agent, step.Operation)
		if !agents.SupportsOperation(step.Agent, step.Operation) {
			return fmt.Errorf("operation %q not supported by %s", step.Operation, step.Agent)
		}
	}
	return nil
}

func agentsOperationMap() map[string][]string {
	out := map[string][]string{}
	for agent, ops := range agents.DefaultOperations {
		list := make([]string, 0, len(ops))
		for name := range ops {
			list = append(list, name)
		}
		out[agent] = list
	}
	return out
}

func extractTheoryOutput(outputs []model.AgentResult) (string, []model.SourceChunk, string) {
	for _, output := range outputs {
		if output.Agent != "theory_specialist" {
			continue
		}
		payload, ok := output.Output.(map[string]any)
		if !ok {
			return "", nil, ""
		}
		answer, _ := payload["answer"].(string)
		conversationID, _ := payload["conversation_id"].(string)
		sources := parseSources(payload["sources"])
		return answer, sources, conversationID
	}
	return "", nil, ""
}

func parseSources(raw any) []model.SourceChunk {
	list, ok := raw.([]any)
	if !ok {
		return nil
	}
	out := make([]model.SourceChunk, 0, len(list))
	for _, item := range list {
		entry, ok := item.(map[string]any)
		if !ok {
			continue
		}
		out = append(out, model.SourceChunk{
			ChunkID:        asString(entry["chunk_id"]),
			RelevanceScore: asFloat(entry["relevance_score"]),
			Preview:        asString(entry["preview"]),
			Metadata:       asMap(entry["metadata"]),
		})
	}
	return out
}

func asString(value any) string {
	if value == nil {
		return ""
	}
	switch val := value.(type) {
	case string:
		return val
	default:
		return fmt.Sprintf("%v", val)
	}
}

func asFloat(value any) float64 {
	switch v := value.(type) {
	case float64:
		return v
	case float32:
		return float64(v)
	case int:
		return float64(v)
	case int64:
		return float64(v)
	case uint64:
		return float64(v)
	default:
		return 0
	}
}

func asMap(value any) map[string]any {
	if value == nil {
		return map[string]any{}
	}
	if m, ok := value.(map[string]any); ok {
		return m
	}
	return map[string]any{}
}

func (e *Engine) resolveModel(profile, provider string) (string, error) {
	profiles := e.cfg.LLM.Profiles
	byProvider, ok := profiles[profile]
	if !ok {
		return "", fmt.Errorf("llm profile %q not defined", profile)
	}
	modelName, ok := byProvider[strings.ToLower(provider)]
	if !ok || strings.TrimSpace(modelName) == "" {
		return "", fmt.Errorf("no model for provider %q in profile %q", provider, profile)
	}
	return modelName, nil
}

func (e *Engine) resolvePlannerProfile(req model.OrchestrateRequest) string {
	if req.LLM.PlannerProfile != "" {
		return req.LLM.PlannerProfile
	}
	return e.cfg.Orchestrator.PlannerProfile
}

func (e *Engine) resolveResponderProfile(req model.OrchestrateRequest) string {
	if req.LLM.Profile != "" {
		return req.LLM.Profile
	}
	return e.cfg.Orchestrator.ResponderProfile
}

func (e *Engine) planWithFallback(ctx context.Context, req model.OrchestrateRequest, info llm.PlanInfo) (model.ExecutionPlan, error) {
	providers := providerOrder(req.LLM.Provider, req.LLM.AllowFallback, req.LLM.FallbackProviders)
	var lastErr error
	for _, provider := range providers {
		planReq, err := e.prepareLLMRequest(req, e.resolvePlannerProfile(req), provider, "planner")
		if err != nil {
			lastErr = err
			continue
		}
		plan, err := e.planner.BuildPlan(ctx, provider, planReq, info)
		if err == nil {
			return plan, nil
		}
		lastErr = err
	}
	return model.ExecutionPlan{}, fmt.Errorf("planner failed: %w", lastErr)
}

func (e *Engine) respond(ctx context.Context, req model.OrchestrateRequest, intent model.IntentResult, entities []model.Entity, outputs []model.AgentResult) (string, error) {
	profile := e.resolveResponderProfile(req)
	providers := providerOrder(req.LLM.Provider, req.LLM.AllowFallback, req.LLM.FallbackProviders)
	info := llm.ResponseInfo{
		UserText:         req.Text,
		Summary:          "",
		IntentLabel:      intent.Label,
		IntentConfidence: intent.Confidence,
		Entities:         entities,
		AgentOutputs:     outputs,
	}
	if req.Context != nil {
		info.Summary = req.Context.Summary
	}

	var lastErr error
	for _, provider := range providers {
		respReq, err := e.prepareLLMRequest(req, profile, provider, "responder")
		if err != nil {
			lastErr = err
			continue
		}
		text, err := e.responder.Generate(ctx, provider, respReq, info)
		if err == nil {
			return text, nil
		}
		lastErr = err
	}
	return "", fmt.Errorf("response generation failed: %w", lastErr)
}

func (e *Engine) clarify(ctx context.Context, req model.OrchestrateRequest, intent model.IntentResult, entities []model.Entity, sig map[string]string, missing []string) string {
	outputs := []model.AgentResult{{
		Agent:     "clarifier",
		Operation: "missing_slots",
		Output: map[string]any{
			"missing": missing,
		},
		Duration: 0,
	}}

	text, err := e.respond(ctx, req, intent, entities, outputs)
	if err != nil {
		return fmt.Sprintf("I need a bit more detail (%s).", strings.Join(missing, ", "))
	}
	return text
}

func (e *Engine) prepareLLMRequest(req model.OrchestrateRequest, profile, provider, role string) (llm.Request, error) {
	modelName, err := e.resolveModelWithOverrides(req.LLM, profile, provider, role)
	if err != nil {
		return llm.Request{}, err
	}
	providerCfg, ok := e.cfg.LLM.Providers[strings.ToLower(provider)]
	if !ok {
		return llm.Request{}, fmt.Errorf("llm provider %q not configured", provider)
	}
	return llm.Request{
		Model:       modelName,
		Temperature: providerCfg.Temperature,
		MaxTokens:   providerCfg.MaxTokens,
		APIKey:      resolveAPIKey(req.LLM, provider, providerCfg.APIKey),
	}, nil
}

func (e *Engine) resolveModelWithOverrides(selection model.LLMSelection, profile, provider, role string) (string, error) {
	override := resolveModelOverride(selection, provider, role)
	if override != "" {
		return override, nil
	}
	return e.resolveModel(profile, provider)
}

func resolveModelOverride(selection model.LLMSelection, provider, role string) string {
	provider = strings.ToLower(provider)
	switch role {
	case "planner":
		if selection.PlannerModels != nil {
			if value := strings.TrimSpace(selection.PlannerModels[provider]); value != "" {
				return value
			}
		}
		if strings.EqualFold(selection.Provider, provider) {
			if value := strings.TrimSpace(selection.PlannerModel); value != "" {
				return value
			}
		}
	default:
		if selection.Models != nil {
			if value := strings.TrimSpace(selection.Models[provider]); value != "" {
				return value
			}
		}
		if strings.EqualFold(selection.Provider, provider) {
			if value := strings.TrimSpace(selection.Model); value != "" {
				return value
			}
		}
	}
	return ""
}

func resolveAPIKey(selection model.LLMSelection, provider string, fallbackKey string) string {
	provider = strings.ToLower(provider)
	if selection.APIKeys != nil {
		if key, ok := selection.APIKeys[provider]; ok && strings.TrimSpace(key) != "" {
			return key
		}
	}
	if strings.EqualFold(selection.Provider, provider) && strings.TrimSpace(selection.APIKey) != "" {
		return selection.APIKey
	}
	return fallbackKey
}

func providerOrder(primary string, allowFallback bool, fallback []string) []string {
	providers := []string{primary}
	if allowFallback {
		for _, name := range fallback {
			if name == "" {
				continue
			}
			if strings.EqualFold(name, primary) {
				continue
			}
			providers = append(providers, name)
		}
	}
	return providers
}

func newRequestID() string {
	buf := make([]byte, 12)
	if _, err := rand.Read(buf); err != nil {
		return fmt.Sprintf("req-%d", time.Now().UnixNano())
	}
	return "req-" + hex.EncodeToString(buf)
}

func errorString(err error) string {
	if err == nil {
		return ""
	}
	return err.Error()
}
