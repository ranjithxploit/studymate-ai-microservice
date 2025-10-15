import os
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path

class SessionManager:
    def __init__(self, base_dir: str = "context"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        session_dir = self.base_dir / session_id
        session_dir.mkdir(exist_ok=True)        
        context_file = session_dir / "context.txt"
        history_file = session_dir / "history.txt"
        metadata_file = session_dir / "metadata.json"        
        metadata = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "message_count": 0,
            "has_pdf_input": False,
            "topics": [],  # List of topics in order (latest last) - supports multiple topics
            "levels": None  # Content complexity level: beginner, university, researcher
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)        
        context_file.touch()
        history_file.touch()
        
        return session_id
    
    def session_exists(self, session_id: str) -> bool:
        session_dir = self.base_dir / session_id
        return session_dir.exists() and session_dir.is_dir()
    
    def get_session_dir(self, session_id: str) -> Path:
        return self.base_dir / session_id
    
    def save_context(self, session_id: str, context: str) -> None:
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
        Save PDF input file with original filename
        
        Args:
            session_id: Session UUID
            pdf_content: PDF file content in bytes
            filename: Original filename (will be sanitized)
            
        Returns:
            str: Path to saved PDF file
        """
        if not self.session_exists(session_id):
            raise ValueError(f"Session {session_id} does not exist")
        
        # Sanitize filename - remove path components, keep only filename
        safe_filename = Path(filename).name
        
        # Ensure .pdf extension
        if not safe_filename.lower().endswith('.pdf'):
            safe_filename += '.pdf'
        
        # Save with original filename
        pdf_file = self.get_session_dir(session_id) / safe_filename
        
        with open(pdf_file, 'wb') as f:
            f.write(pdf_content)
        
        # Update metadata - track multiple PDFs
        metadata = self._load_metadata(session_id)
        
        # Initialize pdf_files list if not exists
        if "pdf_files" not in metadata:
            metadata["pdf_files"] = []
        
        # Add this PDF to the list
        metadata["pdf_files"].append({
            "filename": safe_filename,
            "uploaded_at": datetime.now().isoformat(),
            "path": str(pdf_file)
        })
        
        # Keep old fields for backward compatibility
        metadata["has_pdf_input"] = True
        metadata["pdf_filename"] = safe_filename
        metadata["pdf_saved_at"] = datetime.now().isoformat()
        
        self._save_metadata(session_id, metadata)
        
        return str(pdf_file)
    

    
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
    
    def set_topic(self, session_id: str, topic: str, levels: str = "beginner") -> None:
        """
        Add a new topic to the session (appends to list, doesn't replace)
        
        Args:
            session_id: Session UUID
            topic: The topic/question to add to this session
            levels: Content complexity level (beginner, university, researcher)
        """
        if not self.session_exists(session_id):
            raise ValueError(f"Session {session_id} does not exist")
        
        metadata = self._load_metadata(session_id)
        
        # Initialize topics list if it doesn't exist (backward compatibility)
        if "topics" not in metadata:
            metadata["topics"] = []
        
        # Append new topic to the list
        metadata["topics"].append({
            "topic": topic,
            "added_at": datetime.now().isoformat()
        })
        
        # Update levels (latest takes precedence)
        metadata["levels"] = levels
        metadata["last_topic_added_at"] = datetime.now().isoformat()
        
        self._save_metadata(session_id, metadata)
    
    def get_topic(self, session_id: str) -> Optional[str]:
        """
        Get the most recent topic for a session
        
        Args:
            session_id: Session UUID
            
        Returns:
            Optional[str]: The most recent topic or None if no topics exist
        """
        if not self.session_exists(session_id):
            raise ValueError(f"Session {session_id} does not exist")
        
        metadata = self._load_metadata(session_id)
        topics = metadata.get("topics", [])
        
        if topics:
            return topics[-1]["topic"]  # Return most recent topic
        
        # Backward compatibility: check old "topic" field
        return metadata.get("topic")
    
    def get_all_topics(self, session_id: str) -> List[str]:
        """
        Get all topics for a session in order (oldest first, newest last)
        
        Args:
            session_id: Session UUID
            
        Returns:
            List[str]: List of all topics in the session
        """
        if not self.session_exists(session_id):
            raise ValueError(f"Session {session_id} does not exist")
        
        metadata = self._load_metadata(session_id)
        topics = metadata.get("topics", [])
        
        topic_list = [t["topic"] for t in topics]
        
        # Backward compatibility: include old "topic" field if exists
        old_topic = metadata.get("topic")
        if old_topic and old_topic not in topic_list:
            topic_list.insert(0, old_topic)
        
        return topic_list
    
    def get_difficulty(self, session_id: str) -> str:
        """
        Get the levels (content complexity) for a session
        
        Args:
            session_id: Session UUID
            
        Returns:
            str: The levels or 'beginner' as default
        """
        if not self.session_exists(session_id):
            raise ValueError(f"Session {session_id} does not exist")
        
        metadata = self._load_metadata(session_id)
        
        # Try new "levels" field first, fallback to old "difficulty" field
        levels = metadata.get("levels") or metadata.get("difficulty")
        
        return levels if levels else "beginner"
    
    def get_levels(self, session_id: str) -> str:
        """
        Alias for get_difficulty() with better naming
        
        Args:
            session_id: Session UUID
            
        Returns:
            str: The content complexity level (beginner, university, researcher)
        """
        return self.get_difficulty(session_id)
    
    def get_pdf_files(self, session_id: str) -> List[Dict]:
        """
        Get all PDF files in a session
        
        Args:
            session_id: Session UUID
            
        Returns:
            List[Dict]: List of PDF files with metadata
        """
        if not self.session_exists(session_id):
            raise ValueError(f"Session {session_id} does not exist")
        
        metadata = self._load_metadata(session_id)
        return metadata.get("pdf_files", [])
    
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
