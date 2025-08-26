# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Nano Agent** is an MCP (Model Context Protocol) server that provides autonomous engineering agents with multi-provider LLM support. It creates a nested agent hierarchy where Claude Code (or any MCP client) can delegate work to internal OpenAI-SDK-based agents that have file system tools.

## Development Commands

### Setup & Installation
```bash
# Setup environment
cd apps/nano_agent_mcp_server
cp .env.sample .env  # Add API keys
uv sync --extra test  # Install with test dependencies

# Global installation for Claude Code
./scripts/install.sh
uv tool install -e .
```

### Testing
```bash
# Run all tests (requires API keys)
cd apps/nano_agent_mcp_server
uv run pytest tests/ -v

# Test specific module
uv run pytest tests/nano_agent/modules/test_nano_agent.py -v

# Quick validation without API
uv run nano-cli test-tools

# Test with different providers
uv run nano-cli run "test prompt" --model gpt-5-mini
uv run nano-cli run "test prompt" --model claude-3-haiku-20240307 --provider anthropic
uv run nano-cli run "test prompt" --model gpt-oss:20b --provider ollama
```

### Development Workflow
```bash
# Run CLI directly for testing
cd apps/nano_agent_mcp_server
uv run nano-cli run "Your prompt here" --verbose

# Use command files (NEW)
uv run nano-cli run '/summarize "content to summarize"'
uv run nano-cli commands list
uv run nano-cli commands create new-command

# MCP server (for Claude Code integration)
uv run nano-agent
```

## Architecture

### Nested Agent System
- **Outer Agent** (Claude Code): Communicates via MCP protocol, sees only `prompt_nano_agent` tool
- **MCP Server** (`apps/nano_agent_mcp_server`): Receives prompts, spawns internal agents
- **Inner Agent** (OpenAI SDK): Created per request with file system tools (read_file, write_file, list_directory, get_file_info, edit_file)

### Multi-Provider Support
All providers use OpenAI SDK with compatible endpoints:
- **OpenAI**: GPT-5 models (nano, mini, standard) via native API
- **Anthropic**: Claude models via OpenAI-compatible endpoint
- **Ollama**: Local models via OpenAI-compatible API

### Key Modules
- `modules/nano_agent.py`: Core agent execution logic using OpenAI Agent SDK
- `modules/nano_agent_tools.py`: File system tool implementations
- `modules/provider_config.py`: Multi-provider configuration and client setup
- `modules/token_tracking.py`: Token usage and cost tracking
- `modules/constants.py`: Model configurations and defaults
- `modules/command_loader.py`: Command file loading system (NEW)

### Performance Evaluation System
HOP/LOP pattern for parallel model testing:
- **HOP** (`.claude/commands/perf/hop_evaluate_nano_agents.md`): Orchestrator for parallel evaluation
- **LOP** (`.claude/commands/perf/lop_eval_*.md`): Individual test definitions
- **Sub-agents** (`.claude/agents/nano-agent-*.md`): Model-specific agent configurations

### Claude Code Integration
- Sub-agents in `.claude/agents/` directory for different models
- Performance evaluation commands in `.claude/commands/perf/`
- Hook scripts in `.claude/hooks/` for development workflow

## Environment Variables

Required in `.env` files:
- `OPENAI_API_KEY`: For GPT-5 models
- `ANTHROPIC_API_KEY`: For Claude models (optional)
- `OLLAMA_API_URL`: Defaults to http://localhost:11434 (optional)

## Important Patterns

### Adding New Models
1. Update `modules/constants.py` with model definition
2. Configure provider in `modules/provider_config.py`
3. Create sub-agent in `.claude/agents/` if needed
4. Test with `uv run nano-cli run "test" --model <model> --provider <provider>`

### Tool Development
Tools are in `modules/nano_agent_tools.py` with:
- Raw functions (e.g., `read_file_raw`) for internal use
- Wrapped versions for OpenAI Agent SDK
- Standard response format: `{"success": bool, "message": str, "data": Any}`

### Error Handling
- Provider validation in `validate_model_provider_combination()`
- Graceful API key checking with clear error messages
- Token tracking with cost estimation per provider/model

## Current Limitations
- OpenAI Agent SDK has compatibility issues with openai>=1.99.2 (handled via typing_fix.py)
- GPT-5 models only support temperature=1
- Maximum 20 agent turns per execution
- Tools operate in the directory where commands are run