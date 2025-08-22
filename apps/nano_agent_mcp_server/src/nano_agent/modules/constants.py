"""
Central constants and configuration for the Nano Agent.

This module contains all shared constants, default values, and configuration
used across the nano agent codebase.
"""

# Default Model Configuration
DEFAULT_MODEL = "gpt-5-mini"  # Efficient, fast, good for most tasks
DEFAULT_PROVIDER = "openai"

# Available Models by Provider
AVAILABLE_MODELS = {
    "openai": ["gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-4o"],
    "anthropic": [
        "claude-opus-4-1-20250805",
        "claude-opus-4-20250514",
        "claude-sonnet-4-20250514",
        "claude-3-haiku-20240307",
    ],
    "ollama": ["gpt-oss:20b", "gpt-oss:120b"],
    "lmstudio": ["qwen/qwen3-coder-30b", "openai/gpt-oss-20b"],
}

# Model Display Names and Descriptions
MODEL_INFO = {
    "gpt-5-nano": "GPT-5 Nano - Fastest, best for simple tasks",
    "gpt-5-mini": "GPT-5 Mini - Efficient, fast, good for most tasks",
    "gpt-5": "GPT-5 - Most powerful, best for complex reasoning",
    "gpt-4o": "GPT-4o - Previous generation, proven reliability",
    "claude-opus-4-1-20250805": "Claude Opus 4.1 - Latest Anthropic flagship",
    "claude-opus-4-20250514": "Claude Opus 4 - Powerful reasoning",
    "claude-sonnet-4-20250514": "Claude Sonnet 4 - Balanced performance",
    "claude-3-haiku-20240307": "Claude 3 Haiku - Fast and efficient",
    "gpt-oss:20b": "GPT-OSS 20B - Local open-source model",
    "gpt-oss:120b": "GPT-OSS 120B - Large local model",
    "qwen/qwen3-coder-30b": "Qwen3 Coder 30B - Local model",
}

# Provider API Key Requirements
PROVIDER_REQUIREMENTS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "ollama": None,  # No API key needed
    "lmstudio": None,  # No API key needed
}

# Agent Configuration
MAX_AGENT_TURNS = 20  # Maximum turns in agent loop
DEFAULT_TEMPERATURE = 0.2  # Temperature for agent responses
MAX_TOKENS = 4000  # Maximum tokens per response

# Tool Names
TOOL_READ_FILE = "read_file"
TOOL_LIST_DIRECTORY = "list_directory"
TOOL_WRITE_FILE = "write_file"
TOOL_GET_FILE_INFO = "get_file_info"
TOOL_EDIT_FILE = "edit_file"

# Available Tools List
AVAILABLE_TOOLS = [
    TOOL_READ_FILE,
    TOOL_LIST_DIRECTORY,
    TOOL_WRITE_FILE,
    TOOL_GET_FILE_INFO,
    TOOL_EDIT_FILE,
]

# Demo Configuration
DEMO_PROMPTS = [
    ("List all files in the current directory", DEFAULT_MODEL),
    (
        "Create a file called demo.txt with the content 'Hello from Nano Agent!'",
        DEFAULT_MODEL,
    ),
    ("Read the file demo.txt and tell me what it says", DEFAULT_MODEL),
]

# System Prompts
NANO_AGENT_SYSTEM_PROMPT = """You are a helpful autonomous agent that can perform file operations.

Your capabilities:
1. Read files to understand their contents
2. List directories to explore project structure
3. Write files to create or modify content
4. Get detailed file information

When given a task:
1. First understand what needs to be done
2. Explore the relevant files and directories
3. Complete the task step by step
4. Verify your work

Be thorough but concise. Always verify files exist before trying to read them.
When writing files, ensure the content is correct before saving.

If asked about general information, respond and do not use any tools.
"""

# Error Messages
ERROR_NO_API_KEY = "{} environment variable is not set"
ERROR_PROVIDER_NOT_SUPPORTED = (
    "Provider '{}' not supported. Available providers: openai, anthropic, ollama"
)
ERROR_FILE_NOT_FOUND = "Error: File not found: {}"
ERROR_NOT_A_FILE = "Error: Path is not a file: {}"
ERROR_DIR_NOT_FOUND = "Error: Directory not found: {}"
ERROR_NOT_A_DIR = "Error: Path is not a directory: {}"

# Success Messages
SUCCESS_FILE_WRITE = "Successfully wrote {} bytes to {}"
SUCCESS_FILE_EDIT = "updated"
SUCCESS_AGENT_COMPLETE = "Agent completed successfully in {:.2f}s"

# Version Info
VERSION = "1.0.0"
