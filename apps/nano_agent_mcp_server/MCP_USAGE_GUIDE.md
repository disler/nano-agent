# Nano Agent MCP Server - Complete Usage Guide

The enhanced Nano Agent MCP server provides powerful autonomous AI agents with fine-grained control, session persistence, and security features.

## 🚀 Quick Start

### Basic Usage
```python
# Simple agent execution
result = await prompt_nano_agent(
    "Create a Python function to calculate fibonacci numbers"
)
```

### With Configuration
```python
# Agent with specific model and safety settings  
result = await prompt_nano_agent(
    "Analyze the security of this codebase",
    model="gpt-5",
    temperature=0.2,
    read_only=True,
    allowed_paths=["./src"]
)
```

### Session-Based Conversation
```python
# First call - creates session
result1 = await prompt_nano_agent(
    "Create a TODO app in Python",
    session_id="my-project-session"
)

# Follow-up call - continues conversation
result2 = await prompt_nano_agent(
    "Add user authentication to the app",
    session_id="my-project-session"
)
```

## 📋 Available Tools

### 1. prompt_nano_agent
**Main agent execution tool with full configuration options**

#### Parameters

**Model Configuration:**
- `model` (str): Model to use (default: "gpt-5-mini")
- `provider` (str): Provider ("openai", "anthropic", "ollama")
- `temperature` (float): Model creativity (0.0-2.0)
- `max_tokens` (int): Maximum response tokens

**Security & Permissions:**
- `allowed_tools` (List[str]): Whitelist of tools agent can use
- `blocked_tools` (List[str]): Blacklist of prohibited tools
- `allowed_paths` (List[str]): Whitelist of accessible paths
- `blocked_paths` (List[str]): Blacklist of protected paths
- `read_only` (bool): Disable all write operations

**Session Management:**
- `session_id` (str): Continue specific session
- `clear_history` (bool): Clear session conversation history

#### Response Format
```json
{
  "success": true,
  "result": "Agent response here",
  "metadata": {
    "model": "gpt-5-mini",
    "provider": "openai",
    "token_usage": {...},
    "execution_time_seconds": 15.2,
    "permissions_used": {...}
  },
  "session_info": {
    "session_id": "session_123",
    "message_count": 4,
    "client_id": "claude-desktop"
  }
}
```

### 2. get_session_info
**Get detailed information about a session**

```python
result = await get_session_info("my-session-id")
```

### 3. list_sessions
**List all sessions for the current client**

```python
sessions = await list_sessions(limit=10)
```

### 4. clear_old_sessions
**Clean up old session data**

```python
result = await clear_old_sessions(days=30)
```

### 5. get_available_models
**List all available models and providers**

```python
models = await get_available_models()
```

### 6. get_server_capabilities
**Get server features and limitations**

```python
capabilities = await get_server_capabilities()
```

## 🛡️ Security Features

### Read-Only Mode
Perfect for safe code exploration and analysis:

```python
result = await prompt_nano_agent(
    "Analyze the architecture of this project",
    read_only=True
)
```

### Tool Restrictions
Control exactly what the agent can do:

```python
# Analysis only
result = await prompt_nano_agent(
    "Review the code quality",
    allowed_tools=["read_file", "list_directory", "get_file_info"]
)

# Block dangerous tools
result = await prompt_nano_agent(
    "Help with development",
    blocked_tools=["edit_file"]  # Allow reads and writes but not edits
)
```

### Path Restrictions
Limit file system access:

```python
# Restrict to specific directories
result = await prompt_nano_agent(
    "Work on the authentication module",
    allowed_paths=["./src/auth", "./tests/auth"]
)

# Protect sensitive areas
result = await prompt_nano_agent(
    "Refactor the codebase",
    blocked_paths=["/etc", "~/.ssh", "./secrets", ".env"]
)
```

### Combined Security
```python
# Maximum security for code review
result = await prompt_nano_agent(
    "Perform a security audit",
    read_only=True,
    allowed_tools=["read_file", "list_directory"],
    allowed_paths=["./src"],
    blocked_paths=["./src/secrets"],
    temperature=0.1  # Low creativity for consistent analysis
)
```

## 💬 Session Management

### Session Persistence
Sessions automatically save:
- Conversation history
- Model and provider settings
- Permission settings
- Usage statistics

```python
# Create or continue session
result = await prompt_nano_agent(
    "Start working on user management",
    session_id="user-mgmt-project",
    model="gpt-5",
    provider="openai",
    temperature=0.7
)

# Settings are remembered for future calls
result = await prompt_nano_agent(
    "Add password hashing",
    session_id="user-mgmt-project"  # Uses saved settings
)
```

### Session Information
```python
# Get session details
info = await get_session_info("user-mgmt-project")
# Returns: session_id, created_at, message_count, total_tokens, etc.

# List all sessions
sessions = await list_sessions(limit=5)
# Returns array of session summaries
```

### Session Cleanup
```python
# Clean up old sessions
result = await clear_old_sessions(days=7)  # Keep last 7 days
```

## 🎯 Use Cases

### 1. Safe Code Exploration
```python
# Explore unknown codebase safely
result = await prompt_nano_agent(
    "Analyze this project structure and explain what it does",
    read_only=True,
    temperature=0.2
)
```

### 2. Restricted Development
```python
# Work on specific feature with limits
result = await prompt_nano_agent(
    "Implement user registration functionality",
    allowed_paths=["./src/auth", "./tests/auth"],
    allowed_tools=["read_file", "write_file", "edit_file"],
    blocked_paths=["./src/auth/secrets"]
)
```

### 3. Iterative Development
```python
# Start a development session
session_id = "feature-xyz"

# Initial implementation
await prompt_nano_agent(
    "Create a basic REST API for user management",
    session_id=session_id,
    allowed_paths=["./src/api"]
)

# Add features iteratively
await prompt_nano_agent(
    "Add authentication middleware",
    session_id=session_id
)

await prompt_nano_agent(
    "Add input validation",
    session_id=session_id
)

await prompt_nano_agent(
    "Add unit tests",
    session_id=session_id,
    allowed_paths=["./src/api", "./tests"]
)
```

### 4. Different Permission Levels
```python
# Junior developer - restricted access
await prompt_nano_agent(
    "Help implement the todo list feature",
    allowed_paths=["./src/features/todo"],
    blocked_tools=["edit_file"],  # Only allow create new files
    max_tokens=2000
)

# Senior developer - full access
await prompt_nano_agent(
    "Refactor the entire authentication system",
    allowed_paths=["./src"],
    blocked_paths=["./src/config/secrets"],
    temperature=0.3
)

# Code reviewer - read only
await prompt_nano_agent(
    "Review this pull request for security issues",
    read_only=True,
    allowed_paths=["./src"],
    temperature=0.1
)
```

## 🔧 Configuration Examples

### Claude Desktop Configuration
```json
{
  "mcpServers": {
    "nano-agent": {
      "command": "uv",
      "args": ["run", "nano-agent"],
      "cwd": "/path/to/nano-agent"
    }
  }
}
```

### VS Code Configuration
Example of how VS Code extension might use the server:

```python
# Development session with local model
result = await prompt_nano_agent(
    "Fix the bug in authentication.py",
    model="gpt-oss:20b",
    provider="ollama",
    session_id=workspace_session_id,
    allowed_paths=[workspace_root],
    temperature=0.2
)
```

## 📊 Response Metadata

Every response includes detailed metadata:

```json
{
  "success": true,
  "result": "Implementation completed...",
  "metadata": {
    "model": "gpt-5-mini",
    "provider": "openai",
    "timestamp": "2025-01-30T12:00:00",
    "execution_time_seconds": 25.4,
    "token_usage": {
      "total_tokens": 4521,
      "input_tokens": 1200,
      "output_tokens": 3321,
      "total_cost": "$0.0045"
    },
    "permissions_used": {
      "allowed_tools": ["read_file", "write_file"],
      "blocked_paths": ["/etc", "~/.ssh"],
      "read_only": false
    }
  },
  "session_info": {
    "session_id": "dev-session-123",
    "message_count": 8,
    "client_id": "vscode-extension"
  }
}
```

## 🚨 Error Handling

### Permission Denied
```json
{
  "success": false,
  "error": "Tool execution blocked: write_file not in allowed tools",
  "metadata": {
    "error_type": "PermissionError",
    "blocked_operation": "write_file",
    "allowed_tools": ["read_file", "list_directory"]
  }
}
```

### Path Restrictions
```json
{
  "success": false,
  "error": "Path access denied: '/etc/passwd' matches blocked pattern '/etc'",
  "metadata": {
    "error_type": "PathAccessError",
    "requested_path": "/etc/passwd",
    "blocked_patterns": ["/etc", "~/.ssh"]
  }
}
```

## 🔍 Debugging

### Check Available Models
```python
models = await get_available_models()
print(f"Available: {models['total_models']} models")
```

### Check Server Capabilities
```python
caps = await get_server_capabilities()
print(f"Features: {caps['capabilities']['features']}")
print(f"Limits: {caps['capabilities']['limits']}")
```

### Session Debugging
```python
# Check session status
info = await get_session_info("my-session")
print(f"Messages: {info['message_count']}")
print(f"Tokens used: {info['total_tokens']}")
print(f"Cost: ${info['total_cost']}")
```

## 🏷️ Best Practices

### 1. Security First
- Always use `read_only=True` for exploration
- Restrict paths to necessary directories only
- Use `blocked_paths` for sensitive areas
- Limit tools based on use case

### 2. Efficient Token Usage
- Set appropriate `max_tokens` limits
- Use lower `temperature` for consistent results
- Clear session history when starting new topics

### 3. Session Management
- Use meaningful session IDs
- Clean up old sessions regularly
- Monitor token usage across sessions

### 4. Error Handling
- Check response `success` field
- Handle permission errors gracefully
- Provide fallback options for blocked operations

## 🔮 Future Features

Coming soon:
- Streaming responses for real-time feedback
- Batch operations for multiple prompts
- Resource quotas and rate limiting
- Custom system prompts
- Client-specific default configurations
- Webhook notifications for long-running tasks

The enhanced MCP server provides enterprise-grade security and flexibility while maintaining ease of use for simple tasks!