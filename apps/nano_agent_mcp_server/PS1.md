# PS1 Prompt Customization

The nano-cli interactive mode supports customizable prompt strings (PS1) similar to bash/zsh shells.

## Quick Start

In interactive mode, use the `/ps1` command to customize your prompt:

```bash
# Show current PS1 format and help
nano-agent> /ps1

# Set a custom prompt format
nano-agent> /ps1 {pwd} [{agent}@{model}] >
nano-agent> /ps1 [{time}] {agent}@{model} $
```

## Available Variables

The following variables can be used in your PS1 format string:

| Variable | Description | Example |
|----------|-------------|---------|
| `{name}` | Application name | `nano-agent` |
| `{time}` | Current time (HH:MM:SS) | `14:30:45` |
| `{agent}` | Current agent personality | `coder`, `h4x0r`, `default` |
| `{model}` | Current AI model | `gpt-5-mini` |
| `{pwd}` | Current working directory | `~/projects/app` |

## Default Format

The default PS1 format is:
```
{time} {agent}@{model} > 
```

Which displays as:
```
14:30:45 coder@gpt-5-mini > 
```

## Example Formats

### Minimal
```bash
/ps1 > 
# Result: > 
```

### Time and Path
```bash
/ps1 [{time}] {pwd} $ 
# Result: [14:30:45] ~/projects $ 
```

### Agent and Model
```bash
/ps1 {agent}@{model} > 
# Result: coder@gpt-5-mini > 
```

### Full Information
```bash
/ps1 {pwd} [{agent}:{model}] > 
# Result: ~/projects [coder:gpt-5-mini] > 
```

### Classic Shell Style
```bash
/ps1 {pwd} $ 
# Result: ~/projects $ 
```

### Verbose
```bash
/ps1 [{time}] {name} ({agent}) on {model} in {pwd} > 
# Result: [14:30:45] nano-agent (coder) on gpt-5-mini in ~/projects > 
```

## Persistence

Your PS1 format is automatically saved to `~/.nano-cli/config.json` and will be restored in future sessions.

## Configuration File

The configuration is stored in JSON format:

```json
{
  "ps1_format": "{time} {agent}@{model} > "
}
```

You can manually edit this file if needed, but using the `/ps1` command is recommended.

## Color Styling

The prompt elements are automatically styled with colors:
- Time: Gray
- Agent: Cyan
- Model: Blue
- Path: Magenta
- Name: Green
- Prompt chars (>, $, #): Yellow

## Dynamic Updates

All variables are evaluated dynamically:
- `{time}` updates every prompt
- `{pwd}` reflects the current directory
- `{agent}` updates when you switch agents with `@agent`
- `{model}` updates when you change models with `/model`

## Tips

1. **Keep it simple**: Too much information can be distracting
2. **Include context**: Show what's important for your workflow
3. **Use separators**: Characters like `[`, `]`, `@`, `:` help readability
4. **Test first**: Try the format with `/ps1` before saving
5. **Reset to default**: Use `/ps1 {time} {agent}@{model} > ` to restore defaults

## Related Commands

- `/model <name>` - Change the current model
- `@<agent>` - Switch to a different agent
- `/agents` - List available agents
- `/help` - Show all available commands