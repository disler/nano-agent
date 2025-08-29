"""
Data types for Nano Agent MCP Server.

All request/response models using Pydantic for validation and type safety.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any, List
from datetime import datetime


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