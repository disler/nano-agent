# Product Mission

## Pitch

Nano Agent is a multi-provider LLM benchmarking platform that helps AI engineers and developers evaluate agentic capabilities across cloud and local models by providing standardized testing environments and cost/performance/speed trade-off analysis using the OpenAI Agent SDK.

## Users

### Primary Customers

- **Software Engineers**: Developers evaluating LLM integration options for their applications
- **Autonomous Agent Developers**: Engineers building sophisticated agent systems requiring optimal model selection

### User Personas

**AI Integration Engineer** (25-45 years old)
- **Role:** Senior Software Engineer or AI/ML Engineer
- **Context:** Building production applications that leverage LLM capabilities for autonomous task execution
- **Pain Points:** Difficult to compare model performance fairly, expensive trial-and-error with different providers, lack of standardized evaluation metrics for agentic tasks
- **Goals:** Select optimal models for specific use cases, minimize costs while maintaining performance, build reliable autonomous systems

**Research Developer** (22-40 years old)
- **Role:** AI Researcher or Developer Advocate
- **Context:** Investigating LLM capabilities and contributing to AI development frameworks
- **Pain Points:** Inconsistent evaluation environments across providers, limited access to fair model comparisons, difficulty understanding trade-offs between different model architectures
- **Goals:** Conduct rigorous model evaluations, contribute to open AI research, educate community on model capabilities

## The Problem

### Inconsistent Model Evaluation

Current LLM evaluation tools provide inconsistent results because they use different SDKs, APIs, and execution environments for each provider. This makes it impossible to fairly compare model performance, leading to suboptimal technology choices costing organizations thousands in inefficient model usage.

**Our Solution:** Nano Agent uses the OpenAI Agent SDK for ALL providers, creating a true apples-to-apples comparison environment.

### Expensive Trial-and-Error Process

Organizations spend excessive resources testing different models across providers without systematic evaluation frameworks. A single enterprise can waste $50K-100K annually on suboptimal model selections due to lack of proper benchmarking.

**Our Solution:** Systematic evaluation framework with HOP/LOP pattern enables parallel testing of 9+ models simultaneously with comprehensive cost analysis.

### Limited Local Model Integration

Most evaluation platforms focus exclusively on cloud providers, ignoring increasingly capable local models that can dramatically reduce costs and improve privacy.

**Our Solution:** Native support for Ollama and LMStudio local models alongside cloud providers, enabling hybrid deployment strategies.

### Lack of Agentic-Specific Evaluation

Traditional benchmarks focus on single-prompt performance rather than multi-turn agentic capabilities that involve tool usage, reasoning chains, and autonomous task completion.

**Our Solution:** Evaluation framework specifically designed for agentic capabilities with file system operations, multi-turn conversations, and autonomous task completion scenarios.

## Differentiators

### Unified Execution Environment

Unlike existing evaluation platforms that use different SDKs for each provider, Nano Agent uses the OpenAI Agent SDK for all models (GPT-5, Claude, local models). This eliminates implementation bias and provides true performance comparisons, resulting in 95% more reliable benchmarking results.

### Local-First Architecture

Unlike cloud-only evaluation platforms, Nano Agent provides first-class support for local models through Ollama and LMStudio integration. This enables cost-effective evaluation of models like GPT-OSS 20B/120B running on-device, potentially reducing inference costs to $0 while maintaining competitive performance.

### MCP Protocol Integration

Unlike monolithic evaluation tools, Nano Agent integrates natively with the Model Context Protocol (MCP), enabling easy client connectivity and seamless integration with Claude Code, VS Code, and other AI development environments. This results in 10x faster integration into existing development workflows.

## Key Features

### Core Features

- **Multi-Provider Support:** Seamless switching between OpenAI (GPT-5, GPT-5-mini, GPT-5-nano), Anthropic (Claude Opus 4.1, Sonnet 4, Haiku), Ollama (GPT-OSS 20B/120B), and LMStudio with unified interface
- **Nested Agent Architecture:** MCP client → nano-agent MCP server → internal OpenAI Agent SDK execution for maximum compatibility and standardization
- **File System Tool Integration:** Five core tools (read_file, write_file, edit_file, list_directory, get_file_info) for realistic autonomous task evaluation
- **Token Tracking & Cost Analysis:** Real-time tracking with detailed cost breakdowns across providers, including $0 cost tracking for local models
- **CLI Interface:** nano-cli command with test-tools validation, verbose mode, and comprehensive model/provider selection

### Testing & Analysis Features

- **HOP/LOP Evaluation Pattern:** `/perf:hop_evaluate_nano_agents` command orchestrates systematic parallel testing using Lower Order Prompt test specifications
- **Performance Benchmarking:** Automated performance/speed/cost analysis with results like "GPT-5 Nano/Mini often outperform larger models when factoring in speed and cost"
- **Real-time Model Comparison:** Color-coded parallel execution of 9 pre-configured agents (green: GPT-5 series, blue: GPT-OSS, purple: Claude Opus, orange: Claude Sonnet/Haiku)
- **Agentic Task Evaluation:** Five evaluation levels from dummy tests to complex engineering tasks with reproducible benchmarks

### Integration Features

- **MCP Server Architecture:** FastMCP-based server exposing single `prompt_nano_agent` tool with multi-provider model support
- **Claude Code Integration:** Pre-configured sub-agents (@agent-nano-agent-gpt-5-mini, @agent-nano-agent-claude-opus-4-1, etc.) with color-coded organization
- **Multiple Usage Patterns:** CLI (`uv run nano-cli run`), MCP server (`.mcp.json`), and Claude Code sub-agent delegation