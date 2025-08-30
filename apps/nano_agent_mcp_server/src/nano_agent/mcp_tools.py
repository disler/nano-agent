"""
Additional MCP tools for session and configuration management.
"""

from typing import Dict, List, Any, Optional
from .modules.mcp_session_manager import MCPSessionManager
from .modules.constants import AVAILABLE_MODELS, PROVIDER_REQUIREMENTS


async def get_session_info(
    session_id: str,
    ctx: Any = None
) -> Dict[str, Any]:
    """
    Get information about a specific session.
    
    Args:
        session_id: The session ID to get information for
        ctx: MCP context (automatically injected)
    
    Returns:
        Dictionary containing session information
    """
    if not ctx:
        return {
            "success": False,
            "error": "Session management only available in MCP context"
        }
    
    try:
        client_id = getattr(ctx, 'client_id', None) or getattr(ctx, 'client_name', None) or "mcp-client"
        session_manager = MCPSessionManager()
        
        session_info = await session_manager.get_session_info(
            client_id=client_id,
            session_id=session_id
        )
        
        if session_info:
            return {
                "success": True,
                "session_info": session_info
            }
        else:
            return {
                "success": False,
                "error": f"Session '{session_id}' not found"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting session info: {str(e)}"
        }


async def list_sessions(
    limit: int = 10,
    ctx: Any = None
) -> Dict[str, Any]:
    """
    List all sessions for the current client.
    
    Args:
        limit: Maximum number of sessions to return (default: 10)
        ctx: MCP context (automatically injected)
    
    Returns:
        Dictionary containing list of sessions
    """
    if not ctx:
        return {
            "success": False,
            "error": "Session management only available in MCP context"
        }
    
    try:
        client_id = getattr(ctx, 'client_id', None) or getattr(ctx, 'client_name', None) or "mcp-client"
        session_manager = MCPSessionManager()
        
        sessions = await session_manager.list_client_sessions(
            client_id=client_id,
            limit=limit
        )
        
        return {
            "success": True,
            "sessions": sessions,
            "count": len(sessions)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error listing sessions: {str(e)}"
        }


async def clear_old_sessions(
    days: int = 30,
    ctx: Any = None
) -> Dict[str, Any]:
    """
    Clear old sessions older than specified days.
    
    Args:
        days: Number of days to keep sessions (default: 30)
        ctx: MCP context (automatically injected)
    
    Returns:
        Dictionary containing operation result
    """
    if not ctx:
        return {
            "success": False,
            "error": "Session management only available in MCP context"
        }
    
    try:
        session_manager = MCPSessionManager()
        await session_manager.clear_old_sessions(days=days)
        
        return {
            "success": True,
            "message": f"Cleared sessions older than {days} days"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error clearing sessions: {str(e)}"
        }


async def get_available_models() -> Dict[str, Any]:
    """
    Get list of available models and providers.
    
    Returns:
        Dictionary containing available models by provider
    """
    try:
        models_by_provider = {}
        
        for provider, models in AVAILABLE_MODELS.items():
            if provider in PROVIDER_REQUIREMENTS:
                models_by_provider[provider] = {
                    "models": list(models.keys()),
                    "default": next(iter(models.keys())),
                    "requirements": PROVIDER_REQUIREMENTS[provider]
                }
        
        return {
            "success": True,
            "providers": models_by_provider,
            "total_models": sum(len(info["models"]) for info in models_by_provider.values())
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting available models: {str(e)}"
        }


async def get_server_capabilities() -> Dict[str, Any]:
    """
    Get server capabilities and limitations.
    
    Returns:
        Dictionary containing server capabilities
    """
    try:
        from .modules.constants import VERSION, MAX_AGENT_TURNS, MAX_TOKENS
        
        return {
            "success": True,
            "capabilities": {
                "version": VERSION,
                "features": {
                    "multi_provider": True,
                    "session_management": True,
                    "tool_restrictions": True,
                    "path_restrictions": True,
                    "conversation_history": True,
                    "hooks_system": True,
                    "read_only_mode": True
                },
                "limits": {
                    "max_turns": MAX_AGENT_TURNS,
                    "max_tokens": MAX_TOKENS,
                    "session_history": 100,  # messages
                    "max_file_size": 10485760,  # 10MB
                    "timeout_seconds": 600
                },
                "available_tools": [
                    "read_file",
                    "write_file", 
                    "list_directory",
                    "get_file_info",
                    "edit_file"
                ]
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting server capabilities: {str(e)}"
        }