"""
Session Management for GeneFlow ADK Agents
Tracks user sessions, conversation history, and agent state
"""

import uuid
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


class Session:
    """Represents a single user session with conversation history and context"""
    
    def __init__(self, session_id: str = None, user_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.user_id = user_id or "anonymous"
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.conversation_history: List[Dict[str, Any]] = []
        self.context_data: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        self.active = True
        
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add a message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
        self.last_accessed = datetime.now()
    
    def update_context(self, key: str, value: Any):
        """Update session context data"""
        self.context_data[key] = value
        self.last_accessed = datetime.now()
    
    def get_context(self, key: str = None) -> Any:
        """Get session context data"""
        if key:
            return self.context_data.get(key)
        return self.context_data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "conversation_history": self.conversation_history,
            "context_data": self.context_data,
            "metadata": self.metadata,
            "active": self.active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """Create session from dictionary"""
        session = cls(session_id=data["session_id"], user_id=data.get("user_id"))
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.last_accessed = datetime.fromisoformat(data["last_accessed"])
        session.conversation_history = data.get("conversation_history", [])
        session.context_data = data.get("context_data", {})
        session.metadata = data.get("metadata", {})
        session.active = data.get("active", True)
        return session


class SessionManager:
    """
    Manages multiple user sessions with persistence and cleanup
    Thread-safe implementation
    """
    
    def __init__(self, storage_path: str = None, max_session_age_hours: int = 24):
        self.storage_path = Path(storage_path) if storage_path else Path("sessions")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.max_session_age = timedelta(hours=max_session_age_hours)
        self.sessions: Dict[str, Session] = {}
        self._lock = threading.Lock()
        
        # Load existing sessions
        self._load_sessions()
        
        logger.info(f"SessionManager initialized with storage: {self.storage_path}")
    
    def create_session(self, user_id: str = None) -> Session:
        """Create a new session"""
        with self._lock:
            session = Session(user_id=user_id)
            self.sessions[session.session_id] = session
            self._save_session(session)
            logger.info(f"Created new session: {session.session_id}")
            return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get an existing session"""
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                session.last_accessed = datetime.now()
                self._save_session(session)
            return session
    
    def get_or_create_session(self, session_id: str = None, user_id: str = None) -> Session:
        """Get existing session or create new one"""
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session
        return self.create_session(user_id)
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session.active = False
                self._save_session(session)
                del self.sessions[session_id]
                logger.info(f"Deleted session: {session_id}")
    
    def cleanup_old_sessions(self):
        """Remove sessions older than max_session_age"""
        with self._lock:
            now = datetime.now()
            expired_sessions = [
                sid for sid, session in self.sessions.items()
                if now - session.last_accessed > self.max_session_age
            ]
            for sid in expired_sessions:
                self.delete_session(sid)
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_all_sessions(self) -> List[Session]:
        """Get all active sessions"""
        with self._lock:
            return list(self.sessions.values())
    
    def _save_session(self, session: Session):
        """Save session to disk"""
        try:
            session_file = self.storage_path / f"{session.session_id}.json"
            with open(session_file, 'w') as f:
                json.dump(session.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save session {session.session_id}: {e}")
    
    def _load_sessions(self):
        """Load sessions from disk"""
        try:
            for session_file in self.storage_path.glob("*.json"):
                try:
                    with open(session_file, 'r') as f:
                        data = json.load(f)
                        session = Session.from_dict(data)
                        if session.active:
                            self.sessions[session.session_id] = session
                except Exception as e:
                    logger.error(f"Failed to load session from {session_file}: {e}")
            logger.info(f"Loaded {len(self.sessions)} existing sessions")
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about sessions"""
        with self._lock:
            total_sessions = len(self.sessions)
            total_messages = sum(len(s.conversation_history) for s in self.sessions.values())
            active_today = sum(
                1 for s in self.sessions.values()
                if (datetime.now() - s.last_accessed).days == 0
            )
            
            return {
                "total_sessions": total_sessions,
                "active_today": active_today,
                "total_messages": total_messages,
                "avg_messages_per_session": total_messages / total_sessions if total_sessions > 0 else 0
            }
