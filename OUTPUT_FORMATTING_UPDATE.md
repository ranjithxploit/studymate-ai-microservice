# Output Formatting Update

## Summary
Updated the AI server to provide properly formatted outputs for frontend rendering:
1. **Explanation endpoint**: Now returns Markdown-formatted text
2. **Flowchart endpoint**: Fixed to return proper Mermaid.js diagram code

## Changes Made

### 1. Explanation Endpoint - Markdown Formatting

**File**: `langchain_handler.py` - `generate_explanation()` method

**What Changed**:
- Updated the system prompt to request Markdown formatting in both `explanation` and `example` fields
- AI now uses proper Markdown syntax including:
  - Headers (`##`, `###`) for sections
  - `**Bold**` for emphasis
  - `*Italic*` for terminology
  - `` `code` `` for technical terms
  - Bullet points (`-`) for lists
  - `>` for important notes/quotes
  - Code blocks (` ```language ``` `) for code examples

**Example Output**:
```json
{
  "explanation": "## What is Machine Learning?\n\nMachine Learning is a subset of **AI** that allows computers to learn from data...\n\n### Key Concepts:\n- **Training**: The process of...\n- **Prediction**: Using the model to...",
  "example": "### Real-World Example\n\nConsider a **spam filter** for email:\n\n```python\n# Simple example\nif contains_spam_words(email):\n    mark_as_spam()\n```",
  "key_points": ["...", "..."],
  "further_reading": "..."
}
```

### 2. Flowchart Endpoint - Mermaid.js Integration

**File**: `langchain_handler.py` - `generate_flowchart()` method

**What Changed**:
- Fixed field name from `"mermaid"` to `"mermaid_code"` (matches `FlowchartResponse` model)
- Added `"steps"` array that was missing (required by endpoint)
- Enhanced Mermaid syntax examples in the prompt
- Added fallback logic to ensure correct field names even if AI returns old format
- Improved fallback diagram with better structure

**Mermaid Syntax Examples**:
```
graph TD
    A[Start] --> B[Process Step]
    B --> C{Decision?}
    C -->|Yes| D[Option 1]
    C -->|No| E[Option 2]
    D --> F[End]
    E --> F
```

**Example Output**:
```json
{
  "title": "Machine Learning Process",
  "mermaid_code": "graph TD\n    A[Collect Data] --> B[Preprocess]\n    B --> C[Train Model]\n    C --> D{Accurate?}\n    D -->|Yes| E[Deploy]\n    D -->|No| B",
  "steps": [
    "Step 1: Collect training data",
    "Step 2: Preprocess and clean the data",
    "Step 3: Train the model",
    "Step 4: Evaluate accuracy",
    "Step 5: Deploy if accurate"
  ],
  "description": "End-to-end machine learning workflow"
}
```

## API Response Structure

### Explanation Response (`/api/explain`)
```typescript
{
  question: string;          // The refined question
  explanation: string;       // ✨ NOW IN MARKDOWN FORMAT
  example: string;          // ✨ NOW IN MARKDOWN FORMAT  
  levels: string;           // beginner/university/researcher
  session_id: string;
  pdf_chunks?: Array<{      // Optional: if PDF uploaded
    chunk_text: string;
    page_number: number;
    chunk_index: number;
    relevance_score: number;
    filename: string;
  }>;
}
```

### Flowchart Response (`/api/flowchart`)
```typescript
{
  concept: string;          // The concept being visualized
  steps: string[];          // ✨ FIXED: Array of step descriptions
  mermaid_code: string;     // ✨ FIXED: Proper Mermaid.js syntax
  session_id: string;
}
```

## Frontend Integration

### Rendering Markdown Explanations
```javascript
// React example with react-markdown
import ReactMarkdown from 'react-markdown';

function ExplanationView({ explanation, example }) {
  return (
    <div>
      <ReactMarkdown>{explanation}</ReactMarkdown>
      <ReactMarkdown>{example}</ReactMarkdown>
    </div>
  );
}
```

### Rendering Mermaid Diagrams
```javascript
// React example with react-mermaid or mermaid.js
import Mermaid from 'react-mermaid';

function FlowchartView({ mermaid_code }) {
  return <Mermaid chart={mermaid_code} />;
}

// Or using mermaid.js directly
import mermaid from 'mermaid';

useEffect(() => {
  mermaid.initialize({ startOnLoad: true });
  mermaid.contentLoaded();
}, [mermaid_code]);

return <div className="mermaid">{mermaid_code}</div>;
```

## Testing

### Test Explanation Endpoint
```bash
curl -X POST http://localhost:8000/api/explain \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is machine learning?",
    "levels": "beginner",
    "session_id": ""
  }'
```

Check that `explanation` and `example` fields contain Markdown syntax.

### Test Flowchart Endpoint
```bash
curl -X POST http://localhost:8000/api/flowchart \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "<your_session_id>",
    "concept": "machine learning process"
  }'
```

Check that `mermaid_code` field contains valid Mermaid.js syntax (starts with `graph TD` or `graph LR`).

## Benefits

1. **Better Readability**: Markdown formatting makes explanations more structured and easier to read
2. **Visual Diagrams**: Mermaid.js enables interactive flowcharts that can be zoomed/panned
3. **Frontend Flexibility**: Frontend can now render rich content without manual parsing
4. **Professional Output**: Properly formatted output looks more polished and professional
5. **Code Highlighting**: Code blocks in examples get syntax highlighting automatically

## Notes

- All existing functionality remains unchanged - only the output format improved
- Backward compatible: Frontends can still treat responses as plain text if needed
- The AI is instructed to use Markdown, but fallback plain text still works
- Mermaid syntax is standard and works with all Mermaid.js libraries
- The `steps` array provides text descriptions for accessibility and alternate views

## Mermaid.js Resources

- Official docs: https://mermaid.js.org/
- Syntax guide: https://mermaid.js.org/syntax/flowchart.html
- Live editor: https://mermaid.live/
- React library: https://www.npmjs.com/package/react-mermaid

## Markdown Resources

- CommonMark spec: https://commonmark.org/
- React library: https://www.npmjs.com/package/react-markdown
- GitHub Flavored Markdown: https://github.github.com/gfm/
