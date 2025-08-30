#!/usr/bin/env python
"""Nano Agent MCP Server - Main entry point."""

# Apply typing fixes FIRST before any other imports that might use OpenAI SDK
from .modules import typing_fix

import logging
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables from .env file
load_dotenv()

# Import our nano agent tool and additional MCP tools
from .modules.nano_agent import prompt_nano_agent
from .mcp_tools import (
    get_session_info,
    list_sessions,
    clear_old_sessions,
    get_available_models,
    get_server_capabilities
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the MCP server instance
mcp = FastMCP(
    name="nano-agent",
    instructions="""
    A powerful MCP server that bridges Model Context Protocol with OpenAI's Agent SDK.
    
    This server enables autonomous agent execution through natural language prompts,
    allowing clients to describe work in plain English and have it completed by
    an AI agent with access to file system tools.
    
    Features:
    - Multi-provider LLM support (OpenAI, Anthropic, Ollama)
    - Conversation persistence across sessions
    - Fine-grained tool and path permissions
    - Read-only mode for safe exploration
    - Hooks system for customization
    - Temperature and token limit control
    
    Main tools:
    - prompt_nano_agent: Execute autonomous agent with full configuration options
    - get_session_info: Get information about a specific session
    - list_sessions: List all sessions for the client
    - clear_old_sessions: Clean up old session data
    - get_available_models: List available models and providers
    - get_server_capabilities: Get server features and limitations
    """
)

# Register all tools
mcp.tool()(prompt_nano_agent)
mcp.tool()(get_session_info)
mcp.tool()(list_sessions)
mcp.tool()(clear_old_sessions)
mcp.tool()(get_available_models)
mcp.tool()(get_server_capabilities)


def run():
    """Entry point for the nano-agent command."""
    try:
        logger.info("Starting Nano Agent MCP Server...")
        # FastMCP.run() handles its own async context with anyio
        # Don't wrap it in asyncio.run()
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    run()