# Orchestrator Service

A lightweight Go service that orchestrates the Choice Maker intent/entity pipeline, routes to the correct agent(s), and synthesizes a natural-language response with the selected LLM provider.

## Features
- Stateless orchestrator (conversation context supplied per request)
- Fast path routing via Choice Maker + deterministic signals
- LLM planning fallback for ambiguous or multi-step requests
- Per-conversation LLM provider selection (OpenAI, Anthropic, Gemini, Ollama local/cloud)
- Config-driven profiles and thresholds

## Run

```bash
cd code/agents/orchestrator
cp config.yaml config.local.yaml
# Edit config.local.yaml and export API keys
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
export GEMINI_API_KEY=...

# Run
go run ./cmd/orchestrator -config config.local.yaml
```

## Docker

```bash
cd code/agents/orchestrator
docker build -t orchestrator:local .
docker run --rm -p 8200:8200 \\
  -e OPENAI_API_KEY=... \\
  -e ANTHROPIC_API_KEY=... \\
  -e GEMINI_API_KEY=... \\
  orchestrator:local
```

## API

### POST /v1/orchestrate

```json
{
  "conversation_id": "c_123",
  "text": "Check if P@ssw0rd! is strong",
  "context": {
    "summary": "Previous discussion about password hygiene",
    "state": {
      "theory_conversation_id": "rag-conv-123"
    }
  },
  "llm": {
    "provider": "openai",
    "profile": "responder",
    "planner_profile": "planner",
    "model": "deepseek-v3.2:cloud",
    "planner_model": "deepseek-v3.2:cloud",
    "api_key": "sk-...",
    "api_keys": {
      "openai": "sk-...",
      "anthropic": "sk-ant-...",
      "gemini": "AIza..."
    }
  }
}
```

To bypass the LLM for Theory Specialist and return the RAG answer directly (with sources), set:

```json
"preferences": { "direct_rag": true }
```

When Theory Specialist is used, the orchestrator includes:
- `sources`: the RAG citation chunks
- `agent_conversations.theory_specialist`: the RAG conversation id

### GET /health

Returns `{ "status": "ok" }`.

## Configuration
See `config.yaml` for defaults and model profiles. Environment variables are expanded (e.g., `${OPENAI_API_KEY}`).
For Ollama Cloud, set `llm.providers.ollama_cloud.base_url` to `https://ollama.com`.
If Theory Specialist responses time out, increase `agents.theory_specialist.timeout` (RAG + LLM can be slow).
