package service

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/go-resty/resty/v2"
)

type AIClient struct {
	baseURL string
	token   string
	client  *resty.Client
}

func NewAIClient(baseURL, token string) *AIClient {
	return &AIClient{
		baseURL: strings.TrimRight(baseURL, "/"),
		token:   token,
		client:  resty.New().SetTimeout(10 * time.Second),
	}
}

func (c *AIClient) Health(ctx context.Context) (map[string]string, error) {
	payload := map[string]string{}
	resp, err := c.client.R().
		SetContext(ctx).
		SetHeader("X-Internal-Service-Token", c.token).
		SetResult(&payload).
		Get(c.baseURL + "/ai/health")
    
	if err != nil {
		return nil, err
	}
	if resp.StatusCode() >= 400 {
		return nil, fmt.Errorf("python ai service returned status %d", resp.StatusCode())
	}
	return payload, nil
}
