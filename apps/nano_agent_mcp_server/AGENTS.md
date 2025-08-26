# Nano CLI Agent System

The nano-cli supports customizable agent personalities that extend the base system prompt with specialized behaviors and expertise.

## Overview

Agents are markdown files stored in `~/.nano-cli/agents/` that define specialized personalities, behaviors, and expertise areas for the nano-agent. When an agent is loaded, its content is appended to the base system prompt, allowing you to customize how the AI responds and behaves.

## Usage

### Running with a specific agent

```bash
# Use the --agent flag with the run command
nano-cli run "Write a Python function" --agent coder

# Use the --agent flag with interactive mode
nano-cli interactive --agent h4x0r
```

### Switching agents in interactive mode

```bash
# In interactive mode, use @ to switch agents
nano-agent> @coder        # Switch to coder agent
nano-agent> @analyst      # Switch to analyst agent  
nano-agent> @             # Show current agent and list available
```

### Managing agents

```bash
# List all available agents
nano-agent> /agents

# Show agent file content
nano-agent> /agents show coder

# The agents are stored in ~/.nano-cli/agents/
ls ~/.nano-cli/agents/
```

## Agent File Format

Agent files are markdown files with the following structure:

```markdown
# Agent Name

Brief description of the agent's purpose.

## Personality
Description of the agent's personality traits and communication style.

## Expertise
- Area of expertise 1
- Area of expertise 2
- Area of expertise 3

## Behavioral Guidelines
- How the agent should behave
- What it should prioritize
- How it approaches problems

## Response Style
How the agent structures and formats its responses.

## Examples
Specific examples of how this agent handles requests.

## Notes
Any additional context or requirements.
```

## Built-in Agents

### default
The standard nano-agent with no special modifications.

### h4x0r
A l33t h4x0r agent that speaks in geek/leet speak (1337speak).

### coder
A senior software engineer focused on clean code, design patterns, and best practices.

### analyst
A data analyst and researcher with strong analytical and investigative skills.

### creative
A creative problem solver with a talent for thinking outside the box.

## Creating Custom Agents

1. Create a new markdown file in `~/.nano-cli/agents/`:
```bash
nano ~/.nano-cli/agents/my-agent.md
```

2. Define the agent's personality and behavior using the format above.

3. Use the agent:
```bash
nano-cli run "Hello" --agent my-agent
# Or in interactive mode
nano-agent> @my-agent
```

## How It Works

1. When an agent is specified, the system loads the markdown file from `~/.nano-cli/agents/<agent_name>.md`
2. The content is appended to the base NANO_AGENT_SYSTEM_PROMPT
3. This extended prompt is used to initialize the AI agent
4. The agent maintains this personality throughout the conversation

## Chat History Integration

When switching agents in interactive mode:
- The chat history is preserved
- A system message is added to indicate the agent switch
- The new agent personality takes effect for subsequent messages
- Use `/reset` or `/new` to clear chat history and start fresh

## Examples

### Using the coder agent for code review:
```bash
nano-cli run "Review this Python code: def factorial(n): return 1 if n <= 1 else n * factorial(n-1)" --agent coder
```

### Using the analyst agent for data analysis:
```bash
nano-cli run "Analyze the performance metrics in metrics.json" --agent analyst
```

### Using the h4x0r agent for fun:
```bash
nano-cli interactive --agent h4x0r
nano-agent> Hello, tell me about Python
# Response will be in l33t speak
```

## Tips

1. **Specialized Tasks**: Use specific agents for tasks that match their expertise
2. **Consistency**: Agents maintain their personality throughout a session
3. **Experimentation**: Try different agents for the same task to get varied perspectives
4. **Custom Agents**: Create agents tailored to your specific needs or projects
5. **Agent Switching**: Switch agents mid-conversation to get different viewpoints

## Agent Metadata (Optional)

Some agent files may include YAML frontmatter with metadata:

```yaml
---
name: agent-name
description: Brief description
tools: Tool1, Tool2
color: green
---
```

This metadata is optional and used for display purposes.