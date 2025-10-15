import os
from typing import Dict, List, Optional, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv

load_dotenv()

class LangChainHandler:
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")        
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.7,
            convert_system_message_to_human=True
        )
        
        # Output parsers
        self.str_parser = StrOutputParser()
        self.json_parser = JsonOutputParser()
    
    def refine_user_input(self, user_input: str, context: str = "") -> str:

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an input refinement assistant. Your job is to:
1. Clarify vague or unclear questions
2. Correct spelling and grammar
3. Add context if needed
4. Make questions more specific and actionable

Keep the user's intent but make it clearer and more professional."""),
            ("human", "Context: {context}\n\nUser Input: {input}\n\nRefined Input:")
        ])
        
        chain = prompt | self.llm | self.str_parser
        
        result = chain.invoke({
            "context": context or "No previous context",
            "input": user_input
        })
        
        return result.strip()
    
    def generate_explanation(
        self, 
        question: str, 
        difficulty: str = "beginner",
        context: str = ""
    ) -> Dict[str, str]:
        """
        Generate comprehensive explanation with structured output
        
        Args:
            question: The question to explain
            difficulty: Difficulty level (beginner/intermediate/professional)
            context: Additional context
            
        Returns:
            Dict with explanation, example, and key_points
        """
        
        # Define difficulty-specific system prompts
        difficulty_prompts = {
            "beginner": """You are a friendly and patient teacher explaining to absolute beginners. 
- Use simple, everyday language with NO jargon
- Explain concepts like you're talking to someone with no prior knowledge
- Use analogies and real-world comparisons
- Break down complex ideas into simple steps
- Be encouraging and avoid overwhelming details""",
            
            "intermediate": """You are an experienced educator teaching intermediate learners.
- Assume basic foundational knowledge exists
- Use technical terms but explain them when first introduced
- Provide deeper insights and connections between concepts
- Include practical applications and use cases
- Balance theory with hands-on understanding""",
            
            "professional": """You are an expert consultant addressing professionals and advanced practitioners.
- Use industry-standard terminology and technical precision
- Assume strong foundational knowledge and skip basics
- Focus on advanced patterns, best practices, and optimization
- Discuss edge cases, trade-offs, and architectural considerations
- Reference research papers, industry standards, and cutting-edge techniques"""
        }
        
        system_prompt = difficulty_prompts.get(difficulty, difficulty_prompts["beginner"])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{system_prompt}

Your response must be in this exact JSON format:
{{{{
    "explanation": "Clear, concise explanation tailored to {difficulty} level",
    "example": "Relevant real-world example that resonates with {difficulty} learners",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "further_reading": "Suggested next topics appropriate for {difficulty} level"
}}}}

Remember: Adapt your language, depth, and examples specifically for {difficulty} learners."""),
            ("human", "Context: {context}\n\nQuestion: {question}\n\nDifficulty Level: {difficulty}")
        ])
        
        chain = prompt | self.llm | self.json_parser
        
        try:
            result = chain.invoke({
                "question": question,
                "difficulty": difficulty,
                "context": context or "No additional context"
            })
            return result
        except Exception as e:
            # Fallback to simple format
            fallback_prompt = ChatPromptTemplate.from_messages([
                ("system", f"Explain the following at {difficulty} level with an example:"),
                ("human", "{question}")
            ])
            fallback_chain = fallback_prompt | self.llm | self.str_parser
            explanation = fallback_chain.invoke({"question": question})
            
            return {
                "explanation": explanation,
                "example": "See explanation above",
                "key_points": [],
                "further_reading": ""
            }
    
    def generate_flashcards(
        self, 
        topic: str, 
        count: int = 5,
        difficulty: str = "intermediate"
    ) -> List[Dict[str, str]]:
        """
        Generate educational flashcards with LangChain
        
        Args:
            topic: Topic for flashcards
            count: Number of flashcards
            difficulty: Difficulty level (beginner/intermediate/professional)
            
        Returns:
            List of flashcard dictionaries
        """
        
        # Difficulty-specific instructions
        difficulty_instructions = {
            "beginner": """Create flashcards for absolute beginners:
- Use simple, clear language without jargon
- Focus on fundamental concepts and definitions
- Include helpful hints and memory aids
- Make questions straightforward and unambiguous""",
            
            "intermediate": """Create flashcards for intermediate learners:
- Assume basic knowledge and build upon it
- Include technical terms with context
- Test understanding of relationships and applications
- Balance recall with comprehension questions""",
            
            "professional": """Create flashcards for advanced professionals:
- Use industry-standard terminology
- Focus on best practices, patterns, and edge cases
- Include scenario-based questions
- Test deep understanding and practical application"""
        }
        
        instruction = difficulty_instructions.get(difficulty, difficulty_instructions["intermediate"])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a flashcard creation expert. Generate {{count}} high-quality flashcards.

{instruction}

Return JSON array format:
[
    {{{{
        "front": "Question or prompt appropriate for {difficulty} level",
        "back": "Clear, accurate answer tailored to {difficulty} audience",
        "hint": "Optional hint that guides without giving away the answer"
    }}}}
]

Adapt complexity and terminology to {difficulty} level."""),
            ("human", "Topic: {topic}\nCount: {count}\nDifficulty: {difficulty}")
        ])
        
        chain = prompt | self.llm | self.json_parser
        
        try:
            result = chain.invoke({
                "topic": topic,
                "count": count,
                "difficulty": difficulty
            })
            return result if isinstance(result, list) else []
        except Exception as e:
            # Fallback
            return [{"front": f"Question about {topic}", "back": "Answer", "hint": ""}]
    
    def generate_quiz(
        self, 
        topic: str, 
        count: int = 5,
        difficulty: str = "intermediate"
    ) -> List[Dict[str, Any]]:
        """
        Generate quiz questions with multiple choice options
        
        Args:
            topic: Quiz topic
            count: Number of questions
            difficulty: Difficulty level (beginner/intermediate/professional)
            
        Returns:
            List of quiz question dictionaries
        """
        
        # Difficulty-specific quiz instructions
        difficulty_instructions = {
            "beginner": """Create beginner-friendly multiple-choice questions:
- Focus on basic concepts and fundamental understanding
- Use clear, simple language in questions and options
- Make correct answers obvious for learning reinforcement
- Include encouraging explanations that teach
- Avoid trick questions or confusing distractors""",
            
            "intermediate": """Create intermediate-level multiple-choice questions:
- Test understanding of relationships and applications
- Use technical terminology appropriately
- Include plausible distractors that test real comprehension
- Require thinking beyond simple recall
- Provide explanations that deepen understanding""",
            
            "professional": """Create professional-level multiple-choice questions:
- Test expert knowledge, best practices, and edge cases
- Use industry-standard terminology
- Include subtle distractors that only experts can identify
- Test scenario-based problem solving
- Provide explanations with technical depth and references"""
        }
        
        instruction = difficulty_instructions.get(difficulty, difficulty_instructions["intermediate"])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a quiz generation expert. Create {{count}} multiple-choice questions.

{instruction}

Return JSON array:
[
    {{{{
        "question": "Question text appropriate for {difficulty} learners",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "Correct option text (must match one of the options exactly)",
        "explanation": "Clear explanation of why this is correct, tailored to {difficulty} level"
    }}}}
]

Ensure all elements match the {difficulty} difficulty level."""),
            ("human", "Topic: {topic}\nCount: {count}\nDifficulty: {difficulty}")
        ])
        
        chain = prompt | self.llm | self.json_parser
        
        try:
            result = chain.invoke({
                "topic": topic,
                "count": count,
                "difficulty": difficulty
            })
            return result if isinstance(result, list) else []
        except Exception:
            return []
    
    def generate_demo(
        self, 
        concept: str,
        complexity: str = "simple"
    ) -> Dict[str, Any]:
        """
        Generate step-by-step demonstration
        
        Args:
            concept: Concept to demonstrate
            complexity: Complexity level
            
        Returns:
            Dict with steps and explanation
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Create a step-by-step demonstration. Return JSON:
{{
    "title": "Demonstration title",
    "steps": [
        {{"step": 1, "description": "First step", "code": "code example if applicable"}},
        {{"step": 2, "description": "Second step", "code": "code example if applicable"}}
    ],
    "summary": "Summary of what was demonstrated",
    "tips": ["Tip 1", "Tip 2"]
}}

Complexity: {complexity}"""),
            ("human", "Concept: {concept}")
        ])
        
        chain = prompt | self.llm | self.json_parser
        
        try:
            return chain.invoke({"concept": concept, "complexity": complexity})
        except Exception:
            return {"title": concept, "steps": [], "summary": "", "tips": []}
    
    def generate_example_code(
        self,
        topic: str,
        difficulty: str = "intermediate",
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        Generate professional, production-ready code examples
        
        Args:
            topic: Programming topic or concept
            difficulty: Difficulty level (beginner/intermediate/professional)
            language: Programming language (default: python)
            
        Returns:
            Dict with code, explanation, and best practices
        """
        
        # Difficulty-specific code generation instructions
        difficulty_instructions = {
            "beginner": """Generate beginner-friendly code:
- Start with simple, clear examples
- Use basic syntax and common patterns
- Include extensive comments explaining each step
- Avoid advanced features or optimization
- Focus on readability and learning
- Include print statements to show what's happening""",
            
            "intermediate": """Generate intermediate-level code:
- Use proper programming patterns and conventions
- Include error handling and edge cases
- Use standard library features appropriately
- Balance readability with efficiency
- Include docstrings and moderate comments
- Show practical, real-world usage""",
            
            "professional": """Generate professional, production-ready code:
- Follow industry best practices and design patterns
- Include comprehensive error handling and validation
- Use type hints, documentation, and minimal but precise comments
- Optimize for performance and maintainability
- Include testing considerations
- Show enterprise-grade, scalable solutions
- Follow PEP 8 and style guides religiously"""
        }
        
        instruction = difficulty_instructions.get(difficulty, difficulty_instructions["intermediate"])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are an expert software engineer creating {language} code examples.

{instruction}

Return JSON format:
{{{{
    "code": "Complete, working {language} code example",
    "explanation": "Clear explanation of how the code works, tailored to {difficulty} level",
    "key_concepts": ["Concept 1", "Concept 2", "Concept 3"],
    "best_practices": ["Best practice 1", "Best practice 2"],
    "usage_example": "How to run or use this code",
    "common_pitfalls": ["Pitfall 1 to avoid", "Pitfall 2 to avoid"],
    "next_steps": "What to learn or improve next"
}}}}

Requirements:
- Code must be complete, tested, and ready to run
- Follow {language} best practices and conventions
- Include proper error handling (except for beginner level)
- Use meaningful variable names
- Make it production-quality for professional level
- Adapt complexity to {difficulty} level"""),
            ("human", "Topic: {topic}\nLanguage: {language}\nDifficulty: {difficulty}")
        ])
        
        chain = prompt | self.llm | self.json_parser
        
        try:
            result = chain.invoke({
                "topic": topic,
                "language": language,
                "difficulty": difficulty
            })
            return result
        except Exception as e:
            # Fallback
            fallback_prompt = ChatPromptTemplate.from_messages([
                ("system", f"Generate a {language} code example for the following topic at {difficulty} level:"),
                ("human", "{topic}")
            ])
            fallback_chain = fallback_prompt | self.llm | self.str_parser
            code = fallback_chain.invoke({"topic": topic})
            
            return {
                "code": code,
                "explanation": f"Code example for {topic}",
                "key_concepts": [],
                "best_practices": [],
                "usage_example": "Run the code directly",
                "common_pitfalls": [],
                "next_steps": f"Practice and experiment with {topic}"
            }
    
    def generate_flowchart(self, concept: str) -> Dict[str, Any]:
        """
        Generate flowchart structure in Mermaid format
        
        Args:
            concept: Concept to create flowchart for
            
        Returns:
            Dict with flowchart data
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Create a flowchart for the given concept. Return JSON:
{{
    "title": "Flowchart title",
    "mermaid": "graph TD\\nA[Start] --> B[Step 1]\\nB --> C[Step 2]",
    "description": "Description of the flow",
    "nodes": [
        {{"id": "A", "label": "Start", "type": "start"}},
        {{"id": "B", "label": "Step 1", "type": "process"}}
    ]
}}

Use proper Mermaid.js syntax."""),
            ("human", "Concept: {concept}")
        ])
        
        chain = prompt | self.llm | self.json_parser
        
        try:
            return chain.invoke({"concept": concept})
        except Exception:
            return {
                "title": concept,
                "mermaid": "graph TD\nA[Start]",
                "description": "",
                "nodes": []
            }
    
    def generate_thought_questions(
        self, 
        topic: str,
        count: int = 5
    ) -> List[str]:
        """
        Generate thought-provoking questions
        
        Args:
            topic: Topic for questions
            count: Number of questions
            
        Returns:
            List of thought-provoking questions
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Generate {count} thought-provoking, open-ended questions that encourage critical thinking.

Return as JSON array:
["Question 1?", "Question 2?", "Question 3?"]

Questions should:
- Encourage deep thinking
- Connect to real-world applications
- Challenge assumptions
- Promote creative problem-solving"""),
            ("human", "Topic: {topic}")
        ])
        
        chain = prompt | self.llm | self.json_parser
        
        try:
            result = chain.invoke({"topic": topic, "count": count})
            return result if isinstance(result, list) else []
        except Exception:
            return []
    
    def analyze_code(
        self, 
        code: str, 
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        Analyze code and provide insights
        
        Args:
            code: Code to analyze
            language: Programming language
            
        Returns:
            Analysis results
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Analyze the provided {language} code. Return JSON:
{{
    "summary": "What the code does",
    "complexity": "Time and space complexity",
    "strengths": ["Strength 1", "Strength 2"],
    "improvements": ["Suggestion 1", "Suggestion 2"],
    "best_practices": ["Practice 1", "Practice 2"],
    "explanation": "Line-by-line explanation"
}}"""),
            ("human", "Language: {language}\n\nCode:\n{code}")
        ])
        
        chain = prompt | self.llm | self.json_parser
        
        try:
            return chain.invoke({"code": code, "language": language})
        except Exception:
            return {
                "summary": "Code analysis",
                "complexity": "Unknown",
                "strengths": [],
                "improvements": [],
                "best_practices": [],
                "explanation": ""
            }
    
    def summarize_context(self, context_list: List[str]) -> str:
        """
        Summarize multiple context entries into coherent summary
        
        Args:
            context_list: List of context entries
            
        Returns:
            Summarized context
        """
        if not context_list:
            return "No context available"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Summarize the following context into a concise, coherent summary:"),
            ("human", "{context}")
        ])
        
        chain = prompt | self.llm | self.str_parser
        
        combined_context = "\n".join(context_list)
        result = chain.invoke({"context": combined_context})
        
        return result.strip()
    
    def extract_pdf_insights(self, pdf_text: str, query: str = "") -> Dict[str, Any]:
        """
        Extract key insights from PDF content
        
        Args:
            pdf_text: Extracted PDF text
            query: Optional specific query about the PDF
            
        Returns:
            Dict with insights
        """
        if query:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """Analyze the PDF content and answer the query. Return JSON:
{{
    "answer": "Direct answer to the query",
    "relevant_sections": ["Key section 1", "Key section 2"],
    "summary": "Brief summary of relevant content"
}}"""),
                ("human", "PDF Content:\n{pdf_text}\n\nQuery: {query}")
            ])
        else:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """Analyze the PDF and extract key insights. Return JSON:
{{
    "main_topics": ["Topic 1", "Topic 2"],
    "key_points": ["Point 1", "Point 2"],
    "summary": "Overall summary",
    "difficulty_level": "beginner/intermediate/advanced"
}}"""),
                ("human", "PDF Content:\n{pdf_text}")
            ])
        
        chain = prompt | self.llm | self.json_parser
        
        try:
            return chain.invoke({"pdf_text": pdf_text[:5000], "query": query})  # Limit text length
        except Exception:
            return {
                "answer": "Unable to process",
                "relevant_sections": [],
                "summary": "",
                "main_topics": [],
                "key_points": [],
                "difficulty_level": "unknown"
            }


# Singleton instance
_langchain_handler = None

def get_langchain_handler() -> LangChainHandler:
    """Get or create singleton LangChain handler instance"""
    global _langchain_handler
    if _langchain_handler is None:
        _langchain_handler = LangChainHandler()
    return _langchain_handler
