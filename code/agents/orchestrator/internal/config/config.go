package config

import (
	"errors"
	"fmt"
	"os"
	"strings"
	"time"

	"gopkg.in/yaml.v3"
)

type Duration struct {
	time.Duration
}

func (d *Duration) UnmarshalYAML(value *yaml.Node) error {
	if value.Kind != yaml.ScalarNode {
		return fmt.Errorf("invalid duration type: %v", value.Kind)
	}
	raw := strings.TrimSpace(value.Value)
	if raw == "" {
		d.Duration = 0
		return nil
	}
	parsed, err := time.ParseDuration(raw)
	if err != nil {
		return fmt.Errorf("invalid duration %q: %w", raw, err)
	}
	d.Duration = parsed
	return nil
}

type ServerConfig struct {
	Address      string   `yaml:"address"`
	ReadTimeout  Duration `yaml:"read_timeout"`
	WriteTimeout Duration `yaml:"write_timeout"`
	IdleTimeout  Duration `yaml:"idle_timeout"`
}

type ChoiceMakerConfig struct {
	BaseURL string   `yaml:"base_url"`
	Timeout Duration `yaml:"timeout"`
}

type AgentConfig struct {
	BaseURL string   `yaml:"base_url"`
	Timeout Duration `yaml:"timeout"`
}

type RouteConfig struct {
	Intents       []string            `yaml:"intents"`
	Agent         string              `yaml:"agent"`
	Operation     string              `yaml:"operation"`
	Slots         map[string][]string `yaml:"slots"`
	OptionalSlots []string            `yaml:"optional_slots"`
}

type RoutingConfig struct {
	Routes []RouteConfig `yaml:"routes"`
}

type ProviderConfig struct {
	BaseURL     string   `yaml:"base_url"`
	APIKey      string   `yaml:"api_key"`
	Timeout     Duration `yaml:"timeout"`
	MaxTokens   int      `yaml:"max_tokens"`
	Temperature float64  `yaml:"temperature"`
}

type LLMConfig struct {
	Profiles  map[string]map[string]string `yaml:"profiles"`
	Providers map[string]ProviderConfig    `yaml:"providers"`
}

type OrchestratorConfig struct {
	IntentThreshold  float64 `yaml:"intent_threshold"`
	EntityThreshold  float64 `yaml:"entity_threshold"`
	MaxParallel      int     `yaml:"max_parallel"`
	PlannerProfile   string  `yaml:"planner_profile"`
	ResponderProfile string  `yaml:"responder_profile"`
}

type Config struct {
	Server       ServerConfig           `yaml:"server"`
	ChoiceMaker  ChoiceMakerConfig      `yaml:"choice_maker"`
	Agents       map[string]AgentConfig `yaml:"agents"`
	Routing      RoutingConfig          `yaml:"routing"`
	LLM          LLMConfig              `yaml:"llm"`
	Orchestrator OrchestratorConfig     `yaml:"orchestrator"`
}

func Load(path string) (Config, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return Config{}, fmt.Errorf("read config: %w", err)
	}
	expanded := expandEnv(string(raw))
	var cfg Config
	if err := yaml.Unmarshal([]byte(expanded), &cfg); err != nil {
		return Config{}, fmt.Errorf("parse config: %w", err)
	}
	applyDefaults(&cfg)
	if err := validate(cfg); err != nil {
		return Config{}, err
	}
	return cfg, nil
}

func expandEnv(input string) string {
	var out strings.Builder
	out.Grow(len(input))
	for i := 0; i < len(input); i++ {
		if input[i] != '$' || i+1 >= len(input) || input[i+1] != '{' {
			out.WriteByte(input[i])
			continue
		}
		end := strings.IndexByte(input[i+2:], '}')
		if end == -1 {
			out.WriteByte(input[i])
			continue
		}
		end = end + i + 2
		key := input[i+2 : end]
		value := os.Getenv(key)
		out.WriteString(value)
		i = end
	}
	return out.String()
}

func applyDefaults(cfg *Config) {
	if cfg.Server.Address == "" {
		cfg.Server.Address = ":8200"
	}
	if cfg.Server.ReadTimeout.Duration == 0 {
		cfg.Server.ReadTimeout.Duration = 5 * time.Second
	}
	if cfg.Server.WriteTimeout.Duration == 0 {
		cfg.Server.WriteTimeout.Duration = 30 * time.Second
	}
	if cfg.Server.IdleTimeout.Duration == 0 {
		cfg.Server.IdleTimeout.Duration = 60 * time.Second
	}
	if cfg.ChoiceMaker.Timeout.Duration == 0 {
		cfg.ChoiceMaker.Timeout.Duration = 10 * time.Second
	}
	if cfg.Orchestrator.IntentThreshold == 0 {
		cfg.Orchestrator.IntentThreshold = 0.85
	}
	if cfg.Orchestrator.EntityThreshold == 0 {
		cfg.Orchestrator.EntityThreshold = 0.6
	}
	if cfg.Orchestrator.MaxParallel == 0 {
		cfg.Orchestrator.MaxParallel = 4
	}
	if cfg.Orchestrator.PlannerProfile == "" {
		cfg.Orchestrator.PlannerProfile = "planner"
	}
	if cfg.Orchestrator.ResponderProfile == "" {
		cfg.Orchestrator.ResponderProfile = "responder"
	}
}

func validate(cfg Config) error {
	if cfg.ChoiceMaker.BaseURL == "" {
		return errors.New("choice_maker.base_url is required")
	}
	if len(cfg.Routing.Routes) == 0 {
		return errors.New("routing.routes must not be empty")
	}
	if len(cfg.LLM.Providers) == 0 {
		return errors.New("llm.providers must not be empty")
	}
	if len(cfg.LLM.Profiles) == 0 {
		return errors.New("llm.profiles must not be empty")
	}
	return nil
}
