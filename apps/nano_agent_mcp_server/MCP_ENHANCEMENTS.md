# MCP Server Enhancement Proposals

## Current Limitations

The current MCP server implementation has limited configurability:
- Only `model` and `provider` parameters are exposed
- No temperature or other model settings control
- No tool restrictions or permissions system
- No session/conversation management
- No resource limits or quotas
- No client-specific configuration

## Proposed Enhancements

### 1. Enhanced Tool Parameters

Update `prompt_nano_agent` to accept comprehensive configuration:

```python
async def prompt_nano_agent(
    agentic_prompt: str,
    # Model Configuration
    model: str = DEFAULT_MODEL,
    provider: str = DEFAULT_PROVIDER,
    temperature: float = None,           # 0.0-2.0
    max_tokens: int = None,              # Response limit
    top_p: float = None,                 # Nucleus sampling
    frequency_penalty: float = None,     # Reduce repetition
    presence_penalty: float = None,      # Encourage new topics
    
    # Tool Restrictions
    allowed_tools: List[str] = None,     # Whitelist specific tools
    blocked_tools: List[str] = None,     # Blacklist specific tools
    allowed_paths: List[str] = None,     # Restrict file access
    blocked_paths: List[str] = None,     # Block sensitive paths
    read_only: bool = False,             # Disable write operations
    
    # Execution Limits
    max_turns: int = None,                # Limit agent iterations
    timeout_seconds: int = None,          # Total execution timeout
    max_file_size: int = None,           # Limit file sizes
    max_files: int = None,               # Limit files created/modified
    
    # Session Management
    session_id: str = None,              # Continue conversation
    clear_history: bool = False,         # Start fresh
    
    # Advanced Options
    system_prompt_override: str = None,  # Custom system prompt
    agent_personality: str = None,       # Use named personality
    output_format: str = "text",         # text/json/markdown
    verbose: bool = False,               # Detailed logging
    dry_run: bool = False,              # Preview without execution
    
    ctx: Any = None
) -> Dict[str, Any]:
```

### 2. MCP Resources for Configuration

Expose configuration options as MCP resources:

```python
@mcp.resource()
async def get_available_models() -> List[Dict]:
    """Return list of available models and providers."""
    return [
        {
            "provider": "openai",
            "models": ["gpt-5-mini", "gpt-5", "gpt-4o"],
            "default": "gpt-5-mini"
        },
        {
            "provider": "anthropic",
            "models": ["claude-3-haiku", "claude-sonnet-4"],
            "default": "claude-3-haiku"
        },
        {
            "provider": "ollama",
            "models": ["gpt-oss:20b", "gpt-oss:120b"],
            "default": "gpt-oss:20b"
        }
    ]

@mcp.resource()
async def get_tool_permissions() -> Dict:
    """Return current tool permission settings."""
    return {
        "available_tools": ["read_file", "write_file", "list_directory", "edit_file", "get_file_info"],
        "default_allowed": ["read_file", "list_directory", "get_file_info"],
        "sensitive_tools": ["write_file", "edit_file"]
    }

@mcp.resource()
async def get_server_capabilities() -> Dict:
    """Return server capabilities and limits."""
    return {
        "version": VERSION,
        "features": {
            "multi_provider": True,
            "session_management": True,
            "tool_restrictions": True,
            "path_restrictions": True,
            "custom_prompts": True
        },
        "limits": {
            "max_turns": 20,
            "max_timeout": 600,
            "max_file_size": 10485760,  # 10MB
            "max_tokens": 100000
        }
    }
```

### 3. Multiple Tool Variants

Offer different tool configurations for different use cases:

```python
@mcp.tool()
async def prompt_nano_agent_safe(
    agentic_prompt: str,
    model: str = DEFAULT_MODEL,
    ctx: Any = None
) -> Dict[str, Any]:
    """Execute agent in safe mode (read-only operations)."""
    return await prompt_nano_agent(
        agentic_prompt=agentic_prompt,
        model=model,
        read_only=True,
        allowed_tools=["read_file", "list_directory", "get_file_info"],
        ctx=ctx
    )

@mcp.tool()
async def prompt_nano_agent_restricted(
    agentic_prompt: str,
    allowed_directory: str,
    model: str = DEFAULT_MODEL,
    ctx: Any = None
) -> Dict[str, Any]:
    """Execute agent with path restrictions."""
    return await prompt_nano_agent(
        agentic_prompt=agentic_prompt,
        model=model,
        allowed_paths=[allowed_directory],
        ctx=ctx
    )

@mcp.tool()
async def prompt_nano_agent_analysis(
    agentic_prompt: str,
    model: str = DEFAULT_MODEL,
    ctx: Any = None
) -> Dict[str, Any]:
    """Execute agent for analysis only (no file modifications)."""
    return await prompt_nano_agent(
        agentic_prompt=agentic_prompt,
        model=model,
        allowed_tools=["read_file", "list_directory", "get_file_info"],
        output_format="markdown",
        ctx=ctx
    )
```

### 4. Client-Specific Configuration

Support client-specific settings via configuration file:

```json
// ~/.nano-cli/mcp-clients.json
{
  "clients": {
    "claude-desktop": {
      "default_model": "gpt-5-mini",
      "default_provider": "openai",
      "allowed_tools": ["read_file", "write_file", "list_directory"],
      "blocked_paths": ["/etc", "/System", "~/.ssh"],
      "max_turns": 15,
      "temperature": 0.7
    },
    "vscode": {
      "default_model": "gpt-oss:20b",
      "default_provider": "ollama",
      "allowed_tools": "all",
      "workspace_restricted": true,
      "temperature": 0.2
    },
    "custom-client": {
      "read_only": true,
      "allowed_tools": ["read_file", "list_directory"],
      "output_format": "json"
    }
  }
}
```

### 5. Tool Permission System

Implement granular tool permissions:

```python
class ToolPermissions:
    """Manage tool execution permissions."""
    
    def __init__(self, config: Dict[str, Any]):
        self.allowed_tools = set(config.get("allowed_tools", []))
        self.blocked_tools = set(config.get("blocked_tools", []))
        self.allowed_paths = config.get("allowed_paths", [])
        self.blocked_paths = config.get("blocked_paths", [])
        self.read_only = config.get("read_only", False)
        
    def check_tool_permission(self, tool_name: str, args: Dict) -> Tuple[bool, str]:
        """Check if tool execution is allowed."""
        # Check tool whitelist/blacklist
        if self.allowed_tools and tool_name not in self.allowed_tools:
            return False, f"Tool '{tool_name}' not in allowed list"
        
        if tool_name in self.blocked_tools:
            return False, f"Tool '{tool_name}' is blocked"
        
        # Check read-only mode
        if self.read_only and tool_name in ["write_file", "edit_file"]:
            return False, "Write operations disabled in read-only mode"
        
        # Check path restrictions
        if "file_path" in args:
            path = args["file_path"]
            if not self._check_path_permission(path):
                return False, f"Path '{path}' not allowed"
        
        return True, "Allowed"
```

### 6. Session and State Management

Add conversation persistence across MCP calls:

```python
class MCPSessionManager:
    """Manage sessions for MCP clients."""
    
    def __init__(self):
        self.sessions = {}
        
    async def get_or_create_session(
        self, 
        session_id: str, 
        client_id: str
    ) -> Session:
        """Get existing session or create new one."""
        key = f"{client_id}:{session_id}"
        
        if key not in self.sessions:
            self.sessions[key] = Session(
                session_id=session_id,
                client_id=client_id,
                created_at=datetime.now(),
                conversation=[]
            )
        
        return self.sessions[key]
    
    async def add_to_history(
        self,
        session_id: str,
        client_id: str,
        user_msg: str,
        assistant_msg: str
    ):
        """Add exchange to session history."""
        session = await self.get_or_create_session(session_id, client_id)
        session.conversation.append(ChatMessage(role="user", content=user_msg))
        session.conversation.append(ChatMessage(role="assistant", content=assistant_msg))
```

### 7. Resource Limits and Quotas

Implement usage limits per client:

```python
class ResourceQuota:
    """Track and enforce resource quotas."""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.daily_tokens = 0
        self.daily_requests = 0
        self.monthly_tokens = 0
        self.monthly_requests = 0
        
    def check_quota(self, estimated_tokens: int) -> Tuple[bool, str]:
        """Check if operation is within quota."""
        daily_limit = 100000  # tokens per day
        monthly_limit = 1000000  # tokens per month
        
        if self.daily_tokens + estimated_tokens > daily_limit:
            return False, "Daily token limit exceeded"
        
        if self.monthly_tokens + estimated_tokens > monthly_limit:
            return False, "Monthly token limit exceeded"
        
        return True, "Within quota"
```

### 8. Streaming Responses

Support streaming for real-time feedback:

```python
@mcp.tool()
async def prompt_nano_agent_stream(
    agentic_prompt: str,
    model: str = DEFAULT_MODEL,
    ctx: Any = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream agent execution updates."""
    
    async for update in execute_agent_streaming(agentic_prompt, model):
        yield {
            "type": update.type,  # "tool_call", "thinking", "result"
            "content": update.content,
            "timestamp": update.timestamp
        }
```

### 9. Batch Operations

Support multiple prompts in a single call:

```python
@mcp.tool()
async def prompt_nano_agent_batch(
    prompts: List[Dict[str, Any]],
    parallel: bool = False,
    ctx: Any = None
) -> List[Dict[str, Any]]:
    """Execute multiple prompts in batch."""
    
    if parallel:
        tasks = [
            prompt_nano_agent(**prompt, ctx=ctx)
            for prompt in prompts
        ]
        return await asyncio.gather(*tasks)
    else:
        results = []
        for prompt in prompts:
            result = await prompt_nano_agent(**prompt, ctx=ctx)
            results.append(result)
        return results
```

### 10. Advanced Error Handling

Provide detailed error information:

```python
class MCPError(Exception):
    """Enhanced MCP error with details."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        details: Dict[str, Any] = None,
        suggestions: List[str] = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.suggestions = suggestions or []
    
    def to_dict(self) -> Dict:
        return {
            "error": str(self),
            "error_code": self.error_code,
            "details": self.details,
            "suggestions": self.suggestions
        }

# Usage example
if not api_key:
    raise MCPError(
        message="API key not configured",
        error_code="CONFIG_ERROR",
        details={"provider": provider, "required_env": "OPENAI_API_KEY"},
        suggestions=[
            "Set OPENAI_API_KEY environment variable",
            "Pass api_key parameter",
            "Use local provider like Ollama"
        ]
    )
```

## Implementation Priority

### Phase 1: Core Enhancements (High Priority)
1. ✅ Add temperature and max_tokens parameters
2. ✅ Implement allowed_tools/blocked_tools
3. ✅ Add read_only mode
4. ✅ Path restrictions (allowed_paths/blocked_paths)

### Phase 2: Client Features (Medium Priority)
5. Session management
6. Client-specific configuration
7. Resource quotas
8. Multiple tool variants

### Phase 3: Advanced Features (Low Priority)
9. Streaming responses
10. Batch operations
11. Advanced error handling
12. Custom system prompts

## Example Usage

### Claude Desktop requesting specific model and settings:
```python
result = await prompt_nano_agent(
    agentic_prompt="Analyze this codebase",
    model="gpt-5",
    provider="openai",
    temperature=0.2,
    read_only=True,
    allowed_paths=["./src"],
    output_format="markdown"
)
```

### VS Code with restrictions:
```python
result = await prompt_nano_agent(
    agentic_prompt="Fix the bug in auth.py",
    model="gpt-oss:20b",
    provider="ollama",
    allowed_tools=["read_file", "edit_file"],
    allowed_paths=["./src/auth"],
    max_turns=10
)
```

### Safe exploration mode:
```python
result = await prompt_nano_agent_safe(
    agentic_prompt="What does this project do?",
    model="claude-3-haiku"
)
```

## Benefits

1. **Security**: Fine-grained control over what the agent can access and modify
2. **Flexibility**: Different clients can have different permissions and settings
3. **Cost Control**: Resource quotas prevent runaway usage
4. **User Experience**: Streaming and batch operations improve responsiveness
5. **Compatibility**: Works with any MCP client that can pass parameters
6. **Safety**: Read-only and restricted modes for exploration
7. **Customization**: Client-specific defaults and configurations

## Testing Strategy

1. **Unit Tests**: Test each permission check and restriction
2. **Integration Tests**: Test with different client configurations
3. **Security Tests**: Attempt to bypass restrictions
4. **Performance Tests**: Measure impact of restrictions on performance
5. **Client Tests**: Test with Claude Desktop, VS Code, and custom clients