# OpenAI Agents SDK - Model Configuration Documentation

## Overview
The OpenAI Agents SDK supports multiple model providers through different configuration approaches.

## Supported Model Types

### 1. OpenAI Models (Built-in Support)

#### OpenAIResponsesModel (Recommended)
- Uses the new Responses API
- Default model type for OpenAI models
- Supports structured outputs, multimodal input, hosted file/web search

#### OpenAIChatCompletionsModel
- Uses the Chat Completions API
- Fallback for providers without Responses API support
- More widely compatible with OpenAI-compatible endpoints

### 2. Latest Model Families (August 2025)

#### GPT-5 Series
- **gpt-5**: Flagship reasoning model with PhD-level expertise
- **gpt-5-mini**: 80% of GPT-5 capabilities at 20% cost
- **gpt-5-nano**: Ultra-lightweight for edge deployment
- **gpt-5-chat-latest**: Non-reasoning chat model for fast responses

#### GPT-OSS Series
- **gpt-oss:20b**: Open-weight model for consumer hardware (16GB+ VRAM)
- **gpt-oss:120b**: High-performance open-weight model (80GB+ VRAM)
- **License**: Apache 2.0 - Free for commercial use
- **Availability**: Local deployment via Ollama, cloud via AWS Bedrock

## Non-OpenAI Model Integration

### Method 1: LiteLLM Integration (Simplest)
```python
# Install: pip install "openai-agents[litellm]"

# Use any supported model with litellm/ prefix
claude_agent = Agent(model="litellm/anthropic/claude-3-5-sonnet-20240620", ...)
gemini_agent = Agent(model="litellm/gemini/gemini-2.5-flash-preview-04-17", ...)
```

### Method 2: Global OpenAI Client Override
```python
from agents import set_default_openai_client
from openai import AsyncOpenAI

# For OpenAI-compatible endpoints
client = AsyncOpenAI(
    base_url="http://localhost:11434/v1",  # e.g., Ollama
    api_key="dummy"  # Some providers don't need real keys
)
set_default_openai_client(client)
```

### Method 3: Custom ModelProvider (Runner Level)
```python
from agents import ModelProvider, Runner

# Custom provider for all agents in a run
custom_provider = MyCustomModelProvider()
result = await Runner.run(
    agent,
    input="...",
    model_provider=custom_provider
)
```

### Method 4: Agent-Specific Model
```python
from agents import Agent, OpenAIChatCompletionsModel

# Mix and match different providers
agent = Agent(
    name="CustomAgent",
    model=OpenAIChatCompletionsModel(
        model="custom-model",
        openai_client=AsyncOpenAI(base_url="...")
    )
)
```

## Model Configuration

### Basic Configuration
```python
from agents import Agent, ModelSettings

agent = Agent(
    name="MyAgent",
    instructions="...",
    model="gpt-4o",  # Model name
    model_settings=ModelSettings(
        temperature=0.1,
        max_tokens=1000,
        # Other standard parameters
    )
)
```

### Advanced Configuration (Extra Args)
```python
agent = Agent(
    model="gpt-4o",
    model_settings=ModelSettings(
        temperature=0.1,
        extra_args={
            "service_tier": "flex",
            "user": "user_12345",
            # Any additional API parameters
        }
    )
)
```

## Mixing Models in a Workflow
```python
# Different models for different tasks
triage_agent = Agent(
    name="Triage",
    model="gpt-3.5-turbo",  # Fast, cheap
)

expert_agent = Agent(
    name="Expert",
    model="o3-mini",  # More capable
)

spanish_agent = Agent(
    name="Spanish",
    model=OpenAIChatCompletionsModel(
        model="custom-spanish-model",
        openai_client=custom_client
    )
)
```

## Common Issues and Solutions

### 1. Tracing Errors (401)
When using non-OpenAI providers:
```python
from agents import set_tracing_disabled, set_tracing_export_api_key

# Option 1: Disable tracing
set_tracing_disabled(True)

# Option 2: Set OpenAI key just for tracing
set_tracing_export_api_key("sk-...")

# Option 3: Use custom trace processor
```

### 2. Responses API Not Supported
Most non-OpenAI providers don't support Responses API:
```python
# Option 1: Set global default
from agents import set_default_openai_api
set_default_openai_api("chat_completions")

# Option 2: Use OpenAIChatCompletionsModel explicitly
agent = Agent(
    model=OpenAIChatCompletionsModel(...)
)
```

### 3. Structured Outputs Not Supported
Error: `'response_format.type' : value is not one of the allowed values`

Solution: Use providers that support JSON schema outputs, or handle malformed JSON gracefully.

## Feature Compatibility Matrix

| Feature | OpenAI | Anthropic (via LiteLLM) | Ollama | GPT-OSS |
|---------|--------|-------------------------|---------|---------|
| Responses API | ✅ | ❌ | ❌ | ❌ |
| Chat Completions | ✅ | ✅ | ✅ | ✅ |
| Structured Outputs | ✅ | ⚠️ | ❌ | ⚠️ |
| Multimodal | ✅ | ✅ | ⚠️ | ❌ |
| Function Calling | ✅ | ✅ | ❌ | ⚠️ |
| File/Web Search | ✅ | ❌ | ❌ | ❌ |
| Extended Context | ✅ (400K) | ✅ (200K) | ✅ (131K) | ✅ (131K) |
| Reasoning Effort | ✅ (GPT-5) | ✅ (Claude 4) | ❌ | ⚠️ |
| Local Deployment | ❌ | ❌ | ✅ | ✅ |

## Key Implementation Notes

1. **Model Shape Consistency**: Use a single model shape (Responses or Chat Completions) per workflow for feature compatibility

2. **Provider Limitations**: Be aware of feature differences:
   - Don't send unsupported tools to providers that don't understand them
   - Filter multimodal inputs for text-only models
   - Handle potential JSON parsing errors from providers without structured output support

3. **API Compatibility**: For OpenAI-compatible endpoints (like Ollama), use:
   - `OpenAIChatCompletionsModel` (not Responses)
   - Set appropriate `base_url` and dummy `api_key`

4. **Temperature Support**: Note that some models (e.g., GPT-5 family) may not support temperature parameter

## Example: Multi-Provider Setup
```python
from agents import Agent, Runner, set_tracing_disabled
from openai import AsyncOpenAI

# Disable tracing if no OpenAI key
set_tracing_disabled(True)

# OpenAI model (default)
openai_agent = Agent(
    name="OpenAI",
    model="gpt-4o"
)

# Anthropic via LiteLLM
claude_agent = Agent(
    name="Claude",
    model="litellm/anthropic/claude-3-haiku-20240307"
)

# Ollama local model
ollama_client = AsyncOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)
ollama_agent = Agent(
    name="Ollama",
    model=OpenAIChatCompletionsModel(
        model="gpt-oss:20b",
        openai_client=ollama_client
    )
)
```

## Integration with Latest Models

### GPT-5 Reasoning Models

```python
# Using GPT-5 with reasoning capabilities
reasoning_agent = Agent(
    name="Research Agent",
    model="gpt-5",  # or "gpt-5-mini" for cost optimization
    model_settings=ModelSettings(
        temperature=0.1,
        extra_args={
            "reasoning_effort": "high",  # GPT-5 specific parameter
            "max_tokens": 128000,  # Up to 128K output tokens
        }
    )
)

# For edge deployment with minimal reasoning
edge_agent = Agent(
    name="Edge Agent",
    model="gpt-5-nano",
    model_settings=ModelSettings(
        extra_args={
            "reasoning_effort": "minimal",  # Fastest, cheapest
        }
    )
)
```

### GPT-OSS Local Models

```python
# Local GPT-OSS deployment via Ollama
from openai import AsyncOpenAI

ollama_client = AsyncOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

local_agent = Agent(
    name="Local Agent",
    model=OpenAIChatCompletionsModel(
        model="gpt-oss:20b",  # Use exact Ollama model name
        openai_client=ollama_client
    ),
    model_settings=ModelSettings(
        temperature=0.2,
        max_tokens=131000,  # Full context window
    )
)
```

### Claude 4 Models

```python
# Claude 4 with extended context
claude_agent = Agent(
    name="Claude Agent",
    model="litellm/anthropic/claude-opus-4-20250514",
    model_settings=ModelSettings(
        temperature=0.1,
        max_tokens=200000,  # Claude 4's 200K context
    )
)
```