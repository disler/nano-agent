# Nano CLI Commands System

The nano-cli now supports a command file system similar to Claude Code's `.claude/commands/` pattern. This allows you to create reusable prompt templates that can be invoked with simple commands.

## Overview

Commands are markdown files stored in `~/.nano-cli/commands/` that define reusable prompts. When you run `nano-cli run '/command arguments'`, the CLI loads the command file, substitutes your arguments, and executes the resulting prompt.

## Usage

### Running Commands

```bash
# Use /command syntax with the run command
nano-cli run '/summarize README.md contents here'
nano-cli run '/analyze "$(cat src/main.py)"' --model gpt-5
nano-cli run '/explain how async works in Python' --verbose
```

### Managing Commands

```bash
# List all available commands
nano-cli commands list

# Create a new command template
nano-cli commands create my-command

# Show command details
nano-cli commands show summarize

# Edit a command (opens in default editor)
nano-cli commands edit analyze
```

## Command File Format

Command files are markdown files with the following structure:

```markdown
# Command Name

Description of what this command does.

## Prompt Template

Your prompt here with $ARGUMENTS placeholder.

The $ARGUMENTS will be replaced with whatever 
the user passes after the command name.

## Usage

Examples of how to use this command.

## Notes

Additional context or requirements.
```

## Interactive Mode

The nano-cli includes an enhanced interactive mode with autocompletion and command support:

```bash
# Start interactive mode
nano-cli interactive

# Start with specific model
nano-cli interactive --model gpt-5 --provider openai

# Use simple mode (no autocompletion)
nano-cli interactive --simple
```

### Interactive Features

- **Tab Autocompletion**: Press Tab to autocomplete /commands and special commands
- **Command History**: Use ↑/↓ arrows to navigate through previous commands
- **Inline Commands**: Type `/command args` directly in interactive mode
- **Model Switching**: Change models on the fly with `model <name>`
- **Built-in Help**: Type `help` for available commands
- **Command Listing**: Type `commands` to see available command files
- **Verbose Toggle**: Enable/disable verbose output with `verbose on/off`

### Interactive Commands

All commands use the `/` prefix for consistency:

| Command | Description |
|---------|------------|
| `/help` | Show help information |
| `/help <cmd>` | Show help for specific command |
| `/commands` | List available command files |
| `/commands show <cmd>` | Display full command file content |
| `/clear` | Clear the screen |
| `/history` | Show command history |
| `/exit`, `/quit` | Exit interactive mode |
| `/model <name>` | Change the model |
| `/provider <name>` | Change the provider |
| `/verbose [on/off]` | Toggle verbose output |
| `!<command>` | Execute shell command (uses $SHELL) |
| `/<command> args` | Run a command file |

**Note**: Legacy commands without `/` (like `exit`, `quit`) still work for backward compatibility but are not advertised.

## Built-in Commands

The system comes with several pre-built commands:

### `/summarize` - Generate summaries
```bash
nano-cli run '/summarize "long text to summarize"'
```

### `/analyze` - Perform detailed analysis
```bash
nano-cli run '/analyze "$(cat code.py)"'
```

### `/explain` - Get clear explanations
```bash
nano-cli run '/explain concept or code'
```

### `/refactor` - Suggest code improvements
```bash
nano-cli run '/refactor "messy code here"'
```

### `/test` - Generate test cases
```bash
nano-cli run '/test "function to test"'
```

## Creating Custom Commands

1. Create a new command template:
```bash
nano-cli commands create my-task
```

2. Edit the generated template at `~/.nano-cli/commands/my-task.md`

3. Use your command:
```bash
nano-cli run '/my-task "arguments for your task"'
```

## Advanced Usage

### Using with Different Models

Commands work with all nano-cli options:

```bash
# Use Claude model
nano-cli run '/summarize "text"' --model claude-3-haiku-20240307 --provider anthropic

# Use local Ollama model
nano-cli run '/analyze "code"' --model gpt-oss:20b --provider ollama

# Verbose output
nano-cli run '/explain "concept"' --verbose
```

### Passing File Contents

```bash
# Pass file contents as arguments
nano-cli run "/summarize \"$(cat README.md)\""

# Multiple files
nano-cli run "/analyze \"$(cat src/*.py)\""
```

### Complex Arguments

The `$ARGUMENTS` placeholder captures everything after the command name:

```bash
nano-cli run '/explain the difference between REST and GraphQL APIs'
# $ARGUMENTS = "the difference between REST and GraphQL APIs"
```

## Directory Structure

```
~/.nano-cli/
└── commands/
    ├── summarize.md
    ├── analyze.md
    ├── explain.md
    ├── refactor.md
    ├── test.md
    └── [your-custom-commands].md
```

## Tips

1. **Descriptive Names**: Use clear, action-oriented command names
2. **Document Usage**: Include examples in your command files
3. **Version Control**: Consider storing custom commands in git
4. **Sharing**: Commands are just markdown files - easy to share with your team

## Troubleshooting

- **Command not found**: Check that the `.md` file exists in `~/.nano-cli/commands/`
- **No commands directory**: It's created automatically when you first use the commands feature
- **Edit not working**: Set your `EDITOR` environment variable or install `nano`

## Implementation Details

The command system is implemented via:
- `modules/command_loader.py` - Command loading and parsing logic
- Modified `cli.py` - Integration with the main CLI
- Command detection via `/command` syntax in the prompt argument