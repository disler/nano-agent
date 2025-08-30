# Nano Agent Hooks System

The nano-agent hooks system allows users to customize and extend the behavior of nano-cli and nano-agent (MCP server) by running custom scripts at specific points during execution.

## Overview

Hooks are external scripts that are triggered by specific events during agent execution. They can:
- Validate and filter prompts before execution
- Monitor tool usage and performance
- Enforce security policies
- Log and audit agent activities
- Block or modify operations based on custom rules

## Quick Start

1. **Install example hooks:**
   ```bash
   cd apps/nano_agent_mcp_server
   ./examples/setup_hooks.sh
   ```

2. **Test hooks:**
   ```bash
   nano-cli run "Create a test file"
   # Check logs
   tail -f ~/.nano-cli/logs/*.log
   ```

## Configuration

Hooks are configured in `~/.nano-cli/hooks.json`:

```json
{
  "version": "1.0",
  "enabled": true,
  "timeout_seconds": 5,
  "parallel_execution": true,
  "hooks": {
    "event_name": [
      {
        "name": "hook_name",
        "command": "path/to/script.sh",
        "blocking": true,
        "timeout": 2,
        "enabled": true,
        "contexts": ["cli", "mcp"],
        "matcher": {
          "tool": ["write_file", "edit_file"]
        }
      }
    ]
  }
}
```

## Hook Events

### Agent Lifecycle Events

- **`pre_agent_start`**: Before agent initialization
- **`post_agent_complete`**: After agent completes successfully
- **`agent_error`**: When agent encounters an error

### Tool Execution Events

- **`pre_tool_use`**: Before any tool execution
- **`post_tool_use`**: After successful tool execution
- **`tool_error`**: When tool execution fails

### Prompt Events

- **`user_prompt_submit`**: Before processing user prompt
- **`agent_response`**: After agent generates response

### MCP-Specific Events

- **`mcp_request_received`**: When MCP request arrives
- **`mcp_response_ready`**: Before sending MCP response

### Session Events (CLI only)

- **`session_start`**: When session begins/resumes
- **`session_end`**: When session terminates
- **`session_save`**: Before saving session

## Hook Script Interface

### Input (via stdin)

Hooks receive a JSON object with event data:

```json
{
  "event": "pre_tool_use",
  "timestamp": "2025-01-30T12:00:00",
  "context": "cli",
  "working_dir": "/current/dir",
  "tool_name": "write_file",
  "tool_args": {
    "file_path": "test.txt",
    "content": "Hello"
  },
  "model": "gpt-5-mini",
  "provider": "openai"
}
```

### Output

- **Exit code 0**: Continue normally
- **Exit code 1** (blocking hooks only): Block execution
- **stderr**: Error messages or warnings
- **stdout**: Ignored (reserved for future use)

## Example Hooks

### 1. Security Check (`security_check.py`)

Blocks operations on sensitive files:

```python
#!/usr/bin/env python3
import json
import sys

input_data = json.loads(sys.stdin.read())

BLOCKED_PATHS = [".env", ".ssh/id_rsa", "/etc/passwd"]

if input_data.get("tool_name") == "write_file":
    file_path = input_data.get("tool_args", {}).get("file_path", "")
    for blocked in BLOCKED_PATHS:
        if blocked in file_path:
            print(f"Blocked: {blocked}", file=sys.stderr)
            sys.exit(1)  # Block execution

sys.exit(0)  # Allow
```

### 2. Tool Logger (`log_tool_usage.sh`)

Logs all tool executions:

```bash
#!/bin/bash
INPUT=$(cat)
EVENT=$(echo "$INPUT" | grep -o '"event":"[^"]*"' | cut -d'"' -f4)
TOOL=$(echo "$INPUT" | grep -o '"tool_name":"[^"]*"' | cut -d'"' -f4)
echo "[$(date)] $EVENT: $TOOL" >> ~/.nano-cli/logs/tools.log
exit 0
```

### 3. Performance Monitor (`performance_monitor.py`)

Tracks execution metrics:

```python
#!/usr/bin/env python3
import json
import sys
from pathlib import Path

input_data = json.loads(sys.stdin.read())

if input_data.get("event") == "post_agent_complete":
    metrics = {
        "timestamp": input_data.get("timestamp"),
        "execution_time": input_data.get("execution_time"),
        "token_usage": input_data.get("token_usage", {})
    }
    
    metrics_file = Path.home() / ".nano-cli/metrics/performance.jsonl"
    metrics_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(metrics_file, "a") as f:
        f.write(json.dumps(metrics) + "\n")

sys.exit(0)
```

## Hook Configuration Options

### Global Settings

- **`enabled`**: Master switch for all hooks
- **`timeout_seconds`**: Default timeout for hooks
- **`parallel_execution`**: Run non-blocking hooks in parallel

### Per-Hook Settings

- **`name`**: Unique identifier for the hook
- **`command`**: Command to execute (supports `~` expansion)
- **`blocking`**: If true, can block execution with exit code 1
- **`timeout`**: Maximum execution time in seconds
- **`enabled`**: Enable/disable individual hook
- **`contexts`**: Where hook runs (`["cli"]`, `["mcp"]`, or `["cli", "mcp"]`)
- **`matcher`**: Optional criteria for conditional execution
  - **`tool`**: List of tool names to match
  - **`pattern`**: Regex pattern for file paths

### Conditional Execution

Hooks can be configured to run only under specific conditions:

```json
{
  "name": "sensitive_file_check",
  "command": "check_sensitive.py",
  "blocking": true,
  "matcher": {
    "tool": ["write_file", "edit_file"],
    "pattern": ".*\\.(env|key|pem)$"
  }
}
```

## Context Detection

The hook system automatically detects the execution context:

- **CLI Context**: When running via `nano-cli` commands
- **MCP Context**: When running as an MCP server (Claude Desktop, etc.)

Hooks can be configured to run in specific contexts using the `contexts` field.

## Best Practices

1. **Keep hooks fast**: Use timeouts to prevent hanging
2. **Handle errors gracefully**: Always exit cleanly
3. **Use blocking sparingly**: Only for critical security/validation
4. **Log appropriately**: Use stderr for warnings, files for detailed logs
5. **Test thoroughly**: Test hooks in both CLI and MCP contexts
6. **Version control**: Keep hook scripts in version control
7. **Document behavior**: Comment complex logic in hook scripts

## Troubleshooting

### Hooks not triggering

1. Check if hooks are enabled:
   ```bash
   cat ~/.nano-cli/hooks.json | jq '.enabled'
   ```

2. Verify hook script exists and is executable:
   ```bash
   ls -la ~/.nano-cli/hooks/
   ```

3. Check for errors in logs:
   ```bash
   nano-cli run "test" --verbose
   ```

### Hook blocking unexpectedly

1. Test hook script manually:
   ```bash
   echo '{"event":"pre_tool_use","tool_name":"write_file"}' | python3 ~/.nano-cli/hooks/security_check.py
   echo $?  # Check exit code
   ```

2. Increase timeout if needed:
   ```json
   {
     "timeout": 10
   }
   ```

### Performance issues

1. Disable parallel execution for debugging:
   ```json
   {
     "parallel_execution": false
   }
   ```

2. Profile individual hooks:
   ```bash
   time echo '{}' | ~/.nano-cli/hooks/your_hook.py
   ```

## Advanced Usage

### Dynamic Hook Loading

Hooks can be loaded from multiple locations:
1. Global: `~/.nano-cli/hooks.json`
2. Project: `./.nano-cli/hooks.json`
3. Custom: Via environment variable (future feature)

### Hook Chaining

Multiple hooks for the same event are executed in order:

```json
{
  "pre_tool_use": [
    {"name": "validator", "blocking": true},
    {"name": "logger", "blocking": false},
    {"name": "metrics", "blocking": false}
  ]
}
```

### Cross-Hook Communication

Hooks can communicate via:
- Shared files in `~/.nano-cli/state/`
- Environment variables (set by nano-agent)
- Return values (future feature)

## Security Considerations

1. **Hook scripts run with user privileges** - Be careful with commands
2. **Validate all input** - Hooks receive untrusted data
3. **Avoid shell injection** - Use proper escaping in scripts
4. **Limit file access** - Hooks should only access necessary files
5. **Review third-party hooks** - Audit before installation

## Future Enhancements

Planned features for the hooks system:

- [ ] Hook management CLI commands
- [ ] Hook marketplace/registry
- [ ] Built-in hook templates
- [ ] Hook composition and pipelines
- [ ] Async hook support
- [ ] Hook state management
- [ ] Web-based hook editor
- [ ] Hook testing framework