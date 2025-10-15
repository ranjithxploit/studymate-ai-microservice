# AI Explainer Bot API 🤖

A comprehensive FastAPI-based backend server that provides AI-powered educational content including explanations, flashcards, quizzes, demos, flowcharts, and more.

## 🚀 Features

- **Concept Explanations**: Get simple, beginner-friendly explanations of AI/ML concepts with examples
- **Flashcards**: Generate educational flashcards for any topic
- **Quizzes**: Create multiple-choice quizzes with explanations
- **Code Demos**: Get working code demonstrations with explanations
- **Flowcharts**: Generate step-by-step process diagrams (with Mermaid.js support)
- **Thought-Provoking Questions**: Get deep questions to encourage critical thinking
- **Code Execution Analysis**: Analyze Python code and predict outputs
- **Topics List**: Browse available AI/ML topics

## 📋 Prerequisites

- Python 3.8+
- Google Gemini API Key

## 🔧 Installation

1. **Clone or navigate to the project directory:**
```bash
cd d:\ranjith-projects\python-ai-server
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**

Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Or set environment variables in PowerShell:
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

## 🏃 Running the Server

### Development Mode (with auto-reload):
```bash
python -m uvicorn server:app --reload
```

### Production Mode:
```bash
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

The server will start at: **http://127.0.0.1:8000**

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 🔌 API Endpoints

### 1. Health Check
```
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "model": "gemini-2.5-flash"
}
```

### 2. Explain Concept
```
POST /api/explain
```
**Request Body:**
```json
{
  "question": "What is machine learning?",
  "difficulty": "beginner"
}
```
**Response:**
```json
{
  "question": "What is machine learning?",
  "explanation": "Machine Learning is a type of AI that allows computers to learn from data...",
  "example": "Example: Spam email filter uses ML to classify emails as spam or not spam.",
  "difficulty": "beginner"
}
```

### 3. Generate Flashcards
```
POST /api/flashcards
```
**Request Body:**
```json
{
  "topic": "Neural Networks",
  "count": 5
}
```
**Response:**
```json
{
  "topic": "Neural Networks",
  "flashcards": [
    {
      "front": "What is a Neural Network?",
      "back": "A computational model inspired by biological neural networks..."
    }
  ]
}
```

### 4. Generate Quiz
```
POST /api/quiz
```
**Request Body:**
```json
{
  "topic": "Machine Learning Basics",
  "num_questions": 5,
  "difficulty": "medium"
}
```
**Response:**
```json
{
  "topic": "Machine Learning Basics",
  "questions": [
    {
      "question": "What is supervised learning?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option A",
      "explanation": "Supervised learning uses labeled data..."
    }
  ]
}
```

### 5. Generate Code Demo
```
POST /api/demo
```
**Request Body:**
```json
{
  "concept": "Linear Regression"
}
```
**Response:**
```json
{
  "concept": "Linear Regression",
  "demo_code": "import numpy as np\n# Demo code here...",
  "explanation": "This code demonstrates linear regression...",
  "output_example": "Predicted value: 5.2"
}
```

### 6. Generate Flowchart
```
POST /api/flowchart
```
**Request Body:**
```json
{
  "concept": "How Neural Networks Work"
}
```
**Response:**
```json
{
  "concept": "How Neural Networks Work",
  "steps": [
    "1. Input data is fed into the network",
    "2. Data passes through hidden layers",
    "3. Output layer produces predictions"
  ],
  "mermaid_code": "graph TD\n    A[Input] --> B[Hidden Layer]\n    B --> C[Output]"
}
```

### 7. Thought-Provoking Questions
```
POST /api/thought-questions
```
**Request Body:**
```json
{
  "topic": "Artificial Intelligence",
  "count": 3
}
```
**Response:**
```json
{
  "topic": "Artificial Intelligence",
  "questions": [
    "How will AI impact job markets in the next decade?",
    "What ethical considerations should guide AI development?",
    "Can machines truly understand human emotions?"
  ]
}
```

### 8. Execute Code (Analysis)
```
POST /api/execute-code
```
**Request Body:**
```json
{
  "code": "print('Hello World')",
  "language": "python"
}
```
**Response:**
```json
{
  "output": "Hello World",
  "error": null,
  "execution_time": "simulated"
}
```

### 9. List Topics
```
GET /api/topics
```
**Response:**
```json
{
  "topics": [
    "Machine Learning",
    "Neural Networks",
    "Deep Learning",
    "Natural Language Processing",
    "Computer Vision"
  ]
}
```

## 🧪 Testing

Run the test script:
```bash
python test_api.py
```

Or use curl:
```bash
curl -X POST "http://127.0.0.1:8000/api/explain" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is machine learning?", "difficulty": "beginner"}'
```

## 🔐 CORS Configuration

The API is configured to accept requests from any origin (for development). For production, update the CORS settings in `server.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📦 Project Structure

```
python-ai-server/
├── ai.py              # Simple AI module
├── server.py          # FastAPI application
├── test_api.py        # API testing script
├── requirements.txt   # Python dependencies
├── .env              # Environment variables (create this)
└── README.md         # This file
```

## 🎯 Frontend Integration

Your frontend can call these endpoints using fetch or axios:

```javascript
// Example: Explain a concept
const response = await fetch('http://127.0.0.1:8000/api/explain', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    question: 'What is machine learning?',
    difficulty: 'beginner'
  })
});

const data = await response.json();
console.log(data.explanation);
```

## 🚀 Future Enhancements

Planned features from your problem statement:
- ✅ Explanations with examples
- ✅ Flashcards
- ✅ Quiz generation
- ✅ Code demos
- ✅ Flowcharts
- ✅ Thought-provoking questions
- ⏳ PDF input processing
- ⏳ Adaptive difficulty
- ⏳ Progress tracking (roadmap)
- ⏳ Live code execution (currently simulated)
- ⏳ Prerequisite tracking
- ⏳ Leaderboards (gamification)
- ⏳ Feedback collection
- ⏳ Offline storage
- ⏳ User dashboard
- ⏳ Debugger

## 🛠️ Troubleshooting

### API Key Issues
If you see "GEMINI_API_KEY not set" error:
1. Make sure `.env` file exists with your API key
2. Or set environment variable: `$env:GEMINI_API_KEY="your_key"`

### Port Already in Use
If port 8000 is busy, use a different port:
```bash
python -m uvicorn server:app --reload --port 8001
```

### CORS Errors
Make sure CORS is enabled in `server.py` for your frontend domain.

## 📝 License

This project is for educational purposes.

## 👥 Contributors

- Backend: Your Team
- Frontend: Your Friend's Team

---

**Happy Coding! 🚀**
