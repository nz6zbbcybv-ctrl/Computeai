"""
Session management service with SQLite persistence.
"""
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

from app.config import Config
from app.utils.logger import setup_logger
from app.utils.exceptions import SessionNotFoundError

logger = setup_logger("session_manager")


class SessionManager:
    """Service for managing chat sessions."""
    
    def __init__(self):
        """Initialize session manager and database."""
        self.db_path = Config.DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info(f"Session manager initialized with database: {self.db_path}")
    
    def _init_database(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                message_count INTEGER DEFAULT 0,
                language TEXT,
                model TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session 
            ON messages(session_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_updated 
            ON sessions(updated_at)
        """)
        
        conn.commit()
        conn.close()
    
    def create_session(
        self,
        language: Optional[str] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Create a new session.
        
        Args:
            language: Detected language
            model: Model name
            
        Returns:
            Session ID (UUID)
        """
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sessions (session_id, created_at, updated_at, message_count, language, model)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, now, now, 0, language, model))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session dict or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM sessions WHERE session_id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str
    ):
        """
        Add a message to a session.
        
        Args:
            session_id: Session ID
            role: Message role ('user' or 'assistant')
            content: Message content
            
        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        session = self.get_session(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        now = datetime.utcnow()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert message
        cursor.execute("""
            INSERT INTO messages (session_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (session_id, role, content, now))
        
        # Update session
        cursor.execute("""
            UPDATE sessions 
            SET updated_at = ?, message_count = message_count + 1
            WHERE session_id = ?
        """, (now, session_id))
        
        conn.commit()
        conn.close()
    
    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of message dicts
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT role, content, timestamp 
            FROM messages 
            WHERE session_id = ? 
            ORDER BY timestamp ASC
        """, (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history in format suitable for Groq API.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of message dicts with 'role' and 'content'
        """
        messages = self.get_messages(session_id)
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]
    
    def cleanup_expired_sessions(self):
        """Remove sessions older than timeout period."""
        cutoff = datetime.utcnow() - timedelta(minutes=Config.SESSION_TIMEOUT_MINUTES)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete messages for expired sessions
        cursor.execute("""
            DELETE FROM messages 
            WHERE session_id IN (
                SELECT session_id FROM sessions WHERE updated_at < ?
            )
        """, (cutoff,))
        
        # Delete expired sessions
        cursor.execute("""
            DELETE FROM sessions WHERE updated_at < ?
        """, (cutoff,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} expired sessions")

