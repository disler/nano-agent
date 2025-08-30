# Claude-Inspired Features for nano-cli

This document describes the new Claude CLI-inspired features added to `nano-cli` to enhance the user experience.

## New Features

### 1. Session Management 📝

**Conversation persistence across commands**

- Sessions automatically save your conversation history
- Continue previous conversations with context preservation  
- Named sessions for organizing different projects/topics

**Commands:**
```bash
# Start a new session (automatic)
nano-cli run "Create a Python function" --save

# Continue the last session
nano-cli run "Add error handling to the function" --continue

# Use a specific session
nano-cli run "Update the function" --session session_20250129_143022_a1b2c3

# List all sessions
nano-cli sessions list

# View a specific session
nano-cli sessions show --id session_20250129_143022_a1b2c3

# Clear old sessions (>30 days)
nano-cli sessions clear --days 30
```

### 2. Enhanced Command-Line Arguments 🎛️

**New options for fine-tuning agent behavior:**

```bash
# Temperature control (0.0-2.0)
nano-cli run "Write creative story" --temperature 1.5

# Max tokens limit
nano-cli run "Summarize this" --max-tokens 500

# Disable rich formatting
nano-cli run "Simple output" --no-rich

# Force new session
nano-cli run "Start fresh" --new

# Don't save to history
nano-cli run "Temporary task" --no-save
```

### 3. Session Context Preservation 🔄

**Maintain conversation context across multiple commands:**

```bash
# First command
nano-cli run "Create a TODO app in Python" --save

# Continue with context
nano-cli run "Add a delete function" --continue
# The agent remembers the TODO app context

# Continue later (even after closing terminal)
nano-cli run "Add priority levels to tasks" --continue
```

### 4. Provider and Model Persistence 🔧

Sessions remember your provider and model settings:

```bash
# Start with specific provider/model
nano-cli run "Hello" --provider ollama --model gpt-oss:20b --save

# Continue uses same settings automatically
nano-cli run "Create a function" --continue
# Automatically uses ollama/gpt-oss:20b
```

### 5. Session Metadata Tracking 📊

Each session tracks:
- Total tokens used
- Total cost (for paid providers)
- Message count
- Creation and update timestamps
- Provider and model information

## Storage Location

Sessions are stored in: `~/.nano-cli/sessions/`

Each session is a JSON file with complete conversation history and metadata.

## Benefits

1. **Context Preservation**: No need to repeat context in follow-up commands
2. **Project Organization**: Keep different projects in separate sessions
3. **Cost Tracking**: Monitor token usage and costs per session
4. **Flexibility**: Fine-tune model behavior with temperature and token limits
5. **History**: Review past conversations and results

## Examples

### Example 1: Iterative Development
```bash
# Start a new project
nano-cli run "Create a Flask API for user management" --save

# Add features iteratively
nano-cli run "Add authentication endpoints" --continue
nano-cli run "Add input validation" --continue
nano-cli run "Add unit tests" --continue

# Review the session later
nano-cli sessions show --id session_20250129_143022_a1b2c3
```

### Example 2: Different Projects
```bash
# Project A
nano-cli run "Create React component for dashboard" --new
# Session ID: session_20250129_143022_a1b2c3

# Project B  
nano-cli run "Write Python data analysis script" --new
# Session ID: session_20250129_144533_d4e5f6

# Continue Project A
nano-cli run "Add charts to dashboard" --session session_20250129_143022_a1b2c3

# Continue Project B
nano-cli run "Add visualization" --session session_20250129_144533_d4e5f6
```

### Example 3: Experimentation
```bash
# Try with high creativity
nano-cli run "Write a poem about coding" --temperature 1.8 --no-save

# Try with low creativity  
nano-cli run "Write technical documentation" --temperature 0.2 --save
```

## Compatibility

- All existing `nano-cli` commands continue to work
- New features are opt-in via command-line flags
- Default behavior unchanged unless flags are used
- Backward compatible with existing workflows

## Implementation Details

### Session Manager Module
- `src/nano_agent/modules/session_manager.py`: Core session management
- Handles creation, loading, saving, and querying sessions
- Automatic cleanup of old sessions

### CLI Enhancements
- `src/nano_agent/cli.py`: Updated with new command-line arguments
- Integration with session manager
- New `sessions` command for management

### Data Types
- `src/nano_agent/modules/data_types.py`: Extended with temperature and max_tokens
- Support for chat history in requests

## Future Enhancements

Potential additions inspired by Claude CLI:
1. Session export/import for sharing
2. Session search by content
3. Session templates for common workflows
4. Multi-user session sharing
5. Session branching (fork a session)
6. Rich markdown rendering in terminal
7. Session replay/playback functionality

## Configuration

Default values use Ollama with gpt-oss:20b model for cost-effective local operation:
- Provider: `ollama`
- Model: `gpt-oss:20b`
- Temperature: `0.2`
- Max Tokens: `4000`

These can be overridden via command-line arguments or configuration files.