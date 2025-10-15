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
        levels: str = "beginner",
        context: str = ""
    ) -> Dict[str, str]:

        levels_prompts = {
            "beginner": """You are a friendly and patient teacher explaining to absolute beginners. 
- Use simple, everyday language with NO jargon
- Explain concepts like you're talking to someone with no prior knowledge
- Use analogies and real-world comparisons
- Break down complex ideas into simple steps
- Be encouraging and avoid overwhelming details""",
            
            "university": """You are a university professor teaching students with solid foundational knowledge.
- Assume basic concepts are understood
- Use academic terminology and explain advanced concepts
- Provide theoretical depth with mathematical/technical foundations
- Include research context and scholarly perspectives
- Balance rigorous explanation with practical applications""",
            
            "researcher": """You are an expert researcher addressing fellow researchers and professionals.
- Use advanced technical terminology and assume expert-level knowledge
- Focus on cutting-edge research, novel approaches, and theoretical implications
- Discuss methodologies, experimental designs, and statistical considerations
- Reference recent papers, ongoing research, and unsolved problems
- Emphasize research gaps, future directions, and potential breakthroughs"""
        }
        
        system_prompt = levels_prompts.get(levels, levels_prompts["beginner"])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{system_prompt}

Your response must be in this exact JSON format:
{{{{
    "explanation": "Clear, concise explanation tailored to {levels} level",
    "example": "Relevant real-world example that resonates with {levels} learners",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "further_reading": "Suggested next topics appropriate for {levels} level"
}}}}

Remember: Adapt your language, depth, and examples specifically for {levels} learners."""),
            ("human", "Context: {context}\n\nQuestion: {question}\n\nContent Level: {levels}")
        ])
        
        chain = prompt | self.llm | self.json_parser
        
        try:
            result = chain.invoke({
                "question": question,
                "levels": levels,
                "context": context or "No additional context"
            })
            return result
        except Exception as e:
            fallback_prompt = ChatPromptTemplate.from_messages([
                ("system", f"Explain the following at {levels} level with an example:"),
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
        levels: str = "beginner", 
        all_topics: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:

        levels_instructions = {
            "beginner": """Create flashcards for absolute beginners:
- Use simple, clear language without jargon
- Focus on fundamental concepts and definitions
- Include helpful hints and memory aids
- Make questions straightforward and unambiguous""",
            
            "university": """Create flashcards for university-level students:
- Assume solid foundational knowledge
- Use academic terminology appropriately
- Test theoretical understanding and analytical skills
- Include conceptual relationships and applications""",
            
            "researcher": """Create flashcards for researchers and experts:
- Use advanced technical terminology
- Focus on research methodologies and cutting-edge concepts
- Test critical analysis and synthesis abilities
- Include complex scenarios and theoretical implications"""
        }
        
        instruction = levels_instructions.get(levels, levels_instructions["beginner"])        
        topics_context = ""
        if all_topics and len(all_topics) > 1:
            topics_context = f"\n\nSession Context: This session has covered these topics in order: {', '.join(all_topics)}. Focus primarily on '{topic}' but you may include some questions from previous topics for reinforcement."
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a flashcard creation expert. Generate {{count}} high-quality flashcards.

{instruction}{topics_context}

Return JSON array format:
[
    {{{{
        "front": "Question or prompt appropriate for {levels} level",
        "back": "Clear, accurate answer tailored to {levels} audience",
        "hint": "Optional hint that guides without giving away the answer"
    }}}}
]

Adapt complexity and terminology to {levels} level."""),
            ("human", "Primary Topic: {topic}\nCount: {count}\nContent Level: {levels}")
        ])
        
        chain = prompt | self.llm | self.json_parser
        
        try:
            result = chain.invoke({
                "topic": topic,
                "count": count,
                "levels": levels
            })
            return result if isinstance(result, list) else []
        except Exception as e:
            return [{"front": f"Question about {topic}", "back": "Answer", "hint": ""}]
    
    def generate_quiz(
        self, 
        topic: str, 
        count: int = 5,
        levels: str = "beginner", 
        quiz_difficulty: str = "medium",
        all_topics: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:

        levels_instructions = {
            "beginner": """Content Level: Beginner
- Focus on basic concepts and fundamental understanding
- Use clear, simple language in questions and options
- Cover foundational terminology and core principles
- Build confidence through clear, unambiguous questions""",
            
            "university": """Content Level: University
- Test theoretical understanding and analytical reasoning
- Use academic terminology and concepts
- Include conceptual relationships and applications
- Require synthesis of multiple ideas""",
            
            "researcher": """Content Level: Researcher
- Test expert knowledge and research methodologies
- Use advanced technical terminology
- Include cutting-edge concepts and novel approaches
- Require critical analysis and deep domain expertise"""
        }
        
        quiz_difficulty_instructions = {
            "easy": """Question Difficulty: Easy
- Make correct answers relatively obvious
- Use straightforward distractors
- Focus on recognition and recall
- Provide clear hints in the question stem""",
            
            "medium": """Question Difficulty: Medium
- Require genuine understanding, not just memorization
- Use plausible distractors that test comprehension
- Balance between recall and application
- Include scenario-based elements""",
            
            "hard": """Question Difficulty: Hard
- Create subtle, tricky distractors
- Test edge cases and exceptions
- Require deep analysis and problem-solving
- Include complex scenarios with multiple considerations"""
        }
        
        levels_instruction = levels_instructions.get(levels, levels_instructions["beginner"])
        difficulty_instruction = quiz_difficulty_instructions.get(quiz_difficulty, quiz_difficulty_instructions["medium"])
        
        priority_instruction = ""
        if all_topics and len(all_topics) > 1:
            other_topics = [t for t in all_topics if t != topic]
            priority_instruction = f"""
IMPORTANT - Topic Distribution:
- Primary focus ({int(70 + (10/len(all_topics)))}% of questions): {topic}
- Secondary topics ({int(30 - (10/len(all_topics)))}% of questions): {', '.join(other_topics)}

This creates a quiz that emphasizes the current topic while reinforcing previous learning.
"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a quiz generation expert. Create {{count}} multiple-choice questions.

{levels_instruction}

{difficulty_instruction}{priority_instruction}

Return JSON array:
[
    {{{{
        "question": "Question text (content at {levels} level, difficulty at {quiz_difficulty} level)",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "Correct option text (must match one of the options exactly)",
        "explanation": "Clear explanation tailored to {levels} learners"
    }}}}
]

Balance content complexity ({levels}) with question difficulty ({quiz_difficulty})."""),
            ("human", "Primary Topic: {topic}\nQuestion Count: {count}\nContent Level: {levels}\nQuestion Difficulty: {quiz_difficulty}")
        ])
        
        chain = prompt | self.llm | self.json_parser
        
        try:
            result = chain.invoke({
                "topic": topic,
                "count": count,
                "levels": levels,
                "quiz_difficulty": quiz_difficulty
            })
            return result if isinstance(result, list) else []
        except Exception:
            return []
    
    def generate_demo(
        self, 
        concept: str
    ) -> Dict[str, Any]:        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a coding instructor creating clear, practical demonstrations.

Create a demonstration that:
- Shows working, complete code with helpful comments
- Provides a clear step-by-step explanation
- Includes realistic example output
- Uses best practices and clean code
- Is easy to understand and follow

Return JSON format:
{{
    "code": "Complete, working Python code with comments",
    "explanation": "Clear step-by-step explanation of how the code works",
    "output": "Realistic example output when the code runs"
}}

Make the demonstration practical and educational."""),
            ("human", "Concept: {concept}")
        ])
        
        chain = prompt | self.llm | self.json_parser
        
        try:
            result = chain.invoke({"concept": concept})
            return result
        except Exception as e:
            return {
                "code": f"# Demonstration of {concept}\nprint('Example code')",
                "explanation": f"This demonstrates {concept}",
                "output": "Example output"
            }
    
    def generate_example_code(
        self,
        topic: str,
        levels: str = "beginner",
        language: str = "python"
    ) -> Dict[str, Any]:

        levels_instructions = {
            "beginner": """Generate beginner-friendly code:
- Start with simple, clear examples
- Use basic syntax and common patterns
- Include extensive comments explaining each step
- Avoid advanced features or optimization
- Focus on readability and learning
- Include print statements to show what's happening""",
            
            "university": """Generate university-level code:
- Use proper computer science principles and algorithms
- Include theoretical concepts with practical implementation
- Use appropriate data structures and design patterns
- Balance academic rigor with practical application
- Include docstrings and educational comments
- Show correct algorithmic approaches""",
            
            "researcher": """Generate research-grade code:
- Follow cutting-edge techniques and methodologies
- Include performance optimization and scalability considerations
- Use advanced language features and libraries
- Emphasize experimental design and reproducibility
- Include comprehensive documentation for publication
- Show novel approaches and research-oriented solutions"""
        }
        
        instruction = levels_instructions.get(levels, levels_instructions["beginner"])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are an expert software engineer creating {language} code examples.

{instruction}

Return JSON format:
{{{{
    "code": "Complete, working {language} code example",
    "explanation": "Clear explanation of how the code works, tailored to {levels} level",
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
- Adapt complexity and depth to {levels} level"""),
            ("human", "Topic: {topic}\nLanguage: {language}\nContent Level: {levels}")
        ])
        
        chain = prompt | self.llm | self.json_parser
        
        try:
            result = chain.invoke({
                "topic": topic,
                "language": language,
            })
            return result
        except Exception as e:
            fallback_prompt = ChatPromptTemplate.from_messages([
                ("system", f"Generate a {language} code example for the following topic at {levels} level:"),
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


_langchain_handler = None

def get_langchain_handler() -> LangChainHandler:
    global _langchain_handler
    if _langchain_handler is None:
        _langchain_handler = LangChainHandler()
    return _langchain_handler