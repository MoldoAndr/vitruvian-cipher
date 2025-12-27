package model

import "time"

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type ConversationContext struct {
	History []Message         `json:"history,omitempty"`
	Summary string            `json:"summary,omitempty"`
	State   map[string]string `json:"state,omitempty"`
}

type LLMSelection struct {
	Provider          string            `json:"provider"`
	Profile           string            `json:"profile,omitempty"`
	PlannerProfile    string            `json:"planner_profile,omitempty"`
	APIKey            string            `json:"api_key,omitempty"`
	APIKeys           map[string]string `json:"api_keys,omitempty"`
	Model             string            `json:"model,omitempty"`
	Models            map[string]string `json:"models,omitempty"`
	PlannerModel      string            `json:"planner_model,omitempty"`
	PlannerModels     map[string]string `json:"planner_models,omitempty"`
	AllowFallback     bool              `json:"allow_fallback,omitempty"`
	FallbackProviders []string          `json:"fallback_providers,omitempty"`
}

type Preferences struct {
	Debug     bool `json:"debug,omitempty"`
	DirectRAG bool `json:"direct_rag,omitempty"`
}

type OrchestrateRequest struct {
	RequestID      string               `json:"request_id,omitempty"`
	ConversationID string               `json:"conversation_id"`
	Text           string               `json:"text"`
	Context        *ConversationContext `json:"context,omitempty"`
	LLM            LLMSelection         `json:"llm"`
	Preferences    *Preferences         `json:"preferences,omitempty"`
}

type IntentResult struct {
	Label      string            `json:"label"`
	Confidence float64           `json:"confidence"`
	Candidates []IntentCandidate `json:"candidates,omitempty"`
}

type IntentCandidate struct {
	Label string  `json:"label"`
	Score float64 `json:"score"`
}

type Entity struct {
	Type       string  `json:"type"`
	Value      string  `json:"value"`
	Confidence float64 `json:"confidence"`
	Start      int     `json:"start,omitempty"`
	End        int     `json:"end,omitempty"`
}

type ChoiceMakerResult struct {
	Intent   IntentResult `json:"intent"`
	Entities []Entity     `json:"entities"`
}

type ExecutionStep struct {
	Agent     string         `json:"agent"`
	Operation string         `json:"operation"`
	Params    map[string]any `json:"params"`
	DependsOn []int          `json:"depends_on,omitempty"`
}

type ExecutionPlan struct {
	Reasoning      string          `json:"reasoning,omitempty"`
	Steps          []ExecutionStep `json:"steps"`
	NeedsSynthesis bool            `json:"needs_synthesis"`
}

type AgentResult struct {
	Agent     string        `json:"agent"`
	Operation string        `json:"operation"`
	Output    any           `json:"output"`
	Duration  time.Duration `json:"duration"`
}

type SourceChunk struct {
	ChunkID        string         `json:"chunk_id"`
	RelevanceScore float64        `json:"relevance_score"`
	Preview        string         `json:"preview"`
	Metadata       map[string]any `json:"metadata"`
}

type OrchestrateResponse struct {
	RequestID          string            `json:"request_id,omitempty"`
	ConversationID     string            `json:"conversation_id"`
	Success            bool              `json:"success"`
	ExecutionPath      string            `json:"execution_path"`
	Intent             *IntentResult     `json:"intent,omitempty"`
	Entities           []Entity          `json:"entities,omitempty"`
	AgentsUsed         []string          `json:"agents_used,omitempty"`
	Reply              string            `json:"reply"`
	Clarification      bool              `json:"clarification"`
	Sources            []SourceChunk     `json:"sources,omitempty"`
	AgentConversations map[string]string `json:"agent_conversations,omitempty"`
	Diagnostics        map[string]any    `json:"diagnostics,omitempty"`
}
