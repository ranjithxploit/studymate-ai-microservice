"""
Vector Database Manager for AI Explainer Bot
Stores PDF content with hierarchical topic IDs (1, 1.1, 1.2, 2, 2.1, etc.)
Uses ChromaDB for efficient semantic search and retrieval
"""

import chromadb
from chromadb.config import Settings
import os
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import json
from pathlib import Path
import PyPDF2


class VectorDB:
    def __init__(self, persist_directory: str = "vector_db"):
        self.persist_directory = persist_directory
        

        os.makedirs(persist_directory, exist_ok=True)        
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
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
    
    def extract_text_with_pages(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from PDF with page numbers.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of dictionaries with page number and text content
        """
        try:
            pages_data = []
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    text = page.extract_text().strip()
                    if text:  # Only add non-empty pages
                        pages_data.append({
                            "page_number": page_num,
                            "text": text
                        })
            return pages_data
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return []
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks for better context preservation.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum characters per chunk
            overlap: Number of overlapping characters between chunks
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            
            # If this is not the last chunk, try to break at a sentence or word boundary
            if end < text_length:
                # Look for sentence boundaries (. ! ?)
                for boundary in ['. ', '! ', '? ', '\n\n', '\n', ' ']:
                    boundary_pos = text.rfind(boundary, start, end)
                    if boundary_pos != -1:
                        end = boundary_pos + len(boundary)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap if end < text_length else end
        
        return chunks
    
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
    
    def add_pdf_chunks(
        self,
        pdf_path: str,
        session_id: str,
        chunk_size: int = 2000,  # Larger chunks = fewer chunks = faster
        overlap: int = 100,  # Less overlap = faster
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Add PDF document as chunks with page numbers and indices.
        Designed for session-based PDF processing.
        
        Args:
            pdf_path: Path to PDF file
            session_id: Session ID to associate with this PDF
            chunk_size: Maximum characters per chunk
            overlap: Number of overlapping characters between chunks
            metadata: Additional metadata
            
        Returns:
            Dictionary with document ID, chunk count, and page count
        """
        print(f"🔄 Starting PDF processing for session {session_id}...")
        
        # Extract text with page numbers
        pages_data = self.extract_text_with_pages(pdf_path)
        
        if not pages_data:
            raise ValueError(f"Could not extract text from PDF: {pdf_path}")
        
        print(f"📄 Extracted {len(pages_data)} pages from PDF")
        
        # Generate unique document ID for this PDF
        doc_id = f"session_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        filename = os.path.basename(pdf_path)
        
        chunks_added = 0
        all_chunk_ids = []
        
        # Prepare batch data for all chunks
        batch_documents = []
        batch_metadatas = []
        batch_ids = []
        
        print(f"🔨 Chunking text...")
        
        # Process each page - store full pages if they're small enough
        for page_data in pages_data:
            page_num = page_data["page_number"]
            page_text = page_data["text"]
            
            # If page is small enough, store as single chunk
            if len(page_text) <= chunk_size:
                chunk_id = f"{doc_id}_page{page_num}_chunk0"
                
                chunk_metadata = {
                    "session_id": session_id,
                    "document_id": doc_id,
                    "filename": filename,
                    "pdf_path": pdf_path,
                    "page_number": page_num,
                    "chunk_index": 0,
                    "total_chunks_in_page": 1,
                    "added_at": datetime.now().isoformat(),
                    "type": "pdf_chunk"
                }
                
                if metadata:
                    chunk_metadata.update(metadata)
                
                batch_documents.append(page_text)
                batch_metadatas.append(chunk_metadata)
                batch_ids.append(chunk_id)
                chunks_added += 1
                all_chunk_ids.append(chunk_id)
            else:
                # Only chunk if page is too large
                chunks = self.chunk_text(page_text, chunk_size, overlap)
                
                # Prepare each chunk for batch insertion
                for chunk_idx, chunk_text in enumerate(chunks):
                    chunk_id = f"{doc_id}_page{page_num}_chunk{chunk_idx}"
                    
                    chunk_metadata = {
                        "session_id": session_id,
                        "document_id": doc_id,
                        "filename": filename,
                        "pdf_path": pdf_path,
                        "page_number": page_num,
                        "chunk_index": chunk_idx,
                        "total_chunks_in_page": len(chunks),
                        "added_at": datetime.now().isoformat(),
                        "type": "pdf_chunk"
                    }
                    
                    if metadata:
                        chunk_metadata.update(metadata)
                    
                    # Add to batch
                    batch_documents.append(chunk_text)
                    batch_metadatas.append(chunk_metadata)
                    batch_ids.append(chunk_id)
                    
                    chunks_added += 1
                    all_chunk_ids.append(chunk_id)
        
        print(f"💾 Inserting {chunks_added} chunks into vector DB...")
        
        # Batch insert all chunks at once (MUCH faster!)
        if batch_documents:
            self.collection.add(
                documents=batch_documents,
                metadatas=batch_metadatas,
                ids=batch_ids
            )
        
        print(f"✅ Added {chunks_added} chunks from PDF to vector DB (Session: {session_id})")
        
        return {
            "document_id": doc_id,
            "filename": filename,
            "total_chunks": chunks_added,
            "total_pages": len(pages_data),
            "chunk_ids": all_chunk_ids,
            "session_id": session_id
        }
    
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
    
    def search_pdf_chunks(
        self,
        query: str,
        session_id: str,
        n_results: int = 5
    ) -> List[Dict]:
        """
        Search PDF chunks for a specific session.
        
        Args:
            query: Search query (user's question)
            session_id: Session ID to filter by
            n_results: Number of most relevant chunks to return
            
        Returns:
            List of relevant chunks with metadata (page, chunk_index, text, relevance)
        """
        try:
            # Search with session filter using correct ChromaDB syntax
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where={
                    "$and": [
                        {"session_id": {"$eq": session_id}},
                        {"type": {"$eq": "pdf_chunk"}}
                    ]
                }
            )
            
            formatted = self._format_results(results)
            
            # Add relevance score (1.0 - distance)
            for item in formatted:
                if item.get("distance") is not None:
                    # ChromaDB uses cosine distance (0 = identical, 2 = opposite)
                    # Convert to similarity score (1.0 = best, 0 = worst)
                    item["relevance_score"] = max(0, 1.0 - (item["distance"] / 2.0))
                else:
                    item["relevance_score"] = 0.0
            
            return formatted
            
        except Exception as e:
            print(f"PDF chunk search error: {e}")
            return []
    
    def get_session_pdf_info(self, session_id: str) -> Optional[Dict]:
        """
        Get information about PDF(s) associated with a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dictionary with PDF information or None if no PDF found
        """
        try:
            # Use query instead of get for complex where clauses
            results = self.collection.query(
                query_texts=[""],  # Empty query, filtering by metadata only
                where={"$and": [
                    {"session_id": {"$eq": session_id}},
                    {"type": {"$eq": "pdf_chunk"}}
                ]},
                n_results=1
            )
            
            if results["ids"] and len(results["ids"][0]) > 0:
                metadata = results["metadatas"][0][0]
                
                # Count total chunks for this session using query
                all_chunks = self.collection.query(
                    query_texts=[""],
                    where={"$and": [
                        {"session_id": {"$eq": session_id}},
                        {"type": {"$eq": "pdf_chunk"}}
                    ]},
                    n_results=10000  # Large number to get all chunks
                )
                
                return {
                    "has_pdf": True,
                    "document_id": metadata.get("document_id"),
                    "filename": metadata.get("filename"),
                    "pdf_path": metadata.get("pdf_path"),
                    "total_chunks": len(all_chunks["ids"][0]) if all_chunks["ids"] and all_chunks["ids"][0] else 0,
                    "added_at": metadata.get("added_at")
                }
            
            return {"has_pdf": False}
            
        except Exception as e:
            print(f"Error getting session PDF info: {e}")
            return {"has_pdf": False}
    
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
