package main

import (
	"flag"
	"log/slog"
	"net/http"
	"os"
	"time"

	"orchestrator/internal/agents"
	"orchestrator/internal/choice"
	"orchestrator/internal/config"
	"orchestrator/internal/executor"
	"orchestrator/internal/httpapi"
	"orchestrator/internal/llm"
	"orchestrator/internal/orchestrator"
	"orchestrator/internal/router"
)

func main() {
	configPath := flag.String("config", "config.yaml", "Path to orchestrator config")
	flag.Parse()

	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))

	cfg, err := config.Load(*configPath)
	if err != nil {
		logger.Error("load config", "error", err)
		os.Exit(1)
	}

	choiceClient := choice.New(cfg.ChoiceMaker.BaseURL, cfg.ChoiceMaker.Timeout.Duration)

	routes := buildRoutes(cfg)
	routeEngine := router.New(routes, cfg.Orchestrator.IntentThreshold, cfg.Orchestrator.EntityThreshold)

	agentPool := buildAgentPool(cfg, logger)
	exec := executor.New(agentPool, cfg.Orchestrator.MaxParallel)

	llmRegistry := buildLLMRegistry(cfg, logger)
	planner := llm.NewPlanner(llmRegistry)
	responder := llm.NewResponder(llmRegistry)

	engine := orchestrator.New(cfg, choiceClient, routeEngine, planner, responder, exec, llmRegistry, agentPool)
	server := httpapi.NewServer(engine)

	httpServer := &http.Server{
		Addr:         cfg.Server.Address,
		Handler:      server.Router(),
		ReadTimeout:  cfg.Server.ReadTimeout.Duration,
		WriteTimeout: cfg.Server.WriteTimeout.Duration,
		IdleTimeout:  cfg.Server.IdleTimeout.Duration,
	}

	logger.Info("orchestrator starting", "address", cfg.Server.Address)
	if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		logger.Error("orchestrator stopped", "error", err)
		os.Exit(1)
	}
}

func buildRoutes(cfg config.Config) []router.Route {
	routes := make([]router.Route, 0, len(cfg.Routing.Routes))
	for _, rc := range cfg.Routing.Routes {
		optional := map[string]struct{}{}
		for _, slot := range rc.OptionalSlots {
			optional[slot] = struct{}{}
		}
		route := router.Route{
			Intents:       rc.Intents,
			Agent:         rc.Agent,
			Operation:     rc.Operation,
			Slots:         rc.Slots,
			OptionalSlots: optional,
		}
		routes = append(routes, route)
	}
	return routes
}

func buildAgentPool(cfg config.Config, logger *slog.Logger) *agents.Pool {
	var agentList []agents.Agent
	for name, agentCfg := range cfg.Agents {
		ops, ok := agents.DefaultOperations[name]
		if !ok {
			logger.Warn("unknown agent, skipping", "agent", name)
			continue
		}
		timeout := agentCfg.Timeout.Duration
		if timeout == 0 {
			timeout = 10 * time.Second
		}
		agentList = append(agentList, agents.NewHTTPAgent(name, agentCfg.BaseURL, ops, timeout))
	}
	return agents.NewPool(agentList)
}

func buildLLMRegistry(cfg config.Config, logger *slog.Logger) *llm.Registry {
	var providers []llm.Client
	for name, provider := range cfg.LLM.Providers {
		timeout := provider.Timeout.Duration
		if timeout == 0 {
			timeout = 20 * time.Second
		}
		switch name {
		case "openai":
			providers = append(providers, llm.NewOpenAI(provider.BaseURL, provider.APIKey, timeout))
		case "anthropic":
			providers = append(providers, llm.NewAnthropic(provider.BaseURL, provider.APIKey, timeout))
		case "gemini":
			providers = append(providers, llm.NewGemini(provider.BaseURL, provider.APIKey, timeout))
		case "ollama_local", "ollama_cloud":
			providers = append(providers, llm.NewOllama(name, provider.BaseURL, provider.APIKey, timeout))
		default:
			logger.Warn("unknown llm provider", "provider", name)
		}
	}
	return llm.NewRegistry(providers)
}
