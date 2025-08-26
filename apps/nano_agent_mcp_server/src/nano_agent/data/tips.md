# Nano Agent Tips & Tricks

## Power User Tips

### 1. Efficient Command Usage
- Use Tab completion to save time
- Chain commands with shell integration: `!git status && /analyze changes`
- Use command templates: `/analyze @file.py --detailed`

### 2. Agent Specialization
- Switch agents mid-conversation for different perspectives
- Example workflow:
  - `@analyst` - Analyze the problem
  - `@coder` - Implement the solution  
  - `@qa` - Review and test

### 3. Custom Workflows
Create your own command templates in `~/.nano-cli/commands/`:
- `/review` - Code review template
- `/deploy` - Deployment checklist
- `/debug` - Debugging workflow

### 4. Shell Integration
Combine shell commands with AI analysis:
```bash
!find . -name "*.py" | /analyze "security vulnerabilities"
!git diff | /explain "what changed"
```

### 5. Context Management
- Use `/reset` to start fresh conversations
- Keep chat history for complex discussions
- Save important responses with `!echo "response" > notes.md`

## Keyboard Shortcuts

- **Tab** - Autocomplete commands and paths
- **↑/↓** - Navigate command history
- **Ctrl+C** - Cancel current operation
- **Ctrl+D** - Exit interactive mode
- **Ctrl+L** - Clear screen (same as `/clear`)
- **Ctrl+R** - Search command history

## Advanced Features

### Multi-Model Comparison
Compare responses from different models:
```bash
/model gpt-5-mini
What is recursion?
/model gpt-4o
What is recursion?
```

### Agent Chaining
Use multiple agents for comprehensive analysis:
```bash
@analyst
Analyze this codebase structure
@security  
Review for vulnerabilities
@performance
Identify bottlenecks
```

### Custom PS1 Formats
Create context-aware prompts:
- Development: `{pwd} [{agent}] $ `
- Time tracking: `[{time}] {model} > `
- Full info: `{pwd} [{time}] {agent}@{model} > `

## Productivity Hacks

1. **Aliases**: Create shell aliases for common operations
2. **Templates**: Use command files for repetitive tasks
3. **Agents**: Customize agents for your workflow
4. **Config**: Set optimal defaults in config.json
5. **History**: Learn from past sessions with history search