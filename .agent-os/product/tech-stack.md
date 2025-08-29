# Technical Stack

## Core Application Framework
- **Language:** Python 3.12+ (required for proper typing support)
- **Package Management:** UV (Astral package manager) with dependency groups
- **Application Framework:** FastMCP v1.12.4+ (Model Context Protocol Server)

## AI & LLM Integration
- **Primary SDK:** OpenAI SDK v1.0.0+ (with typing_fix.py for compatibility)
- **Agent Framework:** OpenAI Agents SDK v0.1.0+ (experimental autonomous agents)
- **Provider Support:** 
  - OpenAI (gpt-5, gpt-5-mini, gpt-5-nano, gpt-4o)
  - Anthropic (claude-opus-4-1-20250805, claude-opus-4-20250514, claude-sonnet-4-20250514, claude-3-haiku-20240307)
  - Ollama (gpt-oss:20b, gpt-oss:120b via http://localhost:11434/v1)
  - LMStudio (qwen/qwen3-coder-30b, openai/gpt-oss-20b via http://localhost:1234/v1)

## CLI & User Interface
- **CLI Framework:** Typer v0.9.0+
- **Console Interface:** Rich v13.0.0+ (formatting, progress bars, tables)
- **Configuration:** python-dotenv v1.0.0+ for environment management

## Testing & Development
- **Testing Framework:** Pytest with pytest-asyncio v0.23.0+
- **Development Tools:** UV build system, type checking with Python 3.12+ typing
- **Integration Testing:** Real API calls with rate limiting and error handling

## Communication & Protocols
- **MCP Protocol:** Native Model Context Protocol implementation for client connectivity
- **HTTP Client:** Requests v2.28.0+ for provider API communication
- **Inter-process Communication:** stdin/stdout for MCP protocol compliance

## Local Development Environment
- **Local AI Server:** Ollama (http://localhost:11434/v1)
- **Alternative Local Server:** LMStudio compatibility
- **Development IDE Integration:** Claude Code, VS Code MCP support

## Architecture Patterns
- **Nested Agent Architecture:** MCP Client → nano-agent MCP Server → OpenAI Agent SDK → Tool Functions (max 20 turns)
- **Multi-Provider Abstraction:** ProviderConfig class with unified OpenAI SDK interface for all providers
- **Tool Function System:** Five core tools (read_file, write_file, edit_file, list_directory, get_file_info)
- **Evaluation Framework:** HOP/LOP pattern with 9 pre-configured Claude Code sub-agents for parallel testing

## Configuration & Deployment
- **Environment Management:** Dual .env files (root + apps/nano_agent_mcp_server/.env) for API keys
- **Global Installation:** `./scripts/install.sh` and `uv tool install -e .` for system-wide MCP server access
- **MCP Client Configuration:** .mcp.json with "nano-agent" command or uv directory-based execution
- **Entry Points:** nano-agent (MCP server) and nano-cli (CLI interface)

## Code Repository
- **Repository:** https://github.com/disler/nano-agent
- **Hosting:** GitHub with MIT license
- **Documentation:** Markdown-based with embedded GIFs and images

## Database & Storage
- **File System:** Direct file system operations (no external database)
- **Logging:** JSON-based structured logging for session tracking
- **Token Tracking:** In-memory cost and usage tracking per request

## Performance & Monitoring
- **Concurrency:** Async/await patterns with pytest-asyncio
- **Error Handling:** Comprehensive error handling with graceful degradation
- **Performance Metrics:** Token usage, response time, and cost tracking across providers

## Import Strategy
- **Type Compatibility:** Custom typing fixes for OpenAI SDK compatibility
- **Dependency Management:** UV lock files for reproducible builds
- **Optional Dependencies:** Test-only dependencies separated from production requirements