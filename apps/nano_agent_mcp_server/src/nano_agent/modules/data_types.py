"""
Data types for Nano Agent MCP Server.

All request/response models using Pydantic for validation and type safety.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path


# Tool Permission Models

class ToolPermissions(BaseModel):
    """Configuration for tool execution permissions."""
    allowed_tools: Optional[List[str]] = Field(
        default=None,
        description="Whitelist of allowed tools"
    )
    blocked_tools: Optional[List[str]] = Field(
        default=None,
        description="Blacklist of blocked tools"
    )
    allowed_paths: Optional[List[str]] = Field(
        default=None,
        description="Whitelist of allowed path patterns"
    )
    blocked_paths: Optional[List[str]] = Field(
        default=None,
        description="Blacklist of blocked path patterns"
    )
    read_only: bool = Field(
        default=False,
        description="If True, disable write operations"
    )
    
    def check_tool_permission(self, tool_name: str, args: Dict[str, Any] = None) -> tuple[bool, str]:
        """Check if a tool execution is allowed.
        
        Args:
            tool_name: Name of the tool to check
            args: Tool arguments (used for path validation)
            
        Returns:
            (allowed: bool, reason: str) tuple
        """
        args = args or {}
        
        # Check tool whitelist
        if self.allowed_tools and tool_name not in self.allowed_tools:
            return False, f"Tool '{tool_name}' not in allowed list: {self.allowed_tools}"
        
        # Check tool blacklist
        if self.blocked_tools and tool_name in self.blocked_tools:
            return False, f"Tool '{tool_name}' is blocked"
        
        # Check read-only mode
        if self.read_only and tool_name in ["write_file", "edit_file"]:
            return False, f"Write operations disabled in read-only mode (tool: {tool_name})"
        
        # Check path restrictions for file operations
        file_path = args.get("file_path") or args.get("directory_path")
        if file_path:
            allowed, reason = self._check_path_permission(file_path)
            if not allowed:
                return False, reason
        
        return True, "Allowed"
    
    def _check_path_permission(self, file_path: str) -> tuple[bool, str]:
        """Check if a file path is allowed.
        
        Args:
            file_path: Path to check
            
        Returns:
            (allowed: bool, reason: str) tuple
        """
        try:
            # Convert to Path object for consistent handling
            path = Path(file_path).resolve()
            path_str = str(path)
            
            # Check blocked paths first (takes precedence)
            if self.blocked_paths:
                for blocked_pattern in self.blocked_paths:
                    blocked_path = Path(blocked_pattern).resolve()
                    
                    # Check if path is under blocked directory or matches pattern
                    if path_str.startswith(str(blocked_path)):
                        return False, f"Path '{file_path}' is blocked by pattern '{blocked_pattern}'"
                    
                    # Simple pattern matching for wildcards
                    if "*" in blocked_pattern and self._matches_pattern(path_str, blocked_pattern):
                        return False, f"Path '{file_path}' matches blocked pattern '{blocked_pattern}'"
            
            # Check allowed paths if specified
            if self.allowed_paths:
                allowed = False
                for allowed_pattern in self.allowed_paths:
                    allowed_path = Path(allowed_pattern).resolve()
                    
                    # Check if path is under allowed directory or matches pattern
                    if path_str.startswith(str(allowed_path)):
                        allowed = True
                        break
                    
                    # Simple pattern matching for wildcards
                    if "*" in allowed_pattern and self._matches_pattern(path_str, allowed_pattern):
                        allowed = True
                        break
                
                if not allowed:
                    return False, f"Path '{file_path}' not in allowed paths: {self.allowed_paths}"
            
            return True, "Path allowed"
            
        except Exception as e:
            return False, f"Error checking path permission: {str(e)}"
    
    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Simple wildcard pattern matching.
        
        Args:
            path: File path to check
            pattern: Pattern with optional wildcards (*)
            
        Returns:
            True if path matches pattern
        """
        try:
            import fnmatch
            return fnmatch.fnmatch(path, pattern)
        except ImportError:
            # Fallback to simple contains check
            return pattern.replace("*", "") in path


# MCP Tool Request/Response Models

class ChatMessage(BaseModel):
    """A single message in a chat conversation."""
    role: Literal["user", "assistant", "system"] = Field(
        description="The role of the message sender"
    )
    content: str = Field(
        description="The content of the message"
    )


class PromptNanoAgentRequest(BaseModel):
    """Request model for prompt_nano_agent MCP tool."""
    agentic_prompt: str = Field(
        ...,
        description="Natural language description of the work to be done",
        min_length=1,
        max_length=10000
    )
    model: str = Field(
        default="gpt-5-mini",
        description="LLM model to use for the agent"
    )
    provider: Literal["openai", "anthropic", "ollama", "lmstudio", "ollama-native"] = Field(
        default="openai",
        description="LLM provider for the agent"
    )
    api_base: Optional[str] = Field(
        default=None,
        description="Optional API base URL (overrides environment variables)"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="Optional API key (overrides environment variables)"
    )
    chat_history: Optional[List[ChatMessage]] = Field(
        default=None,
        description="Optional chat history for maintaining conversation context"
    )
    agent_name: Optional[str] = Field(
        default=None,
        description="Optional agent personality to use"
    )
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Model temperature (0.0-2.0)"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        gt=0,
        description="Maximum response tokens"
    )
    allowed_tools: Optional[List[str]] = Field(
        default=None,
        description="List of tools the agent is allowed to use (whitelist)"
    )
    blocked_tools: Optional[List[str]] = Field(
        default=None,
        description="List of tools the agent is not allowed to use (blacklist)"
    )
    allowed_paths: Optional[List[str]] = Field(
        default=None,
        description="List of path patterns the agent can access (whitelist)"
    )
    blocked_paths: Optional[List[str]] = Field(
        default=None,
        description="List of path patterns the agent cannot access (blacklist)"
    )
    read_only: bool = Field(
        default=False,
        description="If True, disable all write operations (write_file, edit_file)"
    )


class PromptNanoAgentResponse(BaseModel):
    """Response model for prompt_nano_agent MCP tool."""
    success: bool = Field(description="Whether the agent completed successfully")
    result: Optional[str] = Field(default=None, description="Agent execution result")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional execution metadata"
    )
    execution_time_seconds: Optional[float] = Field(
        default=None,
        description="Total execution time"
    )
    permissions_used: Optional[ToolPermissions] = Field(
        default=None,
        description="Tool permissions that were enforced during execution"
    )


# Internal Agent Tool Models

class ReadFileRequest(BaseModel):
    """Request model for read_file agent tool."""
    file_path: str = Field(
        ...,
        description="Path to the file to read",
        min_length=1
    )
    encoding: str = Field(
        default="utf-8",
        description="File encoding"
    )


class ReadFileResponse(BaseModel):
    """Response model for read_file agent tool."""
    content: Optional[str] = Field(default=None, description="File contents")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    file_size_bytes: Optional[int] = Field(default=None, description="File size")
    last_modified: Optional[datetime] = Field(default=None, description="Last modification time")


class CreateFileRequest(BaseModel):
    """Request model for create_file agent tool."""
    file_path: str = Field(
        ...,
        description="Path where the file should be created",
        min_length=1
    )
    content: str = Field(
        ...,
        description="Content to write to the file"
    )
    encoding: str = Field(
        default="utf-8",
        description="File encoding"
    )
    overwrite: bool = Field(
        default=False,
        description="Whether to overwrite if file exists"
    )


class CreateFileResponse(BaseModel):
    """Response model for create_file agent tool."""
    success: bool = Field(description="Whether file was created successfully")
    file_path: str = Field(description="Path to the created file")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    bytes_written: Optional[int] = Field(default=None, description="Number of bytes written")



# Agent Configuration Models

class AgentConfig(BaseModel):
    """Configuration for the nano agent."""
    model: str = Field(description="LLM model identifier")
    provider: Literal["openai", "anthropic", "ollama"] = Field(description="LLM provider")
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=4000,
        gt=0,
        description="Maximum tokens in response"
    )
    timeout_seconds: int = Field(
        default=300,
        gt=0,
        description="Execution timeout"
    )


# Execution Tracking Models

class ToolCall(BaseModel):
    """Record of a single tool call."""
    tool_name: str = Field(description="Name of the tool called")
    arguments: Dict[str, Any] = Field(description="Arguments passed to the tool")
    result: Optional[Any] = Field(default=None, description="Tool execution result")
    error: Optional[str] = Field(default=None, description="Error if tool failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the tool was called")
    duration_seconds: Optional[float] = Field(default=None, description="Execution duration")


class AgentExecution(BaseModel):
    """Complete record of an agent execution."""
    prompt: str = Field(description="Original prompt")
    config: AgentConfig = Field(description="Agent configuration used")
    tool_calls: List[ToolCall] = Field(
        default_factory=list,
        description="All tool calls made during execution"
    )
    final_result: Optional[str] = Field(default=None, description="Final execution result")
    total_tokens_used: Optional[int] = Field(default=None, description="Total tokens consumed")
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(default=None)
    success: bool = Field(default=False, description="Whether execution completed successfully")
    error: Optional[str] = Field(default=None, description="Error message if failed")