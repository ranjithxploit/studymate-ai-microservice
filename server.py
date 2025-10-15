import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import google.generativeai as genai
import dotenv
from session_manager import session_manager
from vector_db import get_vector_db
from langchain_handler import get_langchain_handler

dotenv.load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set. Set it in the environment or a .env file.")

genai.configure(api_key=API_KEY)
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
vector_db = get_vector_db()
langchain_handler = get_langchain_handler()
app = FastAPI(
    title="AI Explainer Bot API",
    description="Educational AI API for explaining concepts, generating quizzes, flashcards, and more",
    version="2.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExplainRequest(BaseModel):
    question: str = Field(..., example="What is machine learning?")
    difficulty: Optional[str] = Field("beginner", example="beginner")
    session_id: Optional[str] = None

class ExplainResponse(BaseModel):
    question: str
    explanation: str
    example: str
    difficulty: str
    session_id: str

class FlashcardRequest(BaseModel):
    topic: str = Field(..., example="Neural Networks")
    count: Optional[int] = Field(5, ge=1, le=20)
    difficulty: Optional[str] = Field("intermediate", example="intermediate")
    session_id: Optional[str] = None

class Flashcard(BaseModel):
    front: str
    back: str

class FlashcardResponse(BaseModel):
    topic: str
    flashcards: List[Flashcard]
    session_id: str

class QuizRequest(BaseModel):
    topic: str = Field(..., example="Machine Learning Basics")
    num_questions: Optional[int] = Field(5, ge=1, le=20)
    difficulty: Optional[str] = Field("intermediate", example="intermediate")
    session_id: Optional[str] = None

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str

class QuizResponse(BaseModel):
    topic: str
    questions: List[QuizQuestion]
    session_id: str

class DemoRequest(BaseModel):
    concept: str = Field(..., example="Linear Regression")
    session_id: Optional[str] = None

class DemoResponse(BaseModel):
    concept: str
    demo_code: str
    explanation: str
    output_example: str
    session_id: str

class FlowchartRequest(BaseModel):
    concept: str = Field(..., example="How Neural Networks Work")
    session_id: Optional[str] = None

class FlowchartResponse(BaseModel):
    concept: str
    steps: List[str]
    mermaid_code: str
    session_id: str

class ThoughtRequest(BaseModel):
    topic: str = Field(..., example="Artificial Intelligence")
    count: Optional[int] = Field(3, ge=1, le=10)
    session_id: Optional[str] = None

class ThoughtResponse(BaseModel):
    topic: str
    questions: List[str]
    session_id: str

class CodeExecutionRequest(BaseModel):
    code: str = Field(..., example="print('Hello World')")
    language: Optional[str] = Field("python", example="python")
    session_id: Optional[str] = None

class CodeExecutionResponse(BaseModel):
    output: str
    error: Optional[str]
    execution_time: Optional[str]
    session_id: str

class ExampleCodeRequest(BaseModel):
    topic: str = Field(..., example="File handling in Python")
    difficulty: Optional[str] = Field("intermediate", example="intermediate")
    language: Optional[str] = Field("python", example="python")
    session_id: Optional[str] = None

class ExampleCodeResponse(BaseModel):
    topic: str
    code: str
    explanation: str
    key_concepts: List[str]
    best_practices: List[str]
    usage_example: str
    difficulty: str
    language: str
    session_id: str

class SessionCreateResponse(BaseModel):
    session_id: str
    message: str
    created_at: str

class SessionHistoryResponse(BaseModel):
    session_id: str
    history: List[dict]
    message_count: int

class SessionContextResponse(BaseModel):
    session_id: str
    context: str

class SessionMetadataResponse(BaseModel):
    session_id: str
    created_at: str
    last_updated: str
    message_count: int
    has_pdf_input: bool

class SessionListResponse(BaseModel):
    sessions: List[dict]
    total_count: int

@app.get("/")
def read_root():
    return {
        "message": "AI Explainer Bot API",
        "version": "1.0.0",
        "endpoints": {
            "explain": "/api/explain",
            "flashcards": "/api/flashcards",
            "quiz": "/api/quiz",
            "demo": "/api/demo",
            "flowchart": "/api/flowchart",
            "thought-questions": "/api/thought-questions",
            "execute-code": "/api/execute-code"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "model": MODEL_NAME}

@app.post("/api/explain", response_model=ExplainResponse)
def explain_concept(request: ExplainRequest):
    """
    Explain an AI/ML concept in simple terms with examples.
    Automatically creates or uses existing session for tracking.
    Uses LangChain for refined responses.
    """
    # Create or get session
    session_id = request.session_id
    if not session_id or not session_manager.session_exists(session_id):
        session_id = session_manager.create_session()
    
    # Refine user input first
    refined_question = langchain_handler.refine_user_input(request.question)
    
    # Save input
    session_manager.save_context(
        session_id, 
        f"Topic: {refined_question}\nDifficulty: {request.difficulty}"
    )
    
    # Generate explanation using LangChain
    result = langchain_handler.generate_explanation(refined_question, request.difficulty or "beginner")
    
    # Save history
    session_manager.save_history(
        session_id,
        refined_question,
        f"Explanation: {result['explanation']}\nExample: {result['example']}",
        "explain"
    )
    
    return ExplainResponse(
        question=refined_question,
        explanation=result["explanation"],
        example=result["example"],
        difficulty=request.difficulty or "beginner",
        session_id=session_id
    )

@app.post("/api/flashcards", response_model=FlashcardResponse)
def generate_flashcards(request: FlashcardRequest):
    session_id = request.session_id
    if not session_id or not session_manager.session_exists(session_id):
        session_id = session_manager.create_session()
    refined_topic = langchain_handler.refine_user_input(request.topic)
    difficulty = request.difficulty if request.difficulty else "intermediate"
    session_manager.save_context(
        session_id, 
        f"Generating {request.count} flashcards about: {refined_topic}\nDifficulty: {difficulty}"
    )
    flashcard_data = langchain_handler.generate_flashcards(
        refined_topic, 
        request.count or 5,
        difficulty
    )
    
    flashcards = [
        Flashcard(front=card.get("front", ""), back=card.get("back", ""))
        for card in flashcard_data
    ]
    session_manager.save_history(
        session_id,
        f"Generate flashcards for: {refined_topic}",
        f"Generated {len(flashcards)} flashcards",
        "flashcards"
    )
    
    return FlashcardResponse(
        topic=refined_topic, 
        flashcards=flashcards, 
        session_id=session_id
    )

@app.post("/api/quiz", response_model=QuizResponse)
def generate_quiz(request: QuizRequest):
    """Generate quiz questions. Tracks session automatically. Uses LangChain.
    Difficulty levels: beginner, intermediate, professional"""
    # Create or get session
    session_id = request.session_id
    if not session_id or not session_manager.session_exists(session_id):
        session_id = session_manager.create_session()
    
    # Refine topic
    refined_topic = langchain_handler.refine_user_input(request.topic)
    difficulty = request.difficulty or "intermediate"
    
    # Save input with difficulty
    session_manager.save_context(
        session_id, 
        f"Generating {request.num_questions} quiz questions about: {refined_topic}\nDifficulty: {difficulty}"
    )
    
    # Generate quiz using LangChain (returns a list directly)
    quiz_data = langchain_handler.generate_quiz(
        refined_topic, 
        request.num_questions or 5,
        difficulty
    )
    
    # Convert to QuizQuestion objects
    questions = [
        QuizQuestion(
            question=q.get("question", ""),
            options=q.get("options", []),
            correct_answer=q.get("correct_answer", ""),
            explanation=q.get("explanation", "")
        )
        for q in quiz_data
    ]
    
    # Save history
    session_manager.save_history(
        session_id,
        f"Generate quiz for: {refined_topic}",
        f"Generated {len(questions)} quiz questions",
        "quiz"
    )
    
    return QuizResponse(
        topic=refined_topic, 
        questions=questions, 
        session_id=session_id
    )

@app.post("/api/demo", response_model=DemoResponse)
def generate_demo(request: DemoRequest):
    """Generate code demonstration. Tracks session automatically. Uses LangChain."""
    # Create or get session
    session_id = request.session_id
    if not session_id or not session_manager.session_exists(session_id):
        session_id = session_manager.create_session()
    
    # Refine concept
    refined_concept = langchain_handler.refine_user_input(request.concept)
    
    # Save input
    session_manager.save_context(session_id, f"Generating code demo for: {refined_concept}")
    
    # Generate demo using LangChain
    demo_data = langchain_handler.generate_demo(refined_concept)
    
    # Save history
    session_manager.save_history(
        session_id,
        f"Generate demo for: {refined_concept}",
        f"Code demo generated",
        "demo"
    )
    
    return DemoResponse(
        concept=refined_concept,
        demo_code=demo_data["code"],
        explanation=demo_data["explanation"],
        output_example=demo_data["output"],
        session_id=session_id
    )

@app.post("/api/flowchart", response_model=FlowchartResponse)
def generate_flowchart(request: FlowchartRequest):
    """Generate flowchart/process diagram. Tracks session automatically. Uses LangChain."""
    # Create or get session
    session_id = request.session_id
    if not session_id or not session_manager.session_exists(session_id):
        session_id = session_manager.create_session()
    
    # Refine concept
    refined_concept = langchain_handler.refine_user_input(request.concept)
    
    # Save input
    session_manager.save_context(session_id, f"Generating flowchart for: {refined_concept}")
    
    # Generate flowchart using LangChain
    flowchart_data = langchain_handler.generate_flowchart(refined_concept)
    
    # Save history
    session_manager.save_history(
        session_id,
        f"Generate flowchart for: {refined_concept}",
        f"Flowchart generated with {len(flowchart_data['steps'])} steps",
        "flowchart"
    )
    
    return FlowchartResponse(
        concept=refined_concept,
        steps=flowchart_data["steps"],
        mermaid_code=flowchart_data["mermaid_code"],
        session_id=session_id
    )

@app.post("/api/thought-questions", response_model=ThoughtResponse)
def generate_thought_questions(request: ThoughtRequest):
    """Generate thought-provoking questions. Tracks session automatically. Uses LangChain."""
    # Create or get session
    session_id = request.session_id
    if not session_id or not session_manager.session_exists(session_id):
        session_id = session_manager.create_session()
    
    # Refine topic
    refined_topic = langchain_handler.refine_user_input(request.topic)
    
    # Save input
    session_manager.save_context(
        session_id, 
        f"Generating {request.count} thought questions about: {refined_topic}"
    )
    
    # Generate thought questions using LangChain
    questions = langchain_handler.generate_thought_questions(refined_topic, request.count or 3)
    
    # Save history
    session_manager.save_history(
        session_id,
        f"Generate thought questions for: {refined_topic}",
        f"Generated {len(questions)} thought-provoking questions",
        "thought_questions"
    )
    
    return ThoughtResponse(
        topic=refined_topic, 
        questions=questions, 
        session_id=session_id
    )

@app.post("/api/execute-code", response_model=CodeExecutionResponse)
def execute_code(request: CodeExecutionRequest):
    """Analyze/execute code (simulated). Tracks session automatically. Uses LangChain."""
    # Create or get session
    session_id = request.session_id
    if not session_id or not session_manager.session_exists(session_id):
        session_id = session_manager.create_session()
    
    # Save input
    session_manager.save_context(session_id, f"Analyzing {request.language} code execution")
    
    # NOTE: For security reasons, we don't actually execute arbitrary code
    # Instead, we use AI to analyze what the code would do
    
    # Analyze code using LangChain
    analysis = langchain_handler.analyze_code(request.code, request.language or "python")
    
    # Extract output/error from analysis
    output = analysis.get("output", "Code analysis completed")
    error = analysis.get("error")
    
    # Save history
    session_manager.save_history(
        session_id,
        f"Execute code: {request.code[:50]}...",
        f"Output: {output[:100]}",
        "code_execution"
    )
    
    return CodeExecutionResponse(
        output=output,
        error=error,
        execution_time="simulated",
        session_id=session_id
    )

@app.post("/api/example-code", response_model=ExampleCodeResponse)
def generate_example_code(request: ExampleCodeRequest):
    """
    Generate professional, production-ready code examples.
    Tracks session automatically. Uses LangChain.
    Difficulty levels: beginner, intermediate, professional
    """
    # Create or get session
    session_id = request.session_id
    if not session_id or not session_manager.session_exists(session_id):
        session_id = session_manager.create_session()
    
    # Refine topic
    refined_topic = langchain_handler.refine_user_input(request.topic)
    difficulty = request.difficulty or "intermediate"
    language = request.language or "python"
    
    # Save input with difficulty level
    session_manager.save_context(
        session_id, 
        f"Generating {language} code example for: {refined_topic}\nDifficulty: {difficulty}"
    )
    
    # Generate code example using LangChain
    code_result = langchain_handler.generate_example_code(
        refined_topic, 
        difficulty,
        language
    )
    
    # Save history
    session_manager.save_history(
        session_id,
        f"Generate {language} code for: {refined_topic} ({difficulty})",
        f"Code example generated with {len(code_result.get('best_practices', []))} best practices",
        "example_code"
    )
    
    return ExampleCodeResponse(
        topic=refined_topic,
        code=code_result.get("code", ""),
        explanation=code_result.get("explanation", ""),
        key_concepts=code_result.get("key_concepts", []),
        best_practices=code_result.get("best_practices", []),
        usage_example=code_result.get("usage_example", ""),
        difficulty=difficulty,
        language=language,
        session_id=session_id
    )

# Session Management Endpoints
@app.post("/api/session/create", response_model=SessionCreateResponse)
def create_session():
    """Create a new chat session with unique UUID."""
    session_id = session_manager.create_session()
    metadata = session_manager.get_metadata(session_id)
    
    return SessionCreateResponse(
        session_id=session_id,
        message="Session created successfully",
        created_at=metadata["created_at"]
    )

@app.get("/api/session/{session_id}/history", response_model=SessionHistoryResponse)
def get_session_history(session_id: str):
    """Retrieve conversation history for a session."""
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    history = session_manager.get_history(session_id)
    metadata = session_manager.get_metadata(session_id)
    
    return SessionHistoryResponse(
        session_id=session_id,
        history=history,
        message_count=metadata.get("message_count", 0)
    )

@app.get("/api/session/{session_id}/context", response_model=SessionContextResponse)
def get_session_context(session_id: str):
    """Retrieve context for a session."""
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    context = session_manager.get_context(session_id)
    
    return SessionContextResponse(
        session_id=session_id,
        context=context
    )

@app.get("/api/session/{session_id}/metadata", response_model=SessionMetadataResponse)
def get_session_metadata(session_id: str):
    """Get session metadata."""
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    metadata = session_manager.get_metadata(session_id)
    
    return SessionMetadataResponse(**metadata)

@app.get("/api/sessions", response_model=SessionListResponse)
def list_sessions():
    """List all available sessions."""
    sessions = session_manager.list_sessions()
    
    return SessionListResponse(
        sessions=sessions,
        total_count=len(sessions)
    )

@app.delete("/api/session/{session_id}")
def delete_session(session_id: str):
    """Delete a session."""
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    success = session_manager.delete_session(session_id)
    
    if success:
        return {"message": f"Session {session_id} deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete session")

@app.post("/api/session/{session_id}/upload-pdf")
async def upload_pdf(
    session_id: str, 
    file: UploadFile = File(...),
    topic: Optional[str] = None,
    parent_topic: Optional[str] = None
):
    """
    Upload a PDF file to a session and store in vector database.
    
    Args:
        session_id: Session UUID
        file: PDF file to upload
        topic: Topic name for vector DB (e.g., "Flask", "FastAPI")
        parent_topic: Parent topic if this is a subtopic (e.g., "Flask" for "Flask Routing")
    """
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    # Check file type
    filename = file.filename or "input.pdf"
    if not filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Read file content
    content = await file.read()
    
    # Save PDF to session
    pdf_path = session_manager.save_pdf_input(session_id, content, filename)
    
    # Add to vector database if topic provided
    topic_id = None
    if topic:
        try:
            topic_id = vector_db.add_pdf_document(
                pdf_path=pdf_path,
                topic=topic,
                parent_topic=parent_topic,
                metadata={
                    "session_id": session_id,
                    "filename": filename
                }
            )
        except Exception as e:
            # PDF saved but vector DB storage failed
            return {
                "message": "PDF uploaded successfully but vector DB storage failed",
                "session_id": session_id,
                "filename": filename,
                "saved_path": pdf_path,
                "vector_db_error": str(e)
            }
    
    return {
        "message": "PDF uploaded and indexed successfully",
        "session_id": session_id,
        "filename": filename,
        "saved_path": pdf_path,
        "topic_id": topic_id,
        "topic": topic
    }

@app.get("/api/session/{session_id}/pdfs")
def get_session_pdfs(session_id: str):
    """Get all PDF files in a session."""
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    pdf_files = session_manager.get_pdf_files(session_id)
    
    return {
        "session_id": session_id,
        "pdf_count": len(pdf_files),
        "pdf_files": pdf_files
    }

# ===========================
# Vector DB Endpoints
# ===========================

@app.get("/api/vectordb/topics")
def get_vector_db_topics():
    """Get all topics with hierarchical IDs from vector database."""
    try:
        topics = vector_db.get_all_topics()
        hierarchy = vector_db.get_topic_hierarchy()
        doc_count = vector_db.get_document_count()
        
        return {
            "total_documents": doc_count,
            "topics": topics,
            "hierarchy": hierarchy
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vectordb/search")
def search_vector_db(query: str, n_results: int = 5):
    """
    Semantic search across all PDF documents.
    
    Args:
        query: Search query (e.g., "tell me about Flask routing")
        n_results: Number of results to return (default: 5)
    """
    try:
        results = vector_db.semantic_search(query, n_results)
        
        return {
            "query": query,
            "result_count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vectordb/topic/{topic_id}")
def get_documents_by_topic_id(topic_id: str, n_results: int = 10):
    """
    Get all documents for a specific topic ID.
    
    Args:
        topic_id: Hierarchical topic ID (e.g., "1", "1.1", "2")
        n_results: Maximum results to return
    """
    try:
        results = vector_db.search_by_topic_id(topic_id, n_results)
        
        return {
            "topic_id": topic_id,
            "result_count": len(results),
            "documents": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/vectordb/topic/{topic_id}")
def delete_topic_documents(topic_id: str):
    """Delete all documents with a specific topic ID."""
    try:
        vector_db.delete_by_topic_id(topic_id)
        return {"message": f"Deleted all documents with topic ID: {topic_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vectordb/stats")
def get_vector_db_stats():
    """Get vector database statistics."""
    try:
        topics = vector_db.get_all_topics()
        doc_count = vector_db.get_document_count()
        
        main_topics = [t for t in topics.values() if t.get("parent") is None]
        subtopics = [t for t in topics.values() if t.get("parent") is not None]
        
        return {
            "total_documents": doc_count,
            "total_topics": len(topics),
            "main_topics": len(main_topics),
            "subtopics": len(subtopics),
            "topics_list": list(topics.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Additional endpoints for future features
@app.get("/api/topics")
def list_topics():
    """List available AI/ML topics."""
    return {
        "topics": [
            "Machine Learning",
            "Neural Networks",
            "Deep Learning",
            "Natural Language Processing",
            "Computer Vision",
            "Reinforcement Learning",
            "Data Science",
            "Algorithms",
            "Statistics",
            "Python Programming"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)