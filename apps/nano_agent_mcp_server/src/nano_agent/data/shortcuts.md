# Quick Reference Card

## Essential Commands
| Command | Description |
|---------|-------------|
| `/help` | Show help menu |
| `/exit` | Exit interactive mode |
| `/clear` | Clear screen |
| `/reset` | Clear chat history |
| `/commands` | List command templates |
| `/agents` | List agent personalities |

## Settings Commands
| Command | Description |
|---------|-------------|
| `/model <name>` | Change AI model |
| `/provider <name>` | Change provider |
| `/ps1 <format>` | Customize prompt |
| `/welcome on/off` | Toggle welcome message |
| `/verbose on/off` | Toggle detailed output |

## Agent Management
| Command | Description |
|---------|-------------|
| `@<agent>` | Switch to agent |
| `@` | Show current agent |
| `/agents show <name>` | View agent details |

## Shell Integration
| Command | Description |
|---------|-------------|
| `!<command>` | Execute shell command |
| `!pwd` | Show current directory |
| `!ls` | List files |
| `!git status` | Check git status |

## Command Templates
| Command | Description |
|---------|-------------|
| `/summarize <text>` | Generate summary |
| `/analyze <code>` | Analyze code |
| `/explain <concept>` | Get explanation |
| `/refactor <code>` | Improve code |
| `/test <function>` | Generate tests |

## PS1 Variables
| Variable | Shows |
|----------|--------|
| `{time}` | Current time |
| `{agent}` | Active agent |
| `{model}` | Current model |
| `{pwd}` | Working directory |
| `{name}` | App name |

## Available Models
### OpenAI
- `gpt-5-mini` (default)
- `gpt-5-nano`
- `gpt-5`
- `gpt-4o`
- `gpt-4o-mini`

### Anthropic
- `claude-3-haiku-20240307`
- `claude-opus-4-1-20250805`
- `claude-sonnet-4-20250514`

### Ollama (Local)
- `gpt-oss:20b`
- `gpt-oss:120b`