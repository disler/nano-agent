# Running GPT-OSS Locally with Ollama

Source: [OpenAI Cookbook](https://cookbook.openai.com/articles/gpt-oss/run-locally-ollama)

## Model Options

### gpt-oss:20b
- **Release Date**: August 5, 2025
- **License**: Apache 2.0
- **Smaller model** optimized for consumer hardware
- **Best with ≥16GB VRAM or unified memory**
- **Perfect for higher-end consumer GPUs or Apple Silicon Macs**
- **Context Length**: 131K tokens
- **Hardware Requirements**: 40GB VRAM (FP16), ~10GB VRAM (4-bit quantized)

### gpt-oss:120b
- **Release Date**: August 5, 2025
- **License**: Apache 2.0
- **Full-sized model** for high-performance tasks
- **Best with ≥80GB VRAM or unified memory**
- **Ideal for multi-GPU or workstation setups**
- **Context Length**: 32K tokens
- **Hardware Requirements**: 240GB VRAM (FP16), ~60GB VRAM (4-bit quantized)

**Note:** Models ship MXFP4 quantized out of the box. CPU offloading is possible but slower. Both models are now available on Amazon Bedrock and AWS SageMaker for cloud deployment.

## Latest Capabilities (August 2025)

### Enhanced Reasoning
- **Configurable Reasoning Efforts**: Adjust reasoning depth for different task complexities
- **Agentic Workflows**: Optimized for autonomous AI agents and multi-step reasoning
- **Extended Context**: 131K tokens for gpt-oss:20b, 32K for gpt-oss:120b

### Use Cases
- **On-Device AI**: Privacy-focused applications with local processing
- **Cost-Efficient Deployment**: Free open-weight models for production use
- **Extended Document Analysis**: Process large documents and codebases
- **Multi-Step Problem Solving**: Complex reasoning tasks requiring sustained attention

### Cloud Integration
- **Amazon Bedrock**: Native integration for enterprise deployment
- **AWS SageMaker**: Pre-configured endpoints and scaling
- **Hybrid Deployment**: Combine local Ollama with cloud services

## Quick Setup

1. **Install Ollama**: https://ollama.com/download
2. **Pull the model**:
```bash
# For 20B
ollama pull gpt-oss:20b

# For 120B
ollama pull gpt-oss:120b
```

## Chat Interface

```bash
ollama run gpt-oss:20b
```

## API Usage

### OpenAI SDK Compatible

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",  # Local Ollama API
    api_key="ollama"                       # Dummy key
)

response = client.chat.completions.create(
    model="gpt-oss:20b",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain what MXFP4 quantization is."}
    ]
)

print(response.choices[0].message.content)
```

## Function Calling

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather in a given city",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"]
            },
        },
    }
]

response = client.chat.completions.create(
    model="gpt-oss:20b",
    messages=[{"role": "user", "content": "What's the weather in Berlin right now?"}],
    tools=tools
)

print(response.choices[0].message)
```

**Important:** Since models perform tool calling as part of chain-of-thought, return the reasoning from the API back into subsequent calls until the model reaches a final answer.

## Responses API Workarounds

Ollama doesn't natively support the Responses API yet. Options:

1. **Hugging Face's Responses.js proxy** - Converts Chat Completions to Responses API
2. **Python server with Ollama backend**:
```bash
pip install gpt-oss
python -m gpt_oss.responses_api.serve \
    --inference_backend=ollama \
    --checkpoint gpt-oss:20b
```

## Agents SDK Integration

### Python with LiteLLM

```python
import asyncio
from agents import Agent, Runner, function_tool, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel

set_tracing_disabled(True)

@function_tool
def get_weather(city: str):
    print(f"[debug] getting weather for {city}")
    return f"The weather in {city} is sunny."

async def main():
    agent = Agent(
        name="Assistant",
        instructions="You only respond in haikus.",
        model=LitellmModel(model="ollama/gpt-oss:120b", api_key="ollama"),
        tools=[get_weather],
    )

    result = await Runner.run(agent, "What's the weather in Tokyo?")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

### TypeScript with AI SDK

Use AI SDK with the ollama adapter:
- [AI SDK Documentation](https://openai.github.io/openai-agents-js/extensions/ai-sdk/)
- [Ollama Adapter](https://ai-sdk.dev/providers/community-providers/ollama)

## Key Points

1. **Chat Template**: Ollama applies a chat template that mimics OpenAI harmony format
2. **API Compatibility**: Full Chat Completions API compatibility with OpenAI SDK
3. **Tool Calling**: Supported with chain-of-thought reasoning
4. **Local Performance**: VRAM requirements vary by model size
5. **SDK Support**: Available in Python and JavaScript/TypeScript

## Alternative SDKs

- [Ollama Python SDK](https://github.com/ollama/ollama-python)
- [Ollama JavaScript SDK](https://github.com/ollama/ollama-js)