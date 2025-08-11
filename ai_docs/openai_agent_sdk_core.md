# OpenAI Agents SDK: Engineering-Focused Implementation Guide

## Overview

The OpenAI Agents SDK enables building production-ready agentic AI applications with minimal abstractions. This guide focuses on long-running coding agents that complete engineering work autonomously.

## Core Architecture

### Key Primitives
- **Agents**: LLMs with instructions, tools, and context
- **Handoffs**: Delegation between specialized agents
- **Guardrails**: Input/output validation
- **Sessions**: Automatic conversation history management
- **Streaming**: Real-time progress monitoring

### Latest Model Capabilities (August 2025)

#### GPT-5 Series for Engineering
- **gpt-5**: PhD-level expertise for complex architectural decisions
- **gpt-5-mini**: 80% performance at 20% cost for production workflows
- **gpt-5-nano**: Ultra-fast responses for CI/CD and edge deployment
- **400K Context**: Process entire codebases in single conversations

#### GPT-OSS for Local Development
- **gpt-oss:20b**: Consumer hardware optimization (16GB+ VRAM)
- **gpt-oss:120b**: High-performance local deployment (80GB+ VRAM)
- **Apache 2.0 License**: Free for commercial use
- **131K Context**: Extended reasoning for complex engineering tasks

#### Claude 4 for Research
- **200K Context**: Comprehensive codebase analysis
- **Enhanced Reasoning**: Multi-step problem solving
- **Long-Horizon Tasks**: Extended engineering workflows

## Installation and Setup

```bash
# Using UV (recommended for our nano-agent)
uv add openai-agents

# Or pip
pip install openai-agents

# Set API key
export OPENAI_API_KEY=sk-...
```

## System Prompts for Engineering Work

### Core Engineering Agent

```python
from agents import Agent, ModelSettings
from typing import Any
from dataclasses import dataclass

@dataclass
class EngineeringContext:
    """Context for engineering agents."""
    project_path: str
    language: str
    framework: str = None
    test_command: str = None
    lint_command: str = None
    
CORE_ENGINEERING_PROMPT = """You are an expert software engineer focused on completing tasks autonomously.

Core Principles:
1. COMPLETION: Work until the task is fully complete and tested
2. VERIFICATION: Always verify your work with tests and linting
3. QUALITY: Write production-ready, maintainable code
4. CONTEXT: Understand the codebase before making changes
5. ITERATION: Fix issues immediately when found

Workflow:
1. Analyze the request and existing codebase
2. Create a detailed plan
3. Implement changes incrementally
4. Test each change
5. Fix any issues
6. Verify everything works end-to-end
7. Document changes if needed

Error Handling:
- If tests fail, debug and fix immediately
- If linting fails, correct all issues
- If build fails, resolve dependencies
- Continue until all checks pass

Never leave work incomplete. If blocked, explain why and suggest solutions."""

engineering_agent = Agent[EngineeringContext](
    name="Engineering Agent",
    instructions=CORE_ENGINEERING_PROMPT,
    model="gpt-4-turbo",
    model_settings=ModelSettings(
        temperature=0.2,  # Lower temperature for more consistent code
        top_p=0.9,
    ),
)
```

### Specialized Agent Variants

```python
# Research and Planning Agent
RESEARCH_AGENT_PROMPT = """You are a technical research specialist who thoroughly investigates before implementation.

Your approach:
1. Search and analyze the entire codebase
2. Identify all dependencies and patterns
3. Research best practices for the technology stack
4. Create comprehensive implementation plans
5. Identify potential issues before they occur

Focus on:
- Understanding existing architecture
- Finding reusable components
- Identifying edge cases
- Proposing multiple solutions with trade-offs"""

# Debugging Specialist
DEBUG_AGENT_PROMPT = """You are a debugging specialist who systematically resolves issues.

Methodology:
1. Reproduce the issue consistently
2. Add logging/debugging statements
3. Isolate the problem domain
4. Test hypotheses methodically
5. Implement and verify fixes
6. Add tests to prevent regression

Never guess. Use evidence-based debugging.
Always clean up debug code after fixing."""

# Refactoring Expert
REFACTOR_AGENT_PROMPT = """You are a refactoring expert focused on code quality.

Your process:
1. Analyze code for patterns and anti-patterns
2. Identify improvement opportunities
3. Refactor incrementally with tests
4. Ensure backward compatibility
5. Update documentation
6. Verify performance isn't degraded

Principles:
- DRY (Don't Repeat Yourself)
- SOLID principles
- Clean Code practices
- Performance awareness
- Maintainability focus"""

# Test-Driven Development Agent
TDD_AGENT_PROMPT = """You follow strict TDD methodology.

Workflow:
1. Write failing tests first
2. Implement minimal code to pass
3. Refactor while keeping tests green
4. Add edge case tests
5. Ensure 100% critical path coverage

Never write code without tests.
Tests should be clear, isolated, and fast."""
```

## Long-Running Agent Implementation

### Basic Long-Running Agent

```python
from agents import Agent, Runner, function_tool, Context
from agents.exceptions import MaxTurnsExceeded
import asyncio
import subprocess
from typing import List, Dict, Any

@function_tool
def run_command(command: str, cwd: str = None) -> Dict[str, Any]:
    """Execute shell commands for building, testing, etc."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd,
            capture_output=True, 
            text=True,
            timeout=300  # 5 minute timeout
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out after 5 minutes"
        }

@function_tool
def read_file(file_path: str) -> str:
    """Read file contents."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@function_tool
def write_file(file_path: str, content: str) -> str:
    """Write content to file."""
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@function_tool
def search_codebase(pattern: str, file_extension: str = None) -> List[str]:
    """Search for patterns in codebase."""
    import glob
    import re
    
    matches = []
    search_pattern = f"**/*.{file_extension}" if file_extension else "**/*"
    
    for file_path in glob.glob(search_pattern, recursive=True):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                if re.search(pattern, content):
                    matches.append(file_path)
        except:
            continue
    
    return matches

# Create the long-running agent
engineering_agent = Agent(
    name="Engineering Agent",
    instructions=CORE_ENGINEERING_PROMPT,
    tools=[run_command, read_file, write_file, search_codebase],
    model="gpt-4-turbo",
    model_settings=ModelSettings(
        temperature=0.2,
        max_tokens=4000,
    ),
)

async def run_engineering_task(task: str, max_attempts: int = 3):
    """Run an engineering task with retry logic."""
    
    for attempt in range(max_attempts):
        try:
            result = await Runner.run(
                engineering_agent,
                task,
                max_turns=50,  # Allow many turns for complex tasks
                run_config=RunConfig(
                    workflow_name="engineering_task",
                    trace_metadata={"task": task, "attempt": attempt}
                )
            )
            
            # Verify task completion
            if "complete" in result.final_output.lower():
                return result
                
        except MaxTurnsExceeded:
            print(f"Attempt {attempt + 1} exceeded max turns, retrying...")
            continue
            
    raise Exception("Failed to complete task after maximum attempts")
```

### Advanced Multi-Agent Orchestration

```python
from agents import Agent, Runner, RunConfig, SQLiteSession
from pydantic import BaseModel
from typing import Optional

class TaskStatus(BaseModel):
    """Track task completion status."""
    task_complete: bool
    tests_passing: bool
    lint_passing: bool
    blockers: Optional[List[str]]
    next_steps: Optional[List[str]]

# Planning Agent
planning_agent = Agent(
    name="Planner",
    instructions="""Break down engineering tasks into clear steps.
    Output a structured plan with dependencies and success criteria.""",
    output_type=List[str],
)

# Implementation Agent
implementation_agent = Agent(
    name="Implementer", 
    instructions=CORE_ENGINEERING_PROMPT,
    tools=[run_command, read_file, write_file],
    output_type=TaskStatus,
)

# Review Agent
review_agent = Agent(
    name="Reviewer",
    instructions="""Review code changes for:
    - Correctness
    - Performance
    - Security
    - Best practices
    Provide specific feedback.""",
    handoff_description="Code review specialist",
)

# Orchestrator Agent with Handoffs
orchestrator = Agent(
    name="Orchestrator",
    instructions="""Coordinate the engineering workflow:
    1. Use Planner for task breakdown
    2. Use Implementer for coding
    3. Use Reviewer for quality checks
    4. Iterate until complete""",
    handoffs=[planning_agent, implementation_agent, review_agent],
)

async def run_complex_engineering_task(task: str):
    """Run a complex task with multi-agent orchestration."""
    
    # Use session for conversation memory
    session = SQLiteSession(f"task_{hash(task)}", "engineering_tasks.db")
    
    result = await Runner.run(
        orchestrator,
        task,
        session=session,
        max_turns=100,
        run_config=RunConfig(
            workflow_name="complex_engineering",
            trace_metadata={"task": task}
        )
    )
    
    return result
```

## Monitoring and Logging

### Comprehensive Monitoring Setup

```python
from agents import Agent, Runner, RunConfig
from agents.lifecycle import AgentHooks
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_runs.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('nano_agent')

class EngineeringAgentHooks(AgentHooks):
    """Custom hooks for monitoring agent execution."""
    
    def __init__(self, logger):
        self.logger = logger
        self.start_time = None
        self.tool_calls = []
        
    async def on_agent_start(self, agent, input_items):
        """Log when agent starts."""
        self.start_time = datetime.now()
        self.logger.info(f"Agent {agent.name} started at {self.start_time}")
        self.logger.debug(f"Input: {json.dumps(input_items[:100])}...")  # Log first 100 chars
        
    async def on_agent_end(self, agent, output):
        """Log when agent completes."""
        duration = (datetime.now() - self.start_time).total_seconds()
        self.logger.info(f"Agent {agent.name} completed in {duration:.2f}s")
        self.logger.debug(f"Output preview: {str(output)[:200]}...")
        
    async def on_tool_call(self, tool_name, arguments):
        """Log tool usage."""
        self.tool_calls.append({
            "tool": tool_name,
            "args": arguments,
            "timestamp": datetime.now().isoformat()
        })
        self.logger.info(f"Tool called: {tool_name}")
        self.logger.debug(f"Arguments: {json.dumps(arguments)}")
        
    async def on_error(self, error):
        """Log errors."""
        self.logger.error(f"Agent error: {str(error)}", exc_info=True)
        
    def get_metrics(self):
        """Return execution metrics."""
        return {
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "tool_calls": len(self.tool_calls),
            "tools_used": list(set(t["tool"] for t in self.tool_calls))
        }

# Create monitored agent
monitored_agent = Agent(
    name="Monitored Engineering Agent",
    instructions=CORE_ENGINEERING_PROMPT,
    tools=[run_command, read_file, write_file],
    hooks=EngineeringAgentHooks(logger),
)

async def run_with_monitoring(task: str):
    """Run task with comprehensive monitoring."""
    
    logger.info(f"Starting task: {task}")
    
    try:
        result = await Runner.run(
            monitored_agent,
            task,
            run_config=RunConfig(
                workflow_name="monitored_engineering",
                trace_metadata={
                    "task": task,
                    "timestamp": datetime.now().isoformat(),
                    "environment": "development"
                },
                # Enable tracing for OpenAI dashboard
                tracing_disabled=False,
                trace_include_sensitive_data=False,
            )
        )
        
        # Log metrics
        metrics = monitored_agent.hooks.get_metrics()
        logger.info(f"Task completed. Metrics: {json.dumps(metrics)}")
        
        # Store result for analysis
        with open(f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump({
                "task": task,
                "final_output": result.final_output,
                "metrics": metrics,
                "new_items_count": len(result.new_items),
            }, f, indent=2)
            
        return result
        
    except Exception as e:
        logger.error(f"Task failed: {str(e)}", exc_info=True)
        raise
```

## Streaming for Live Feedback

### Real-Time Progress Streaming

```python
from agents import Agent, Runner, ItemHelpers
from agents.stream_events import StreamEvent, RawResponsesStreamEvent, RunItemStreamEvent
from openai.types.responses import ResponseTextDeltaEvent
import asyncio

class StreamingEngineeringAgent:
    """Engineering agent with live streaming feedback."""
    
    def __init__(self):
        self.agent = Agent(
            name="Streaming Engineer",
            instructions=CORE_ENGINEERING_PROMPT,
            tools=[run_command, read_file, write_file],
        )
        self.current_output = ""
        self.tool_outputs = []
        
    async def run_with_streaming(self, task: str, progress_callback=None):
        """Run task with streaming updates."""
        
        result = Runner.run_streamed(self.agent, task)
        
        async for event in result.stream_events():
            await self.handle_stream_event(event, progress_callback)
            
        # Return complete result
        await result.wait()
        return result
        
    async def handle_stream_event(self, event: StreamEvent, callback):
        """Process streaming events."""
        
        if event.type == "raw_response_event":
            # Handle token-by-token streaming
            if isinstance(event.data, ResponseTextDeltaEvent):
                self.current_output += event.data.delta
                if callback:
                    await callback({
                        "type": "text_delta",
                        "content": event.data.delta
                    })
                    
        elif event.type == "run_item_stream_event":
            # Handle completed items
            item = event.item
            
            if item.type == "tool_call_item":
                if callback:
                    await callback({
                        "type": "tool_call",
                        "tool": item.call.name,
                        "status": "started"
                    })
                    
            elif item.type == "tool_call_output_item":
                self.tool_outputs.append(item.output)
                if callback:
                    await callback({
                        "type": "tool_output",
                        "output": item.output[:200],  # First 200 chars
                        "status": "completed"
                    })
                    
            elif item.type == "message_output_item":
                message = ItemHelpers.text_message_output(item)
                if callback:
                    await callback({
                        "type": "message",
                        "content": message
                    })
                    
        elif event.type == "agent_updated_stream_event":
            # Handle agent handoffs
            if callback:
                await callback({
                    "type": "handoff",
                    "from": event.old_agent.name if event.old_agent else None,
                    "to": event.new_agent.name
                })

# Usage with live feedback
async def engineering_task_with_ui(task: str):
    """Run engineering task with UI updates."""
    
    agent = StreamingEngineeringAgent()
    
    async def update_ui(event):
        """Update UI based on streaming events."""
        if event["type"] == "text_delta":
            # Update live text display
            print(event["content"], end="", flush=True)
        elif event["type"] == "tool_call":
            print(f"\n🔧 Running: {event['tool']}")
        elif event["type"] == "tool_output":
            print(f"✅ Completed: {event['output'][:50]}...")
        elif event["type"] == "handoff":
            print(f"\n🔄 Handoff: {event['from']} → {event['to']}")
            
    result = await agent.run_with_streaming(task, update_ui)
    return result
```

## Practical Nano-Agent Implementation

### Complete Nano-Agent Setup

```python
"""
nano_agent.py - Production-ready engineering agent
"""

from agents import Agent, Runner, RunConfig, SQLiteSession, function_tool
from agents.exceptions import MaxTurnsExceeded, InputGuardrailTripwireTriggered
from agents.guardrails import InputGuardrail, GuardrailFunctionOutput
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import asyncio
import subprocess
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nano_agent")

# Configuration
class NanoAgentConfig(BaseModel):
    """Configuration for nano-agent."""
    max_turns: int = Field(default=50, description="Maximum agent turns")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout: int = Field(default=300, description="Command timeout in seconds")
    model: str = Field(default="gpt-4-turbo", description="Model to use")
    temperature: float = Field(default=0.2, description="Model temperature")
    enable_streaming: bool = Field(default=True, description="Enable streaming")
    session_db: str = Field(default="nano_sessions.db", description="Session database")

# Tools
@function_tool
def execute_code(code: str, language: str = "python") -> Dict[str, Any]:
    """Execute code snippets safely."""
    if language == "python":
        cmd = ["python", "-c", code]
    elif language == "javascript":
        cmd = ["node", "-e", code]
    else:
        return {"error": f"Unsupported language: {language}"}
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
    except Exception as e:
        return {"error": str(e)}

@function_tool
def git_operations(operation: str, args: List[str] = None) -> Dict[str, Any]:
    """Perform git operations."""
    allowed_ops = ["status", "diff", "add", "commit", "log", "branch"]
    if operation not in allowed_ops:
        return {"error": f"Operation {operation} not allowed"}
    
    cmd = ["git", operation] + (args or [])
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    return {
        "success": result.returncode == 0,
        "output": result.stdout,
        "error": result.stderr
    }

@function_tool
def project_structure() -> str:
    """Get project structure."""
    import os
    
    structure = []
    for root, dirs, files in os.walk(".", topdown=True):
        # Skip hidden and build directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
        
        level = root.replace(".", "").count(os.sep)
        indent = " " * 2 * level
        structure.append(f"{indent}{os.path.basename(root)}/")
        
        subindent = " " * 2 * (level + 1)
        for file in files[:10]:  # Limit files shown
            structure.append(f"{subindent}{file}")
            
    return "\n".join(structure[:100])  # Limit total lines

# Guardrails
async def safety_guardrail(ctx, agent, input_data):
    """Prevent potentially harmful operations."""
    dangerous_patterns = [
        "rm -rf /",
        "format c:",
        "delete system32",
        ":(){:|:&};:",  # Fork bomb
    ]
    
    input_str = str(input_data).lower()
    for pattern in dangerous_patterns:
        if pattern.lower() in input_str:
            return GuardrailFunctionOutput(
                output_info={"blocked": pattern},
                tripwire_triggered=True
            )
    
    return GuardrailFunctionOutput(
        output_info={"safe": True},
        tripwire_triggered=False
    )

# Agents
class NanoAgent:
    """Main nano-agent implementation."""
    
    def __init__(self, config: NanoAgentConfig = None):
        self.config = config or NanoAgentConfig()
        
        # System prompt combining all best practices
        self.system_prompt = """You are an elite software engineer with deep expertise in building production systems.

CORE MISSION: Complete engineering tasks autonomously with exceptional quality.

OPERATING PRINCIPLES:
1. UNDERSTAND before acting - analyze the codebase and requirements thoroughly
2. PLAN meticulously - break down complex tasks into clear steps
3. IMPLEMENT incrementally - make changes in small, testable chunks
4. VERIFY continuously - test every change immediately
5. ITERATE until perfect - fix all issues before considering task complete

WORKFLOW PROTOCOL:
1. Exploration Phase:
   - Understand project structure
   - Identify relevant files and dependencies
   - Research patterns and conventions used

2. Planning Phase:
   - Create detailed implementation plan
   - Identify potential risks and edge cases
   - Define success criteria

3. Implementation Phase:
   - Write clean, documented code
   - Follow existing patterns and style
   - Add comprehensive error handling

4. Verification Phase:
   - Run all tests
   - Verify functionality manually
   - Check for edge cases
   - Ensure no regressions

5. Completion Phase:
   - Clean up any debug code
   - Update documentation if needed
   - Summarize changes made

ERROR RECOVERY:
- When tests fail: Debug systematically, fix, and re-test
- When builds break: Resolve dependencies and configuration
- When blocked: Explain the issue and propose solutions

QUALITY STANDARDS:
- Code must be production-ready
- All tests must pass
- No linting errors
- Documentation for complex logic
- Performance considerations addressed

Remember: Your reputation depends on delivering complete, working solutions. Never leave a task partially done."""
        
        # Create the main agent
        self.agent = Agent(
            name="NanoAgent",
            instructions=self.system_prompt,
            tools=[
                execute_code,
                git_operations,
                project_structure,
                run_command,
                read_file,
                write_file,
                search_codebase
            ],
            model=self.config.model,
            model_settings=ModelSettings(
                temperature=self.config.temperature,
                top_p=0.9,
            ),
            input_guardrails=[
                InputGuardrail(guardrail_function=safety_guardrail)
            ],
        )
        
        # Create specialized agents for handoffs
        self.debug_agent = Agent(
            name="DebugSpecialist",
            instructions=DEBUG_AGENT_PROMPT,
            tools=[execute_code, read_file, write_file],
            handoff_description="Debugging complex issues",
        )
        
        self.test_agent = Agent(
            name="TestSpecialist", 
            instructions=TDD_AGENT_PROMPT,
            tools=[execute_code, read_file, write_file],
            handoff_description="Writing comprehensive tests",
        )
        
        # Orchestrator with handoffs
        self.orchestrator = Agent(
            name="Orchestrator",
            instructions="""Coordinate engineering work efficiently.
            Delegate to specialists when needed:
            - DebugSpecialist for complex debugging
            - TestSpecialist for test creation
            Complete the task using available resources.""",
            handoffs=[self.agent, self.debug_agent, self.test_agent],
        )
        
    async def run(self, task: str, session_id: str = None) -> Any:
        """Run an engineering task."""
        
        # Create session if ID provided
        session = None
        if session_id:
            session = SQLiteSession(session_id, self.config.session_db)
        
        # Configure run
        run_config = RunConfig(
            workflow_name="nano_agent_task",
            trace_metadata={
                "task": task[:100],
                "session_id": session_id,
            },
            model=self.config.model,
        )
        
        # Run with retries
        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"Starting task (attempt {attempt + 1}/{self.config.max_retries})")
                
                if self.config.enable_streaming:
                    result = await self._run_streaming(task, session, run_config)
                else:
                    result = await Runner.run(
                        self.orchestrator,
                        task,
                        session=session,
                        max_turns=self.config.max_turns,
                        run_config=run_config
                    )
                
                logger.info("Task completed successfully")
                return result
                
            except MaxTurnsExceeded:
                logger.warning(f"Max turns exceeded on attempt {attempt + 1}")
                if attempt < self.config.max_retries - 1:
                    # Simplify task or continue from current state
                    task = f"Continue the previous task: {task[:100]}"
                    continue
                raise
                
            except InputGuardrailTripwireTriggered as e:
                logger.error(f"Safety guardrail triggered: {e}")
                raise
                
            except Exception as e:
                logger.error(f"Task failed on attempt {attempt + 1}: {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise
                
    async def _run_streaming(self, task, session, run_config):
        """Run with streaming enabled."""
        
        result = Runner.run_streamed(
            self.orchestrator,
            task,
            session=session,
            max_turns=self.config.max_turns,
            run_config=run_config
        )
        
        # Process streaming events
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                if isinstance(event.data, ResponseTextDeltaEvent):
                    print(event.data.delta, end="", flush=True)
            elif event.type == "run_item_stream_event":
                if event.item.type == "tool_call_item":
                    print(f"\n[Tool: {event.item.call.name}]", flush=True)
                    
        await result.wait()
        return result

# CLI Interface
async def main():
    """CLI interface for nano-agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Nano-Agent: Autonomous Engineering Assistant")
    parser.add_argument("task", help="Engineering task to perform")
    parser.add_argument("--session", help="Session ID for conversation continuity")
    parser.add_argument("--model", default="gpt-4-turbo", help="Model to use")
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming")
    parser.add_argument("--max-turns", type=int, default=50, help="Maximum turns")
    
    args = parser.parse_args()
    
    # Configure agent
    config = NanoAgentConfig(
        model=args.model,
        enable_streaming=not args.no_stream,
        max_turns=args.max_turns
    )
    
    # Run task
    agent = NanoAgent(config)
    result = await agent.run(args.task, args.session)
    
    # Output final result
    print("\n" + "="*50)
    print("TASK COMPLETED")
    print("="*50)
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

## Best Practices Summary

### 1. System Prompt Design
- Clear mission statement
- Explicit workflow steps
- Error recovery procedures
- Quality standards
- Completion criteria

### 2. Long-Running Tasks
- Use high max_turns (50-100)
- Implement retry logic
- Session management for continuity
- Progress monitoring
- Graceful error handling

### 3. Monitoring & Observability
- Comprehensive logging
- Execution metrics
- Tool usage tracking
- OpenAI trace integration
- Result persistence

### 4. Streaming Implementation
- Real-time progress updates
- Token-by-token streaming
- Tool execution visibility
- Handoff notifications
- UI integration support

### 5. Production Considerations
- Input validation with guardrails
- Safety checks
- Resource limits (timeouts)
- Proper error handling
- Configuration management

## Usage Examples

```bash
# Basic task
python nano_agent.py "Fix all linting errors in the project"

# With session for continuity
python nano_agent.py "Implement user authentication" --session auth_feature

# With specific model
python nano_agent.py "Refactor database queries for performance" --model gpt-4

# Without streaming for batch processing
python nano_agent.py "Generate comprehensive test suite" --no-stream

# Complex multi-step task
python nano_agent.py "Analyze codebase, identify performance bottlenecks, implement optimizations, and verify improvements with benchmarks"
```

## Integration with MCP Server

The nano-agent can be exposed as an MCP server tool:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("NanoAgentMCP")

@mcp.tool()
async def run_engineering_task(
    task: str,
    session_id: Optional[str] = None,
    model: str = "gpt-4-turbo"
) -> str:
    """Execute engineering task with nano-agent."""
    config = NanoAgentConfig(model=model)
    agent = NanoAgent(config)
    result = await agent.run(task, session_id)
    return result.final_output

if __name__ == "__main__":
    mcp.run()
```

This documentation provides a comprehensive foundation for building sophisticated, long-running engineering agents using the OpenAI Agents SDK. The nano-agent implementation demonstrates production-ready patterns for autonomous task completion with proper monitoring, error handling, and user feedback.