"""
MCP Session Manager for conversation persistence.

Manages sessions for MCP clients to maintain conversation context
across multiple tool calls.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict

from .data_types import ChatMessage

logger = logging.getLogger(__name__)


@dataclass
class MCPSession:
    """Represents an MCP client session."""
    session_id: str
    client_id: str
    created_at: datetime
    last_updated: datetime
    conversation: List[ChatMessage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Session settings (can be persisted across calls)
    model: Optional[str] = None
    provider: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    
    # Permission settings
    allowed_tools: Optional[List[str]] = None
    blocked_tools: Optional[List[str]] = None
    allowed_paths: Optional[List[str]] = None
    blocked_paths: Optional[List[str]] = None
    read_only: bool = False
    
    # Usage tracking
    total_tokens: int = 0
    total_requests: int = 0
    total_cost: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "client_id": self.client_id,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "conversation": [
                {"role": msg.role, "content": msg.content}
                for msg in self.conversation
            ],
            "metadata": self.metadata,
            "model": self.model,
            "provider": self.provider,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "allowed_tools": self.allowed_tools,
            "blocked_tools": self.blocked_tools,
            "allowed_paths": self.allowed_paths,
            "blocked_paths": self.blocked_paths,
            "read_only": self.read_only,
            "total_tokens": self.total_tokens,
            "total_requests": self.total_requests,
            "total_cost": self.total_cost
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "MCPSession":
        """Create session from dictionary."""
        conversation = [
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in data.get("conversation", [])
        ]
        
        return cls(
            session_id=data["session_id"],
            client_id=data["client_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            conversation=conversation,
            metadata=data.get("metadata", {}),
            model=data.get("model"),
            provider=data.get("provider"),
            temperature=data.get("temperature"),
            max_tokens=data.get("max_tokens"),
            allowed_tools=data.get("allowed_tools"),
            blocked_tools=data.get("blocked_tools"),
            allowed_paths=data.get("allowed_paths"),
            blocked_paths=data.get("blocked_paths"),
            read_only=data.get("read_only", False),
            total_tokens=data.get("total_tokens", 0),
            total_requests=data.get("total_requests", 0),
            total_cost=data.get("total_cost", 0.0)
        )


class MCPSessionManager:
    """Manages MCP client sessions with persistence."""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize session manager.
        
        Args:
            storage_dir: Directory to store session data (default: ~/.nano-cli/mcp-sessions)
        """
        self.storage_dir = storage_dir or Path.home() / ".nano-cli" / "mcp-sessions"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for active sessions
        self.sessions: Dict[str, MCPSession] = {}
        
        # Load existing sessions on startup
        self._load_sessions()
        
        logger.info(f"MCP SessionManager initialized with storage: {self.storage_dir}")
    
    def _load_sessions(self):
        """Load existing sessions from disk."""
        session_files = self.storage_dir.glob("*.json")
        loaded_count = 0
        
        for session_file in session_files:
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                session = MCPSession.from_dict(data)
                
                # Only load recent sessions (last 7 days)
                if datetime.now() - session.last_updated < timedelta(days=7):
                    key = self._make_key(session.client_id, session.session_id)
                    self.sessions[key] = session
                    loaded_count += 1
            except Exception as e:
                logger.warning(f"Failed to load session from {session_file}: {e}")
        
        if loaded_count > 0:
            logger.info(f"Loaded {loaded_count} active sessions from disk")
    
    def _make_key(self, client_id: str, session_id: str) -> str:
        """Create unique key for session storage."""
        return f"{client_id}:{session_id}"
    
    def _save_session(self, session: MCPSession):
        """Save session to disk."""
        try:
            session_file = self.storage_dir / f"{session.client_id}_{session.session_id}.json"
            with open(session_file, 'w') as f:
                json.dump(session.to_dict(), f, indent=2)
            logger.debug(f"Saved session {session.session_id} to disk")
        except Exception as e:
            logger.error(f"Failed to save session {session.session_id}: {e}")
    
    async def get_or_create_session(
        self,
        client_id: str,
        session_id: Optional[str] = None,
        create_new: bool = False
    ) -> MCPSession:
        """Get existing session or create a new one.
        
        Args:
            client_id: Unique identifier for the MCP client
            session_id: Optional session ID to continue
            create_new: Force creation of new session
            
        Returns:
            MCPSession object
        """
        # Generate session ID if not provided
        if not session_id or create_new:
            session_id = f"mcp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{client_id[:8]}"
        
        key = self._make_key(client_id, session_id)
        
        # Return existing session if found and not forcing new
        if key in self.sessions and not create_new:
            session = self.sessions[key]
            session.last_updated = datetime.now()
            logger.debug(f"Returning existing session {session_id} for client {client_id}")
            return session
        
        # Create new session
        session = MCPSession(
            session_id=session_id,
            client_id=client_id,
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        self.sessions[key] = session
        self._save_session(session)
        logger.info(f"Created new session {session_id} for client {client_id}")
        
        return session
    
    async def update_session(
        self,
        client_id: str,
        session_id: str,
        user_prompt: str,
        agent_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Update session with new conversation exchange.
        
        Args:
            client_id: Client identifier
            session_id: Session identifier
            user_prompt: User's prompt
            agent_response: Agent's response
            metadata: Optional metadata (tokens, cost, etc.)
        """
        key = self._make_key(client_id, session_id)
        
        if key not in self.sessions:
            logger.warning(f"Session {session_id} not found for update")
            return
        
        session = self.sessions[key]
        
        # Add conversation exchange
        session.conversation.append(ChatMessage(role="user", content=user_prompt))
        session.conversation.append(ChatMessage(role="assistant", content=agent_response))
        
        # Update metadata
        session.last_updated = datetime.now()
        session.total_requests += 1
        
        if metadata:
            # Update token usage
            if "token_usage" in metadata:
                tokens = metadata["token_usage"].get("total_tokens", 0)
                session.total_tokens += tokens
                
                # Update cost if available
                if "total_cost" in metadata["token_usage"]:
                    cost_str = metadata["token_usage"]["total_cost"]
                    # Parse cost string like "$0.0066"
                    if cost_str.startswith("$"):
                        session.total_cost += float(cost_str[1:])
            
            # Store execution metadata
            if "execution_time_seconds" in metadata:
                if "metadata" not in session.metadata:
                    session.metadata["execution_times"] = []
                session.metadata["execution_times"].append(metadata["execution_time_seconds"])
        
        # Limit conversation history (keep last 50 exchanges)
        if len(session.conversation) > 100:  # 50 exchanges = 100 messages
            session.conversation = session.conversation[-100:]
        
        # Save to disk
        self._save_session(session)
        
        logger.debug(f"Updated session {session_id} with new exchange")
    
    async def get_conversation_context(
        self,
        client_id: str,
        session_id: str,
        max_messages: int = 20
    ) -> List[ChatMessage]:
        """Get conversation history for context.
        
        Args:
            client_id: Client identifier
            session_id: Session identifier
            max_messages: Maximum number of messages to return
            
        Returns:
            List of chat messages for context
        """
        key = self._make_key(client_id, session_id)
        
        if key not in self.sessions:
            return []
        
        session = self.sessions[key]
        
        # Return last N messages
        if len(session.conversation) > max_messages:
            return session.conversation[-max_messages:]
        
        return session.conversation
    
    async def update_session_settings(
        self,
        client_id: str,
        session_id: str,
        **settings
    ):
        """Update session settings (model, permissions, etc.).
        
        Args:
            client_id: Client identifier
            session_id: Session identifier
            **settings: Settings to update (model, provider, temperature, etc.)
        """
        key = self._make_key(client_id, session_id)
        
        if key not in self.sessions:
            logger.warning(f"Session {session_id} not found for settings update")
            return
        
        session = self.sessions[key]
        
        # Update allowed settings
        allowed_settings = [
            "model", "provider", "temperature", "max_tokens",
            "allowed_tools", "blocked_tools", "allowed_paths", 
            "blocked_paths", "read_only"
        ]
        
        for setting, value in settings.items():
            if setting in allowed_settings and value is not None:
                setattr(session, setting, value)
                logger.debug(f"Updated session {session_id} setting {setting} = {value}")
        
        session.last_updated = datetime.now()
        self._save_session(session)
    
    async def get_session_info(
        self,
        client_id: str,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get session information.
        
        Args:
            client_id: Client identifier
            session_id: Session identifier
            
        Returns:
            Session information dictionary or None if not found
        """
        key = self._make_key(client_id, session_id)
        
        if key not in self.sessions:
            return None
        
        session = self.sessions[key]
        
        return {
            "session_id": session.session_id,
            "client_id": session.client_id,
            "created_at": session.created_at.isoformat(),
            "last_updated": session.last_updated.isoformat(),
            "message_count": len(session.conversation),
            "total_requests": session.total_requests,
            "total_tokens": session.total_tokens,
            "total_cost": session.total_cost,
            "model": session.model,
            "provider": session.provider
        }
    
    async def list_client_sessions(
        self,
        client_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """List all sessions for a client.
        
        Args:
            client_id: Client identifier
            limit: Maximum number of sessions to return
            
        Returns:
            List of session information dictionaries
        """
        client_sessions = []
        
        for key, session in self.sessions.items():
            if session.client_id == client_id:
                client_sessions.append({
                    "session_id": session.session_id,
                    "created_at": session.created_at.isoformat(),
                    "last_updated": session.last_updated.isoformat(),
                    "message_count": len(session.conversation),
                    "total_requests": session.total_requests
                })
        
        # Sort by last updated, most recent first
        client_sessions.sort(key=lambda x: x["last_updated"], reverse=True)
        
        return client_sessions[:limit]
    
    async def clear_old_sessions(self, days: int = 30):
        """Clear sessions older than specified days.
        
        Args:
            days: Number of days to keep sessions
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        keys_to_remove = []
        
        for key, session in self.sessions.items():
            if session.last_updated < cutoff_date:
                keys_to_remove.append(key)
                
                # Delete from disk
                session_file = self.storage_dir / f"{session.client_id}_{session.session_id}.json"
                if session_file.exists():
                    session_file.unlink()
        
        # Remove from memory
        for key in keys_to_remove:
            del self.sessions[key]
        
        if keys_to_remove:
            logger.info(f"Cleared {len(keys_to_remove)} old sessions")