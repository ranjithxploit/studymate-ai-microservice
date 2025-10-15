"""
Session Management Module for AI Explainer Bot
Handles UUID-based session tracking, context storage, and history management
"""
import os
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path

class SessionManager:
    """Manages chat sessions with UUID tracking and file storage"""
    
    def __init__(self, base_dir: str = "context"):
        """
        Initialize session manager
        
        Args:
            base_dir: Base directory for storing session data
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def create_session(self) -> str:
        """
        Create a new chat session with unique UUID
        
        Returns:
            str: Session UUID
        """
        session_id = str(uuid.uuid4())
        session_dir = self.base_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        # Create initial files
        context_file = session_dir / "context.txt"
        history_file = session_dir / "history.txt"
        metadata_file = session_dir / "metadata.json"
        
        # Initialize metadata
        metadata = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "message_count": 0,
            "has_pdf_input": False
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        # Initialize empty files
        context_file.touch()
        history_file.touch()
        
        return session_id
    
    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists
        
        Args:
            session_id: Session UUID
            
        Returns:
            bool: True if session exists
        """
        session_dir = self.base_dir / session_id
        return session_dir.exists() and session_dir.is_dir()
    
    def get_session_dir(self, session_id: str) -> Path:
        """
        Get session directory path
        
        Args:
            session_id: Session UUID
            
        Returns:
            Path: Session directory path
        """
        return self.base_dir / session_id
    
    def save_context(self, session_id: str, context: str) -> None:
        """
        Save or append context to session
        
        Args:
            session_id: Session UUID
            context: Context text to save
        """
        if not self.session_exists(session_id):
            raise ValueError(f"Session {session_id} does not exist")
        
        context_file = self.get_session_dir(session_id) / "context.txt"
        
        with open(context_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n[{timestamp}]\n{context}\n")
        
        self._update_metadata(session_id)
    
    def save_history(self, session_id: str, user_input: str, ai_response: str, 
                     interaction_type: str = "general") -> None:
        """
        Save conversation history
        
        Args:
            session_id: Session UUID
            user_input: User's input/question
            ai_response: AI's response
            interaction_type: Type of interaction (explain, quiz, flashcard, etc.)
        """
        if not self.session_exists(session_id):
            raise ValueError(f"Session {session_id} does not exist")
        
        history_file = self.get_session_dir(session_id) / "history.txt"
        
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": interaction_type,
            "user_input": user_input,
            "ai_response": ai_response
        }
        
        with open(history_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(history_entry, ensure_ascii=False) + "\n")
        
        self._update_metadata(session_id)
    
    def save_pdf_input(self, session_id: str, pdf_content: bytes, filename: str) -> str:
        """
        Save PDF input file
        
        Args:
            session_id: Session UUID
            pdf_content: PDF file content in bytes
            filename: Original filename
            
        Returns:
            str: Path to saved PDF file
        """
        if not self.session_exists(session_id):
            raise ValueError(f"Session {session_id} does not exist")
        
        pdf_file = self.get_session_dir(session_id) / "input.pdf"
        
        with open(pdf_file, 'wb') as f:
            f.write(pdf_content)
        
        # Update metadata
        metadata = self._load_metadata(session_id)
        metadata["has_pdf_input"] = True
        metadata["pdf_filename"] = filename
        metadata["pdf_saved_at"] = datetime.now().isoformat()
        self._save_metadata(session_id, metadata)
        
        return str(pdf_file)
    
    def save_text_input(self, session_id: str, text_input: str, input_type: str = "text") -> None:
        """
        Save text or topic input
        
        Args:
            session_id: Session UUID
            text_input: Text or topic input
            input_type: Type of input (text, topic, question)
        """
        if not self.session_exists(session_id):
            raise ValueError(f"Session {session_id} does not exist")
        
        input_file = self.get_session_dir(session_id) / "input.txt"
        
        with open(input_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n[{timestamp}] ({input_type})\n{text_input}\n")
        
        self._update_metadata(session_id)
    
    def get_context(self, session_id: str) -> str:
        """
        Retrieve session context
        
        Args:
            session_id: Session UUID
            
        Returns:
            str: Context content
        """
        if not self.session_exists(session_id):
            raise ValueError(f"Session {session_id} does not exist")
        
        context_file = self.get_session_dir(session_id) / "context.txt"
        
        if context_file.exists():
            with open(context_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def get_history(self, session_id: str) -> List[Dict]:
        """
        Retrieve session history
        
        Args:
            session_id: Session UUID
            
        Returns:
            List[Dict]: List of history entries
        """
        if not self.session_exists(session_id):
            raise ValueError(f"Session {session_id} does not exist")
        
        history_file = self.get_session_dir(session_id) / "history.txt"
        history = []
        
        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            history.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        
        return history
    
    def get_metadata(self, session_id: str) -> Dict:
        """
        Get session metadata
        
        Args:
            session_id: Session UUID
            
        Returns:
            Dict: Session metadata
        """
        if not self.session_exists(session_id):
            raise ValueError(f"Session {session_id} does not exist")
        
        return self._load_metadata(session_id)
    
    def list_sessions(self) -> List[Dict]:
        """
        List all available sessions
        
        Returns:
            List[Dict]: List of session metadata
        """
        sessions = []
        
        if not self.base_dir.exists():
            return sessions
        
        for session_dir in self.base_dir.iterdir():
            if session_dir.is_dir():
                try:
                    metadata = self._load_metadata(session_dir.name)
                    sessions.append(metadata)
                except:
                    continue
        
        # Sort by last updated (newest first)
        sessions.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
        
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session UUID
            
        Returns:
            bool: True if deleted successfully
        """
        if not self.session_exists(session_id):
            return False
        
        session_dir = self.get_session_dir(session_id)
        
        # Delete all files in directory
        for file in session_dir.iterdir():
            file.unlink()
        
        # Delete directory
        session_dir.rmdir()
        
        return True
    
    def _load_metadata(self, session_id: str) -> Dict:
        """Load session metadata"""
        metadata_file = self.get_session_dir(session_id) / "metadata.json"
        
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {}
    
    def _save_metadata(self, session_id: str, metadata: Dict) -> None:
        """Save session metadata"""
        metadata_file = self.get_session_dir(session_id) / "metadata.json"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def _update_metadata(self, session_id: str) -> None:
        """Update session metadata timestamps and counts"""
        metadata = self._load_metadata(session_id)
        metadata["last_updated"] = datetime.now().isoformat()
        metadata["message_count"] = metadata.get("message_count", 0) + 1
        self._save_metadata(session_id, metadata)


# Global session manager instance
session_manager = SessionManager()
