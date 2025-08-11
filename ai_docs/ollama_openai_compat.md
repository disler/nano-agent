# Ollama OpenAI Compatibility

## Quick Start

```python
from openai import OpenAI

client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama',  # required but unused
)

response = client.chat.completions.create(
    model="llama2",  # or any model you have pulled
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

## Setup

1. Download and install Ollama
2. Pull a model: `ollama pull llama2`
3. Ollama runs on `http://localhost:11434`

## Available Models

Any model you have pulled with Ollama can be used. Popular options:

### Latest State-of-the-Art Models (August 2025)
- **gpt-oss:20b**: OpenAI's open-weight model optimized for 16GB GPUs, supports 131K context length
- **gpt-oss:120b**: OpenAI's larger model requiring 80GB GPU for enhanced capabilities
- **mistral:7b**: Mistral AI's efficient 7B parameter model with strong performance
- **mixtral:8x7b**: Mistral AI's mixture of experts model for robust multi-task performance
- **mistral:large**: Mistral AI's latest large model for advanced reasoning
- **magistral:small**: Mistral AI's first AI reasoning model with chain-of-thought capabilities (open-source)
- **magistral:medium**: Mistral AI's commercial reasoning model for complex problem-solving
- **gemma:2b**: Google's lightweight 2B parameter model for general text generation
- **gemma:7b**: Google's 7B parameter model with enhanced capabilities
- **qwen2:0.5b**: Alibaba's ultra-lightweight model for resource-constrained applications
- **qwen2:7b**: Alibaba's 7B parameter model with improved performance
- **llama3.2:3b**: Meta's latest 3B parameter model optimized for efficiency
- **llama3.2:8b**: Meta's 8B parameter model with enhanced reasoning
- **llama3.2:70b**: Meta's 70B parameter model for complex tasks
- **llama3.3:70b**: Meta's latest 70B model emphasizing cost-efficiency and performance
- **deepseek:r1**: DeepSeek's open-source model with strong coding and mathematics capabilities
- **grok:3**: xAI's real-time conversational AI with up-to-date information access

### Established Popular Models
- llama2
- codellama
- deepseek-coder
- phi
- neural-chat
- starling-lm
- orca-mini

To pull a model: `ollama pull <model_name>`

**Note**: The gpt-oss models are OpenAI's latest open-weight releases, offering enterprise-grade performance on consumer hardware. Use the exact model names with colons (e.g., `gpt-oss:20b`) when pulling models.

## Latest Model Capabilities (August 2025)

### Reasoning and Problem-Solving
- **Mistral Magistral Series**: First AI reasoning models with chain-of-thought capabilities for complex problem-solving
- **GPT-OSS Models**: Enhanced reasoning with configurable effort levels for agentic workflows
- **Llama 3.3**: Optimized for mathematical computations and instruction following

### Specialized Use Cases
- **DeepSeek R1**: Strong performance in coding assistance and mathematical problem-solving
- **Grok 3**: Real-time conversational AI with access to current information
- **Claude 4 Series**: Extended context windows and enhanced reasoning for long-horizon tasks

### Hardware Optimization
- **gpt-oss:20b**: Optimized for 16GB+ VRAM with 131K context support
- **gpt-oss:120b**: High-performance model requiring 80GB+ VRAM
- **Magistral Small**: Open-source reasoning model for accessible deployment

## API Endpoint

- Base URL: `http://localhost:11434/v1`
- Chat Completions: `/v1/chat/completions`

## cURL Example

```bash
curl http://localhost:11434/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "llama2",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ]
    }'
```

## Features Support

✅ Supported:
- Chat completions
- Streaming responses
- System/user/assistant messages
- Multi-turn conversations

⏳ Future (under consideration):
- Embeddings API
- Function calling
- Vision support
- Logprobs

## Key Notes

1. API key is required by OpenAI client libraries but not used by Ollama (can be any string)
2. Model name should match exactly what you've pulled with `ollama pull`
3. Runs locally on port 11434
4. Experimental support - GitHub issues welcome

## Integration Examples

### Vercel AI SDK
```typescript
const openai = new OpenAI({
    baseURL: 'http://localhost:11434/v1',
    apiKey: 'ollama',
});
```

### Autogen
```python
config_list = [
    {
        "model": "codellama",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
    }
]
```