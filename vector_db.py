"""
Vector Database Manager for AI Explainer Bot
Stores PDF content with hierarchical topic IDs (1, 1.1, 1.2, 2, 2.1, etc.)
Uses ChromaDB for efficient semantic search and retrieval
"""

import chromadb
from chromadb.config import Settings
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json
from pathlib import Path
import PyPDF2


class VectorDB:
    """
    Manages vector database for storing and retrieving PDF content.
    
    Features:
    - Hierarchical topic IDs (1 for Flask, 1.1 for Flask basics, 2 for FastAPI, 2.1 for FastAPI routing, etc.)
    - PDF content extraction and storage
    - Semantic search across stored documents
    - Topic-based organization
    """
    
    def __init__(self, persist_directory: str = "vector_db"):
        """
        Initialize ChromaDB client with persistent storage.
        
        Args:
            persist_directory: Directory to store vector database files
        """
        self.persist_directory = persist_directory
        
        # Create directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection for PDF documents
        self.collection = self.client.get_or_create_collection(
            name="pdf_documents",
            metadata={"description": "PDF documents with hierarchical topic IDs"}
        )
        
        # Topic tracking file
        self.topics_file = os.path.join(persist_directory, "topics.json")
        self.topics = self._load_topics()
    
    def _load_topics(self) -> Dict:
        """Load topic hierarchy from file."""
        if os.path.exists(self.topics_file):
            with open(self.topics_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"topics": {}, "next_main_id": 1}
    
    def _save_topics(self):
        """Save topic hierarchy to file."""
        with open(self.topics_file, 'w', encoding='utf-8') as f:
            json.dump(self.topics, f, indent=2)
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text content from PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return ""
    
    def get_or_create_topic_id(self, topic: str, parent_topic: Optional[str] = None) -> str:
        """
        Get existing topic ID or create a new hierarchical ID.
        
        Examples:
            - "Flask" -> "1"
            - "Flask" (already exists as "1"), subtopic "Routing" -> "1.1"
            - "FastAPI" -> "2"
            - "FastAPI" (already exists as "2"), subtopic "Authentication" -> "2.1"
        
        Args:
            topic: Topic name (e.g., "Flask", "FastAPI")
            parent_topic: Parent topic name if this is a subtopic
            
        Returns:
            Hierarchical topic ID (e.g., "1", "1.1", "2.1")
        """
        topic_lower = topic.lower()
        
        if parent_topic:
            # This is a subtopic
            parent_lower = parent_topic.lower()
            
            # Check if parent exists
            if parent_lower not in self.topics["topics"]:
                # Create parent first
                parent_id = self.get_or_create_topic_id(parent_topic)
            else:
                parent_id = self.topics["topics"][parent_lower]["id"]
            
            # Check if this subtopic already exists
            for topic_name, topic_data in self.topics["topics"].items():
                if topic_name == topic_lower and topic_data.get("parent") == parent_lower:
                    return topic_data["id"]
            
            # Create new subtopic ID
            # Count existing subtopics for this parent
            subtopic_count = sum(
                1 for t in self.topics["topics"].values()
                if t.get("parent") == parent_lower
            )
            new_subtopic_id = f"{parent_id}.{subtopic_count + 1}"
            
            # Store subtopic
            self.topics["topics"][topic_lower] = {
                "id": new_subtopic_id,
                "name": topic,
                "parent": parent_lower,
                "created_at": datetime.now().isoformat()
            }
            self._save_topics()
            return new_subtopic_id
        
        else:
            # This is a main topic
            if topic_lower in self.topics["topics"]:
                return self.topics["topics"][topic_lower]["id"]
            
            # Create new main topic
            new_id = str(self.topics["next_main_id"])
            self.topics["topics"][topic_lower] = {
                "id": new_id,
                "name": topic,
                "parent": None,
                "created_at": datetime.now().isoformat()
            }
            self.topics["next_main_id"] += 1
            self._save_topics()
            return new_id
    
    def add_pdf_document(
        self,
        pdf_path: str,
        topic: str,
        parent_topic: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Add PDF document to vector database with hierarchical topic ID.
        
        Args:
            pdf_path: Path to PDF file
            topic: Topic name (e.g., "Flask", "Routing")
            parent_topic: Parent topic if this is a subtopic
            metadata: Additional metadata
            
        Returns:
            Topic ID assigned to this document
        """
        # Extract text from PDF
        text_content = self.extract_text_from_pdf(pdf_path)
        
        if not text_content:
            raise ValueError(f"Could not extract text from PDF: {pdf_path}")
        
        # Get or create topic ID
        topic_id = self.get_or_create_topic_id(topic, parent_topic)
        
        # Prepare metadata
        doc_metadata = {
            "topic": topic,
            "topic_id": topic_id,
            "parent_topic": parent_topic or "",
            "pdf_path": pdf_path,
            "added_at": datetime.now().isoformat(),
            "filename": os.path.basename(pdf_path)
        }
        
        if metadata:
            doc_metadata.update(metadata)
        
        # Generate unique document ID
        doc_id = f"{topic_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Add to ChromaDB collection
        self.collection.add(
            documents=[text_content],
            metadatas=[doc_metadata],
            ids=[doc_id]
        )
        
        print(f"✅ Added PDF to vector DB: {topic} (ID: {topic_id})")
        return topic_id
    
    def search_by_topic(self, topic: str, n_results: int = 5) -> List[Dict]:
        """
        Search documents by topic name.
        
        Args:
            topic: Topic to search for
            n_results: Number of results to return
            
        Returns:
            List of matching documents with metadata
        """
        try:
            results = self.collection.query(
                query_texts=[topic],
                n_results=n_results,
                where={"topic": topic}
            )
            
            return self._format_results(results)
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def search_by_topic_id(self, topic_id: str, n_results: int = 5) -> List[Dict]:
        """
        Search documents by hierarchical topic ID.
        
        Args:
            topic_id: Topic ID (e.g., "1", "1.1", "2")
            n_results: Number of results to return
            
        Returns:
            List of matching documents
        """
        try:
            results = self.collection.query(
                query_texts=[""],  # Empty query, we're filtering by metadata
                n_results=n_results,
                where={"topic_id": topic_id}
            )
            
            return self._format_results(results)
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def semantic_search(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Perform semantic search across all documents.
        
        Args:
            query: Search query (e.g., "tell me about Flask routing")
            n_results: Number of results to return
            
        Returns:
            List of most relevant documents
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            return self._format_results(results)
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def get_all_topics(self) -> Dict:
        """
        Get all topics with their hierarchical structure.
        
        Returns:
            Dictionary of topics with IDs and hierarchy
        """
        return self.topics["topics"]
    
    def get_topic_hierarchy(self) -> Dict:
        """
        Get topics organized in hierarchical structure.
        
        Returns:
            Nested dictionary showing topic hierarchy
        """
        hierarchy = {}
        
        # First, add all main topics
        for topic_name, topic_data in self.topics["topics"].items():
            if topic_data["parent"] is None:
                hierarchy[topic_data["id"]] = {
                    "name": topic_data["name"],
                    "id": topic_data["id"],
                    "subtopics": {}
                }
        
        # Then, add subtopics under their parents
        for topic_name, topic_data in self.topics["topics"].items():
            if topic_data["parent"] is not None:
                parent_id = self.topics["topics"][topic_data["parent"]]["id"]
                if parent_id in hierarchy:
                    hierarchy[parent_id]["subtopics"][topic_data["id"]] = {
                        "name": topic_data["name"],
                        "id": topic_data["id"]
                    }
        
        return hierarchy
    
    def get_document_count(self) -> int:
        """Get total number of documents in the database."""
        return self.collection.count()
    
    def delete_by_topic_id(self, topic_id: str):
        """
        Delete all documents with a specific topic ID.
        
        Args:
            topic_id: Topic ID to delete
        """
        try:
            # Get all documents with this topic_id
            results = self.collection.get(
                where={"topic_id": topic_id}
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                print(f"✅ Deleted {len(results['ids'])} documents with topic ID: {topic_id}")
        except Exception as e:
            print(f"Delete error: {e}")
    
    def _format_results(self, results: Dict) -> List[Dict]:
        """Format ChromaDB results into a cleaner structure."""
        formatted = []
        
        if not results["ids"] or not results["ids"][0]:
            return formatted
        
        for i in range(len(results["ids"][0])):
            formatted.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i] if results["documents"] else "",
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if "distances" in results else None
            })
        
        return formatted
    
    def reset_database(self):
        """⚠️ WARNING: Delete all data from the vector database."""
        self.client.delete_collection("pdf_documents")
        self.collection = self.client.get_or_create_collection(
            name="pdf_documents",
            metadata={"description": "PDF documents with hierarchical topic IDs"}
        )
        self.topics = {"topics": {}, "next_main_id": 1}
        self._save_topics()
        print("✅ Vector database reset complete")


# Singleton instance
_vector_db_instance = None

def get_vector_db() -> VectorDB:
    """Get or create singleton VectorDB instance."""
    global _vector_db_instance
    if _vector_db_instance is None:
        _vector_db_instance = VectorDB()
    return _vector_db_instance
