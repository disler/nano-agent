"""
Session management for nano-cli with conversation persistence.

Inspired by Claude CLI's session features, provides conversation history
and context preservation across commands.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from uuid import uuid4

from .data_types import ChatMessage


@dataclass
class Session:
    """Represents a conversation session."""
    session_id: str
    created_at: str
    last_updated: str
    provider: str
    model: str
    conversation: List[ChatMessage]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "provider": self.provider,
            "model": self.model,
            "conversation": [
                {"role": msg.role, "content": msg.content} 
                for msg in self.conversation
            ],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Session":
        """Create session from dictionary."""
        return cls(
            session_id=data["session_id"],
            created_at=data["created_at"],
            last_updated=data["last_updated"],
            provider=data["provider"],
            model=data["model"],
            conversation=[
                ChatMessage(role=msg["role"], content=msg["content"])
                for msg in data.get("conversation", [])
            ],
            metadata=data.get("metadata", {})
        )


class SessionManager:
    """Manages conversation sessions with persistence."""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize session manager.
        
        Args:
            storage_dir: Directory to store sessions (default: ~/.nano-cli/sessions)
        """
        if storage_dir is None:
            storage_dir = Path.home() / ".nano-cli" / "sessions"
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[Session] = None
        
    def create_session(self, provider: str, model: str, session_id: Optional[str] = None) -> Session:
        """Create a new session.
        
        Args:
            provider: Provider name (openai, ollama, etc.)
            model: Model name (gpt-oss:20b, etc.)
            session_id: Optional session ID, generates one if not provided
            
        Returns:
            New Session object
        """
        if session_id is None:
            # Generate session ID with timestamp for easy sorting
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = f"session_{timestamp}_{uuid4().hex[:8]}"
            
        session = Session(
            session_id=session_id,
            created_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            provider=provider,
            model=model,
            conversation=[],
            metadata={
                "total_tokens": 0,
                "total_cost": 0.0,
                "message_count": 0
            }
        )
        
        self.current_session = session
        self.save_session(session)
        return session
    
    def load_session(self, session_id: str) -> Optional[Session]:
        """Load an existing session.
        
        Args:
            session_id: Session ID to load
            
        Returns:
            Session object if found, None otherwise
        """
        session_file = self.storage_dir / f"{session_id}.json"
        if not session_file.exists():
            return None
            
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)
            session = Session.from_dict(data)
            self.current_session = session
            return session
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None
    
    def save_session(self, session: Optional[Session] = None) -> bool:
        """Save the current or specified session.
        
        Args:
            session: Session to save (uses current if not specified)
            
        Returns:
            True if saved successfully
        """
        if session is None:
            session = self.current_session
        if session is None:
            return False
            
        session.last_updated = datetime.now().isoformat()
        session_file = self.storage_dir / f"{session.session_id}.json"
        
        try:
            with open(session_file, 'w') as f:
                json.dump(session.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False
    
    def add_exchange(self, user_msg: str, assistant_msg: str, metadata: Optional[Dict] = None):
        """Add a conversation exchange to the current session.
        
        Args:
            user_msg: User's message
            assistant_msg: Assistant's response
            metadata: Optional metadata (tokens, cost, etc.)
        """
        if self.current_session is None:
            return
            
        self.current_session.conversation.append(
            ChatMessage(role="user", content=user_msg)
        )
        self.current_session.conversation.append(
            ChatMessage(role="assistant", content=assistant_msg)
        )
        
        # Update metadata
        self.current_session.metadata["message_count"] += 2
        if metadata:
            if "token_usage" in metadata:
                usage = metadata["token_usage"]
                self.current_session.metadata["total_tokens"] += usage.get("total_tokens", 0)
                self.current_session.metadata["total_cost"] += usage.get("total_cost", 0)
        
        self.save_session()
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get list of recent sessions.
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of session summaries
        """
        sessions = []
        session_files = sorted(
            self.storage_dir.glob("session_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:limit]
        
        for session_file in session_files:
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                sessions.append({
                    "session_id": data["session_id"],
                    "created_at": data["created_at"],
                    "last_updated": data["last_updated"],
                    "provider": data["provider"],
                    "model": data["model"],
                    "message_count": data.get("metadata", {}).get("message_count", 0)
                })
            except Exception:
                continue
                
        return sessions
    
    def get_last_session(self) -> Optional[Session]:
        """Get the most recent session.
        
        Returns:
            Most recent Session object if found
        """
        sessions = self.get_recent_sessions(limit=1)
        if sessions:
            return self.load_session(sessions[0]["session_id"])
        return None
    
    def clear_old_sessions(self, days: int = 30) -> int:
        """Clear sessions older than specified days.
        
        Args:
            days: Number of days to keep sessions
            
        Returns:
            Number of sessions deleted
        """
        import time
        
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        deleted = 0
        
        for session_file in self.storage_dir.glob("session_*.json"):
            if session_file.stat().st_mtime < cutoff_time:
                try:
                    session_file.unlink()
                    deleted += 1
                except Exception:
                    pass
                    
        return deleted
    
    def get_conversation_context(self, max_messages: int = 20) -> List[ChatMessage]:
        """Get recent conversation context from current session.
        
        Args:
            max_messages: Maximum number of messages to include
            
        Returns:
            List of recent messages for context
        """
        if self.current_session is None:
            return []
            
        # Return the most recent messages
        return self.current_session.conversation[-max_messages:]