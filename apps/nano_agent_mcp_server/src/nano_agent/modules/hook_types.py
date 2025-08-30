"""
Hook types and data structures for nano-agent hooks system.

Defines hook events, data structures, and configuration models.
"""

from enum import Enum
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from datetime import datetime


class HookEvent(Enum):
    """Hook event types that can trigger user-defined scripts."""
    
    # Agent lifecycle hooks
    PRE_AGENT_START = "pre_agent_start"          # Before agent initialization
    POST_AGENT_COMPLETE = "post_agent_complete"  # After agent completes
    AGENT_ERROR = "agent_error"                  # When agent encounters error
    
    # Tool execution hooks
    PRE_TOOL_USE = "pre_tool_use"               # Before any tool execution
    POST_TOOL_USE = "post_tool_use"             # After successful tool execution
    TOOL_ERROR = "tool_error"                   # When tool execution fails
    
    # Session hooks (CLI only)
    SESSION_START = "session_start"              # When session begins/resumes
    SESSION_END = "session_end"                  # When session terminates
    SESSION_SAVE = "session_save"                # Before saving session
    
    # Prompt hooks
    USER_PROMPT_SUBMIT = "user_prompt_submit"    # Before processing user prompt
    AGENT_RESPONSE = "agent_response"            # After agent generates response
    
    # MCP-specific events (when running as MCP server)
    MCP_REQUEST_RECEIVED = "mcp_request_received"  # When MCP request arrives
    MCP_RESPONSE_READY = "mcp_response_ready"      # Before sending MCP response


@dataclass
class HookEventData:
    """Data passed to hook scripts via stdin as JSON."""
    
    # Event identification
    event: str                           # Event type (e.g., "pre_tool_use")
    timestamp: str                       # ISO format timestamp
    
    # Execution context
    context: str                         # "cli" or "mcp"
    working_dir: str                     # Current working directory
    project_dir: Optional[str] = None   # Project root if detected
    
    # Session information (if applicable)
    session_id: Optional[str] = None     # Current session ID
    message_count: Optional[int] = None  # Messages in current session
    
    # Agent configuration
    model: Optional[str] = None          # Current model (e.g., "gpt-oss:20b")
    provider: Optional[str] = None       # Current provider (e.g., "ollama")
    temperature: Optional[float] = None  # Model temperature
    max_tokens: Optional[int] = None     # Max tokens setting
    
    # Prompt/Response data
    prompt: Optional[str] = None          # User prompt
    agent_response: Optional[str] = None  # Agent's response
    
    # Tool-specific data
    tool_name: Optional[str] = None      # Tool being executed
    tool_args: Optional[Dict] = None     # Tool arguments
    tool_result: Optional[Any] = None    # Tool execution result
    error: Optional[str] = None          # Error message if applicable
    
    # Token usage (if available)
    token_usage: Optional[Dict] = None   # Token usage statistics
    execution_time: Optional[float] = None  # Execution time in seconds
    
    # MCP-specific fields (when running as MCP server)
    mcp_client: Optional[str] = None     # Client identifier (e.g., "claude-desktop")
    mcp_request_id: Optional[str] = None # Unique MCP request ID
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class HookExecutionResult:
    """Result from executing a single hook."""
    
    hook_name: str                       # Name of the hook
    success: bool                        # Whether execution succeeded
    exit_code: int                       # Process exit code
    stdout: str = ""                     # Standard output
    stderr: str = ""                     # Standard error
    execution_time: float = 0.0          # Execution time in seconds
    blocked: bool = False                # Whether hook blocked further execution
    error: Optional[str] = None          # Error message if failed
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class HookResult:
    """Aggregated result from executing hooks for an event."""
    
    event: HookEvent                     # Event that triggered hooks
    hooks_executed: int                  # Number of hooks executed
    results: List[HookExecutionResult]   # Individual hook results
    blocked: bool = False                # Whether any hook blocked execution
    total_time: float = 0.0              # Total execution time
    
    @property
    def all_succeeded(self) -> bool:
        """Check if all hooks succeeded."""
        return all(r.success for r in self.results)
    
    @property
    def blocking_reason(self) -> Optional[str]:
        """Get reason if execution was blocked."""
        for result in self.results:
            if result.blocked:
                return f"{result.hook_name}: {result.stderr or result.error or 'Blocked'}"
        return None


@dataclass
class HookConfig:
    """Configuration for a single hook."""
    
    name: str                            # Hook name
    command: str                         # Command to execute
    event: str                           # Event that triggers this hook
    blocking: bool = False               # Whether hook can block execution
    timeout: int = 60                    # Timeout in seconds
    enabled: bool = True                 # Whether hook is enabled
    contexts: List[str] = None           # Contexts where hook runs ("cli", "mcp", or both)
    
    # Optional matching criteria
    matcher: Optional[Dict] = None       # Tool names, patterns, etc.
    condition: Optional[str] = None      # Additional condition expression
    
    def __post_init__(self):
        """Set defaults after initialization."""
        if self.contexts is None:
            self.contexts = ["cli", "mcp"]  # Run in both contexts by default
    
    def matches(self, data: HookEventData) -> bool:
        """Check if hook should run based on matcher and condition."""
        # Check context
        if data.context not in self.contexts:
            return False
        
        # Check matcher criteria
        if self.matcher:
            # Tool name matching
            if "tool" in self.matcher and data.tool_name:
                tools = self.matcher["tool"]
                if isinstance(tools, str):
                    tools = [tools]
                if data.tool_name not in tools:
                    return False
            
            # Pattern matching (for file paths)
            if "pattern" in self.matcher and data.tool_args:
                import re
                pattern = self.matcher["pattern"]
                # Check file_path or filename in tool args
                file_path = data.tool_args.get("file_path") or data.tool_args.get("filename", "")
                if not re.match(pattern, file_path):
                    return False
        
        # Check condition (simplified - in production would use safe expression evaluator)
        if self.condition:
            # For now, just check simple conditions like "{{context:cli}}"
            if "{{context:" in self.condition:
                expected_context = self.condition.split("{{context:")[1].split("}}")[0]
                if data.context != expected_context:
                    return False
        
        return True


@dataclass
class HooksConfiguration:
    """Complete hooks configuration."""
    
    version: str = "1.0"
    enabled: bool = True
    timeout_seconds: int = 60
    parallel_execution: bool = True
    hooks: Dict[str, List[HookConfig]] = None
    
    def __post_init__(self):
        """Initialize hooks dictionary."""
        if self.hooks is None:
            self.hooks = {}
    
    @classmethod
    def from_dict(cls, data: Dict) -> "HooksConfiguration":
        """Create configuration from dictionary."""
        config = cls(
            version=data.get("version", "1.0"),
            enabled=data.get("enabled", True),
            timeout_seconds=data.get("timeout_seconds", 60),
            parallel_execution=data.get("parallel_execution", True)
        )
        
        # Parse hooks
        hooks_data = data.get("hooks", {})
        for event_name, hook_list in hooks_data.items():
            config.hooks[event_name] = []
            for hook_data in hook_list:
                hook_config = HookConfig(
                    name=hook_data["name"],
                    command=hook_data["command"],
                    event=event_name,
                    blocking=hook_data.get("blocking", False),
                    timeout=hook_data.get("timeout", config.timeout_seconds),
                    enabled=hook_data.get("enabled", True),
                    contexts=hook_data.get("contexts", ["cli", "mcp"]),
                    matcher=hook_data.get("matcher"),
                    condition=hook_data.get("condition")
                )
                config.hooks[event_name].append(hook_config)
        
        return config