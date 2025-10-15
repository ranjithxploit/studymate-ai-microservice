import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import google.generativeai as genai
import dotenv
from session_manager import session_manager

# Load environment variables
dotenv.load_dotenv()

# Configure Google Generative AI
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set. Set it in the environment or a .env file.")

genai.configure(api_key=API_KEY)
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Initialize FastAPI
app = FastAPI(
    title="AI Explainer Bot API",
    description="Educational AI API for explaining concepts, generating quizzes, flashcards, and more",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
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
    difficulty: Optional[str] = Field("medium", example="medium")
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

# Session Management Models
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

# Helper function to call AI
def call_ai(prompt: str) -> str:
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        return getattr(response, "text", None) or str(response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI request failed: {str(e)}")

@app.get("/")
def read_root():
    """Root endpoint with API information."""
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
    """
    # Create or get session
    session_id = request.session_id
    if not session_id or not session_manager.session_exists(session_id):
        session_id = session_manager.create_session()
    
    # Save input
    session_manager.save_text_input(session_id, request.question, "question")
    session_manager.save_context(session_id, f"Topic: {request.question}\nDifficulty: {request.difficulty}")
    
    prompt = f"""You are an educational AI assistant. Explain the following concept in {request.difficulty} level terms.
    
Question: {request.question}

Provide your response in this exact format:
EXPLANATION: [Your clear, simple explanation here]
EXAMPLE: [A real-world example that illustrates this concept]

Keep it concise and easy to understand."""

    response_text = call_ai(prompt)
    
    # Parse the response
    explanation = ""
    example = ""
    
    if "EXPLANATION:" in response_text and "EXAMPLE:" in response_text:
        parts = response_text.split("EXAMPLE:")
        explanation = parts[0].replace("EXPLANATION:", "").strip()
        example = parts[1].strip()
    else:
        # Fallback if format isn't followed
        lines = response_text.strip().split("\n")
        explanation = response_text
        example = "Example: Spam email filter uses ML to classify emails."
    
    # Save history
    session_manager.save_history(
        session_id,
        request.question,
        f"Explanation: {explanation}\nExample: {example}",
        "explain"
    )
    
    return ExplainResponse(
        question=request.question,
        explanation=explanation,
        example=example,
        difficulty=request.difficulty or "beginner",
        session_id=session_id
    )

@app.post("/api/flashcards", response_model=FlashcardResponse)
def generate_flashcards(request: FlashcardRequest):
    """Generate educational flashcards. Tracks session automatically."""
    # Create or get session
    session_id = request.session_id
    if not session_id or not session_manager.session_exists(session_id):
        session_id = session_manager.create_session()
    
    # Save input
    session_manager.save_text_input(session_id, request.topic, "flashcard_topic")
    session_manager.save_context(session_id, f"Generating {request.count} flashcards about: {request.topic}")
    
    prompt = f"""Create {request.count} educational flashcards about "{request.topic}".

Format each flashcard as:
CARD [number]:
FRONT: [Question or term]
BACK: [Answer or definition]

Make them educational and helpful for learning."""

    response_text = call_ai(prompt)
    flashcards = []
    cards = response_text.split("CARD")
    
    for card in cards[1:]:
        if "FRONT:" in card and "BACK:" in card:
            try:
                front_back = card.split("BACK:")
                front = front_back[0].split("FRONT:")[1].strip()
                back = front_back[1].strip()
                flashcards.append(Flashcard(front=front, back=back))
            except:
                continue
    if not flashcards:
        flashcards = [
            Flashcard(
                front=f"What is {request.topic}?",
                back=response_text[:200]
            )
        ]
    
    # Save history
    session_manager.save_history(
        session_id,
        f"Generate flashcards for: {request.topic}",
        f"Generated {len(flashcards)} flashcards",
        "flashcards"
    )
    
    return FlashcardResponse(topic=request.topic, flashcards=flashcards, session_id=session_id)

@app.post("/api/quiz", response_model=QuizResponse)
def generate_quiz(request: QuizRequest):
    """Generate quiz questions. Tracks session automatically."""
    # Create or get session
    session_id = request.session_id
    if not session_id or not session_manager.session_exists(session_id):
        session_id = session_manager.create_session()
    
    # Save input
    session_manager.save_text_input(session_id, request.topic, "quiz_topic")
    session_manager.save_context(session_id, f"Generating {request.num_questions} quiz questions about: {request.topic} (Difficulty: {request.difficulty})")
    
    prompt = f"""Create a {request.difficulty} level quiz about "{request.topic}" with {request.num_questions} multiple choice questions.

Format each question as:
QUESTION [number]: [The question text]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
CORRECT: [A/B/C/D]
EXPLANATION: [Why this is the correct answer]

Make questions educational and clear."""

    response_text = call_ai(prompt)
    questions = []
    question_blocks = response_text.split("QUESTION")[1:]
    
    for block in question_blocks:
        try:
            lines = block.strip().split("\n")
            question_text = lines[0].split(":", 1)[1].strip() if ":" in lines[0] else lines[0].strip()
            
            options = []
            correct_letter = ""
            explanation = ""
            
            for line in lines[1:]:
                line = line.strip()
                if line.startswith(("A)", "B)", "C)", "D)")):
                    options.append(line[3:].strip())
                elif line.startswith("CORRECT:"):
                    correct_letter = line.split(":")[1].strip()[0]
                elif line.startswith("EXPLANATION:"):
                    explanation = line.split(":", 1)[1].strip()
            
            if options and correct_letter:
                correct_index = ord(correct_letter.upper()) - ord('A')
                if 0 <= correct_index < len(options):
                    questions.append(QuizQuestion(
                        question=question_text,
                        options=options,
                        correct_answer=options[correct_index],
                        explanation=explanation or "Correct!"
                    ))
        except:
            continue
    
    # Fallback
    if not questions:
        questions = [QuizQuestion(
            question=f"What is {request.topic}?",
            options=["Option A", "Option B", "Option C", "Option D"],
            correct_answer="Option A",
            explanation="This is a sample question."
        )]
    
    # Save history
    session_manager.save_history(
        session_id,
        f"Generate quiz for: {request.topic}",
        f"Generated {len(questions)} quiz questions",
        "quiz"
    )
    
    return QuizResponse(topic=request.topic, questions=questions, session_id=session_id)

@app.post("/api/demo", response_model=DemoResponse)
def generate_demo(request: DemoRequest):
    """Generate code demonstration. Tracks session automatically."""
    # Create or get session
    session_id = request.session_id
    if not session_id or not session_manager.session_exists(session_id):
        session_id = session_manager.create_session()
    
    # Save input
    session_manager.save_text_input(session_id, request.concept, "demo_concept")
    session_manager.save_context(session_id, f"Generating code demo for: {request.concept}")
    
    prompt = f"""Create a simple Python code demonstration for "{request.concept}".

Provide:
1. Working Python code (well-commented)
2. Explanation of what the code does
3. Example output

Format:
CODE:
```python
[your code here]
```

EXPLANATION:
[explanation here]

OUTPUT:
[example output]"""

    response_text = call_ai(prompt)
    
    # Parse response
    code = ""
    explanation = ""
    output = ""
    
    if "```python" in response_text:
        code_parts = response_text.split("```python")
        if len(code_parts) > 1:
            code = code_parts[1].split("```")[0].strip()
    
    if "EXPLANATION:" in response_text:
        expl_parts = response_text.split("EXPLANATION:")
        if len(expl_parts) > 1:
            explanation = expl_parts[1].split("OUTPUT:")[0].strip() if "OUTPUT:" in expl_parts[1] else expl_parts[1].strip()
    
    if "OUTPUT:" in response_text:
        output = response_text.split("OUTPUT:")[1].strip()
    
    # Fallbacks
    if not code:
        code = f"# Demo code for {request.concept}\nprint('Hello World')"
    if not explanation:
        explanation = f"This demonstrates {request.concept}"
    if not output:
        output = "Sample output"
    
    # Save history
    session_manager.save_history(
        session_id,
        f"Generate demo for: {request.concept}",
        f"Code demo generated",
        "demo"
    )
    
    return DemoResponse(
        concept=request.concept,
        demo_code=code,
        explanation=explanation,
        output_example=output,
        session_id=session_id
    )

@app.post("/api/flowchart", response_model=FlowchartResponse)
def generate_flowchart(request: FlowchartRequest):
    """Generate flowchart/process diagram. Tracks session automatically."""
    # Create or get session
    session_id = request.session_id
    if not session_id or not session_manager.session_exists(session_id):
        session_id = session_manager.create_session()
    
    # Save input
    session_manager.save_text_input(session_id, request.concept, "flowchart_concept")
    session_manager.save_context(session_id, f"Generating flowchart for: {request.concept}")
    
    prompt = f"""Create a step-by-step process flowchart for "{request.concept}".

Provide:
1. Numbered steps (clear and concise)
2. Mermaid.js flowchart code

Format:
STEPS:
1. [Step 1]
2. [Step 2]
...

MERMAID:
```mermaid
[mermaid flowchart code]
```"""

    response_text = call_ai(prompt)
    
    # Parse steps
    steps = []
    mermaid_code = ""
    
    if "STEPS:" in response_text:
        steps_section = response_text.split("STEPS:")[1]
        if "MERMAID:" in steps_section:
            steps_section = steps_section.split("MERMAID:")[0]
        
        for line in steps_section.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                steps.append(line)
    
    if "```mermaid" in response_text:
        mermaid_parts = response_text.split("```mermaid")
        if len(mermaid_parts) > 1:
            mermaid_code = mermaid_parts[1].split("```")[0].strip()
    
    # Fallbacks
    if not steps:
        steps = [
            f"1. Understand {request.concept}",
            "2. Apply the concept",
            "3. Evaluate results"
        ]
    
    if not mermaid_code:
        mermaid_code = "graph TD\n    A[Start] --> B[Process]\n    B --> C[End]"
    
    # Save history
    session_manager.save_history(
        session_id,
        f"Generate flowchart for: {request.concept}",
        f"Flowchart generated with {len(steps)} steps",
        "flowchart"
    )
    
    return FlowchartResponse(
        concept=request.concept,
        steps=steps,
        mermaid_code=mermaid_code,
        session_id=session_id
    )

@app.post("/api/thought-questions", response_model=ThoughtResponse)
def generate_thought_questions(request: ThoughtRequest):
    """Generate thought-provoking questions. Tracks session automatically."""
    # Create or get session
    session_id = request.session_id
    if not session_id or not session_manager.session_exists(session_id):
        session_id = session_manager.create_session()
    
    # Save input
    session_manager.save_text_input(session_id, request.topic, "thought_topic")
    session_manager.save_context(session_id, f"Generating {request.count} thought questions about: {request.topic}")
    
    prompt = f"""Generate {request.count} thought-provoking questions about "{request.topic}".

These should be deep, open-ended questions that encourage critical thinking and discussion.

Format as a numbered list:
1. [Question 1]
2. [Question 2]
..."""

    response_text = call_ai(prompt)
    
    # Parse questions
    questions = []
    for line in response_text.split("\n"):
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith("-")):
            # Remove numbering
            question = line.split(".", 1)[1].strip() if "." in line else line.strip("- ")
            if question:
                questions.append(question)
    
    # Fallback
    if not questions:
        questions = [f"How does {request.topic} impact our daily lives?"]
    
    # Save history
    session_manager.save_history(
        session_id,
        f"Generate thought questions for: {request.topic}",
        f"Generated {len(questions)} thought-provoking questions",
        "thought_questions"
    )
    
    return ThoughtResponse(topic=request.topic, questions=questions, session_id=session_id)

@app.post("/api/execute-code", response_model=CodeExecutionResponse)
def execute_code(request: CodeExecutionRequest):
    """Analyze/execute code (simulated). Tracks session automatically."""
    # Create or get session
    session_id = request.session_id
    if not session_id or not session_manager.session_exists(session_id):
        session_id = session_manager.create_session()
    
    # Save input
    session_manager.save_text_input(session_id, request.code, "code_execution")
    session_manager.save_context(session_id, f"Analyzing {request.language} code execution")
    
    # NOTE: For security reasons, we don't actually execute arbitrary code
    # Instead, we use AI to simulate/explain what the code would do
    
    prompt = f"""Analyze this Python code and tell me what it would output:

```python
{request.code}
```

Provide:
1. The expected output
2. Any errors if the code has issues
3. Brief explanation

Format:
OUTPUT: [what the code outputs]
ERROR: [any errors, or "None"]
EXPLANATION: [brief explanation]"""

    response_text = call_ai(prompt)
    
    # Parse response
    output = ""
    error = None
    
    if "OUTPUT:" in response_text:
        output_section = response_text.split("OUTPUT:")[1]
        if "ERROR:" in output_section:
            output = output_section.split("ERROR:")[0].strip()
        else:
            output = output_section.strip()
    
    if "ERROR:" in response_text:
        error_section = response_text.split("ERROR:")[1]
        if "EXPLANATION:" in error_section:
            error_text = error_section.split("EXPLANATION:")[0].strip()
        else:
            error_text = error_section.strip()
        
        if error_text and error_text.lower() != "none":
            error = error_text
    
    # Save history
    session_manager.save_history(
        session_id,
        f"Execute code: {request.code[:50]}...",
        f"Output: {output[:100]}",
        "code_execution"
    )
    
    return CodeExecutionResponse(
        output=output or "Code analysis completed",
        error=error,
        execution_time="simulated",
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
async def upload_pdf(session_id: str, file: UploadFile = File(...)):
    """Upload a PDF file to a session."""
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    # Check file type
    filename = file.filename or "input.pdf"
    if not filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Read file content
    content = await file.read()
    
    # Save PDF
    pdf_path = session_manager.save_pdf_input(session_id, content, filename)
    
    return {
        "message": "PDF uploaded successfully",
        "session_id": session_id,
        "filename": filename,
        "saved_path": pdf_path
    }

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