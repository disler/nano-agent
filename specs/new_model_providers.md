# Multi-Provider Model Support for Nano Agent - Simplified Implementation

## Overview
Based on the OpenAI Agents SDK documentation, we can add support for Ollama and Anthropic models with a thin abstraction layer that leverages the SDK's built-in capabilities.

## Current State
- Uses OpenAI Agent SDK with `OpenAIResponsesModel` (default)
- Only supports OpenAI provider
- Tools use `@function_tool` decorator

## Target Implementation

### Supported Providers and Models

#### Ollama (Local Models via OpenAI-compatible API)
- `gpt-oss:20b`
- `gpt-oss:120b`

#### Anthropic (Via LiteLLM)
- `claude-opus-4-1-20250805`
- `claude-opus-4-20250514`
- `claude-sonnet-4-20250514`
- `claude-3-haiku-20240307`

## Implementation Strategy

### Option 1: LiteLLM Integration (Recommended for Anthropic)
```python
# Install: pip install "openai-agents[litellm]"

# Then simply use:
agent = Agent(
    model="litellm/anthropic/claude-opus-4-1-20250805",
    ...
)
```

### Option 2: OpenAI-Compatible Endpoints (Recommended for Ollama)
```python
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel

ollama_client = AsyncOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # Dummy key
)

agent = Agent(
    model=OpenAIChatCompletionsModel(
        model="gpt-oss:20b",
        openai_client=ollama_client
    )
)
```

## Simplified Architecture

### 1. Provider Configuration Module
Create `modules/provider_config.py`:

```python
from typing import Optional, Union
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, ModelSettings
import os

class ProviderConfig:
    """Configuration for different model providers."""
    
    @staticmethod
    def create_agent(
        name: str,
        instructions: str,
        tools: list,
        model: str,
        provider: str,
        model_settings: Optional[ModelSettings] = None
    ) -> Agent:
        """Create an agent with the appropriate provider configuration."""
        
        if provider == "openai":
            # Default OpenAI configuration
            return Agent(
                name=name,
                instructions=instructions,
                tools=tools,
                model=model,
                model_settings=model_settings
            )
        
        elif provider == "anthropic":
            # Use LiteLLM for Anthropic
            return Agent(
                name=name,
                instructions=instructions,
                tools=tools,
                model=f"litellm/anthropic/{model}",
                model_settings=model_settings
            )
        
        elif provider == "ollama":
            # Use OpenAI-compatible endpoint for Ollama
            ollama_client = AsyncOpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama"
            )
            return Agent(
                name=name,
                instructions=instructions,
                tools=tools,
                model=OpenAIChatCompletionsModel(
                    model=model,
                    openai_client=ollama_client
                ),
                model_settings=model_settings
            )
        
        else:
            raise ValueError(f"Unsupported provider: {provider}")
```

### 2. Update nano_agent.py

Minimal changes to `_execute_nano_agent`:

```python
from .provider_config import ProviderConfig

def _execute_nano_agent(request: PromptNanoAgentRequest, enable_rich_logging: bool = True) -> PromptNanoAgentResponse:
    # ... existing validation ...
    
    # Create agent with provider-specific configuration
    agent = ProviderConfig.create_agent(
        name="NanoAgent",
        instructions=NANO_AGENT_SYSTEM_PROMPT,
        tools=get_nano_agent_tools(),
        model=request.model,
        provider=request.provider,
        model_settings=ModelSettings(
            max_tokens=MAX_TOKENS,
            temperature=DEFAULT_TEMPERATURE if not request.model.startswith("gpt-5") else None
        )
    )
    
    # Handle tracing for non-OpenAI providers
    if request.provider != "openai":
        from agents import set_tracing_disabled
        set_tracing_disabled(True)  # Or use a trace key if available
    
    # Rest of the code remains the same...
```

### 3. Update Constants

```python
# constants.py
AVAILABLE_MODELS = {
    "openai": [
        "gpt-5",
        "gpt-5-mini",
        "gpt-5-nano",
        "gpt-4o",
        "gpt-3.5-turbo"
    ],
    "anthropic": [
        "claude-opus-4-1-20250805",
        "claude-opus-4-20250514",
        "claude-sonnet-4-20250514",
        "claude-3-haiku-20240307"
    ],
    "ollama": [
        "gpt-oss:20b",
        "gpt-oss:120b"
    ],
    "lmstudio": [
        "qwen/qwen3-coder-30b"
    ]
}

PROVIDER_REQUIREMENTS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "lmstudio": None, 
    "ollama": None  # No API key needed

}
```

### 4. Validation and Error Handling

```python
def validate_provider_setup(provider: str, model: str) -> tuple[bool, Optional[str]]:
    """Validate that provider is properly configured."""
    
    # Check model availability
    if provider not in AVAILABLE_MODELS:
        return False, f"Unknown provider: {provider}"
    
    if model not in AVAILABLE_MODELS[provider]:
        return False, f"Model {model} not available for {provider}"
    
    # Check API keys
    required_key = PROVIDER_REQUIREMENTS.get(provider)
    if required_key and not os.getenv(required_key):
        return False, f"Missing environment variable: {required_key}"
    
    # Check Ollama availability
    if provider == "ollama":
        import requests
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=1)
            models = [m["name"] for m in response.json().get("models", [])]
            if model not in models:
                return False, f"Model {model} not pulled in Ollama. Run: ollama pull {model}"
        except:
            return False, "Ollama service not running. Start with: ollama serve"
    
    return True, None
```

## Tool Compatibility

The existing tools will work with all providers since they return strings:
- `read_file_raw()`
- `write_file_raw()`
- `list_directory_raw()`
- `get_file_info_raw()`

The `@function_tool` decorator will be handled by the Agent SDK appropriately for each provider.

## Installation Requirements

Update `requirements.txt`:
```
openai-agents>=0.2.5
openai>=1.0.0
anthropic>=0.21.0  # For direct Anthropic usage if needed
openai-agents[litellm]  # For LiteLLM support
```

## Usage Examples

### Via MCP Server (unchanged interface)
```python
# OpenAI (default)
await prompt_nano_agent(
    agentic_prompt="Create a Python function",
    model="gpt-5-mini",
    provider="openai"
)

# Anthropic
await prompt_nano_agent(
    agentic_prompt="Analyze this code",
    model="claude-opus-4-1-20250805",
    provider="anthropic"
)

# Ollama
await prompt_nano_agent(
    agentic_prompt="Generate documentation",
    model="gpt-oss:20b",
    provider="ollama"
)
```

## Implementation Steps

1. **Install Dependencies**
   ```bash
   pip install "openai-agents[litellm]"
   ```

2. **Create provider_config.py**
   - Simple factory for creating configured agents
   - Handle provider-specific setup

3. **Update nano_agent.py**
   - Replace direct Agent creation with ProviderConfig.create_agent()
   - Add tracing control for non-OpenAI providers

4. **Update constants.py**
   - Add model lists for each provider
   - Add validation requirements

5. **Test Each Provider**
   - Verify OpenAI still works (no regression)
   - Test Anthropic via LiteLLM
   - Test Ollama with local models

## Known Limitations

Based on the SDK documentation:

| Feature | OpenAI | Anthropic | Ollama |
|---------|--------|-----------|---------|
| Tool Calling | ✅ Native | ✅ Via LiteLLM | ⚠️ May need prompt engineering |
| Structured Output | ✅ | ⚠️ Limited | ❌ |
| Token Tracking | ✅ | ✅ | ✅ |
| Rich Logging | ✅ | ✅ | ✅ |

## Error Messages

Provide clear error messages for common issues:
- "Ollama service not running. Start with: `ollama serve`"
- "Model not available in Ollama. Pull with: `ollama pull gpt-oss:20b`"
- "Missing ANTHROPIC_API_KEY environment variable"
- "Provider 'anthropic' requires litellm. Install with: `pip install openai-agents[litellm]`"

## Success Criteria

1. ✅ All three providers work through `prompt_nano_agent`
2. ✅ Tools execute correctly for all providers
3. ✅ Token tracking works for all providers
4. ✅ Rich logging displays correctly
5. ✅ Clear error messages for configuration issues
6. ✅ No regression in OpenAI functionality
7. ✅ Minimal code changes (thin abstraction layer)