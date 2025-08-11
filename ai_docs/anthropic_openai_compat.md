# Anthropic OpenAI SDK Compatibility

## Quick Start

```python
from openai import OpenAI

client = OpenAI(
    api_key="ANTHROPIC_API_KEY",  # Your Anthropic API key
    base_url="https://api.anthropic.com/v1/"  # Anthropic's API endpoint
)

response = client.chat.completions.create(
    model="claude-3-haiku-20240307",  # Anthropic model name
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who are you?"}
    ],
)

print(response.choices[0].message.content)
```

## Available Models
- claude-opus-4-20250514
- claude-sonnet-4-20250514
- claude-3-opus-20240229
- claude-3-sonnet-20240229
- claude-3-haiku-20240307
- claude-3-5-sonnet-20241022
- claude-3-5-haiku-20241022

## Key Differences from OpenAI
1. System messages are hoisted and concatenated at the beginning
2. `strict` parameter for function calling is ignored
3. Audio input not supported
4. Prompt caching not supported via OpenAI SDK (use native Anthropic SDK)
5. Rate limits follow Anthropic's standard limits
6. Extended context windows (200K tokens) for long-horizon tasks
7. Enhanced reasoning capabilities for complex problem-solving

## Supported Features
- ✅ Chat completions
- ✅ Streaming
- ✅ Function/tool calling (without strict mode)
- ✅ max_tokens / max_completion_tokens
- ✅ temperature (0-1)
- ✅ top_p
- ✅ stop sequences
- ✅ Image inputs

## Ignored Parameters
- logprobs
- response_format
- presence_penalty
- frequency_penalty
- seed
- audio
- modalities

## Extended Thinking Support

```python
response = client.chat.completions.create(
    model="claude-3-opus-20240229",
    messages=...,
    extra_body={
        "thinking": {"type": "enabled", "budget_tokens": 2000}
    }
)
```

## Important Notes
- This compatibility layer is for testing and comparison, not production
- For full features (PDFs, citations, prompt caching), use native Anthropic SDK
- Most unsupported fields are silently ignored rather than producing errors
- Claude 4 models (Opus and Sonnet) support extended context windows and enhanced reasoning capabilities
- For the latest model availability and features, refer to Anthropic's official API documentation

## Claude 4 Latest Capabilities (August 2025)

### Enhanced Reasoning
- **Long-Horizon Tasks**: Can execute complex, multi-step reasoning over extended periods
- **Coding Proficiency**: Optimized for software development and code analysis
- **Data Analysis**: Advanced capabilities for analyzing large datasets and complex information

### Use Cases
- **Agentic Workflows**: Configurable reasoning efforts for different complexity levels
- **Extended Context**: 200K token context windows for comprehensive document analysis
- **Complex Problem-Solving**: Multi-step reasoning for engineering and research tasks
- **Code Generation**: Advanced coding assistance with understanding of large codebases