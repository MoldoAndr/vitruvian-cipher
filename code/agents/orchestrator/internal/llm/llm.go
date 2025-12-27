package llm

import (
	"context"
	"fmt"
	"strings"

	"orchestrator/internal/model"
)

type Request struct {
	Model          string
	System         string
	Messages       []model.Message
	Temperature    float64
	MaxTokens      int
	ResponseFormat string
	APIKey         string
}

type Response struct {
	Content string
	Raw     any
}

type Client interface {
	Name() string
	Generate(ctx context.Context, req Request) (Response, error)
}

type Registry struct {
	providers map[string]Client
}

func NewRegistry(clients []Client) *Registry {
	reg := &Registry{providers: map[string]Client{}}
	for _, client := range clients {
		reg.providers[strings.ToLower(client.Name())] = client
	}
	return reg
}

func (r *Registry) Get(name string) (Client, error) {
	client, ok := r.providers[strings.ToLower(name)]
	if !ok {
		return nil, fmt.Errorf("llm provider %q not configured", name)
	}
	return client, nil
}
