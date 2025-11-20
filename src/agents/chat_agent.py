"""
Chat Agent: Lightweight Conversational AI for Bioinformatics

Fast, educational responses for general bioinformatics questions without
tool overhead.

Features:
    - Fast response times (1-3 seconds)
    - Context-aware conversation history
    - Scientifically accurate explanations
    - No external tool integration

Topics Covered:
    DNA/RNA sequences, genetics concepts, ORFs, motifs, GC content,
    bioinformatics techniques, and research methodologies

Usage:
    from src.agents.chat_agent import ChatAgent
    chat = ChatAgent()
    response = chat.answer_question("What is GC content?", conversation_history=[])

Model: gemini-2.0-flash-exp
"""

import logging
import os
from typing import Dict, Any, Optional, List

from google.adk.agents import LlmAgent
import google.generativeai as genai
from google.genai import types

logger = logging.getLogger(__name__)


class ChatAgent:
    """
    Lightweight chat agent for answering general bioinformatics questions.
    
    Provides fast, educational responses to bioinformatics queries without
    the overhead of tool integration. Maintains conversation context through
    recent message history.
    
    Attributes:
        model (str): LLM model name (gemini-2.0-flash-exp)
        client (genai.GenerativeModel): Configured Generative AI model
        system_instruction (str): System prompt for the agent
    
    Args:
        model (str, optional): Model to use. Defaults to "gemini-2.0-flash-exp"
    
    Raises:
        RuntimeError: If GOOGLE_API_KEY environment variable is not set
    
    Example:
        >>> agent = ChatAgent()
        >>> answer = agent.answer_question(
        ...     "Explain ORFs in DNA sequences",
        ...     conversation_history=[]
        ... )
    """
    
    def __init__(self, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize the ChatAgent with system instructions.
        
        Sets up the generative AI model with specific instructions for
        bioinformatics expertise and conversation style.
        
        Args:
            model (str, optional): Model identifier. Defaults to "gemini-2.0-flash-exp"
        
        Raises:
            RuntimeError: If GOOGLE_API_KEY environment variable is not set
        
        Attributes Set:
            self.model: Store the model name
            self.system_instruction: Initialize system prompt
            self.client: Create GenerativeModel with system instruction
        """
        self.model = model
        self.system_instruction = """You are GeneFlow, an expert bioinformatics assistant.

You answer questions about:
- DNA/RNA sequences and their properties
- Genetics, genomics, and molecular biology concepts
- Bioinformatics tools and techniques
- ORFs, motifs, GC content, and sequence analysis
- Species identification from genetic sequences
- Research methodologies in genomics

Provide clear, accurate, educational responses. Use examples when helpful.
Be conversational and friendly while maintaining scientific accuracy."""
        
        # Configure API
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not found in environment")
        
        genai.configure(api_key=api_key)
        
        # Create model with system instruction
        self.client = genai.GenerativeModel(
            model_name=self.model,
            system_instruction=self.system_instruction
        )
        
        logger.info(f"ChatAgent initialized with model: {self.model}")
    
    def answer_question(
        self, 
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Answer a bioinformatics question with conversational context.
        
        Generates a response to a question about bioinformatics, using recent
        conversation history to maintain context and coherence.
        
        Args:
            question (str): The user's question to answer
            conversation_history (list, optional): List of recent messages with
                structure [{'role': 'user'|'model', 'content': str}, ...].
                Only the last 6 messages are retained for context.
                Defaults to None (no history).
        
        Returns:
            str: The generated answer or error message. Returns a user-friendly
                error message if generation fails.
        
        Raises:
            Exception: Caught internally and returned as user-friendly message
        
        Example:
            >>> history = [
            ...     {'role': 'user', 'content': 'What are ORFs?'},
            ...     {'role': 'model', 'content': 'ORFs are open reading frames...'}
            ... ]
            >>> answer = agent.answer_question(
            ...     "How do we find them?",
            ...     conversation_history=history
            ... )
        
        Note:
            - Response times: 1-3 seconds typically
            - Uses temperature 0.7 for balanced creativity and accuracy
            - Max output tokens: 2048 per response
        """
        
        # Build conversation context
        messages = []
        
        if conversation_history:
            for msg in conversation_history[-6:]:  # Last 6 messages for context
                role = "user" if msg.get('role') == 'user' else "model"
                messages.append({"role": role, "parts": [msg.get('content', '')]})
        
        # Add current question
        messages.append({"role": "user", "parts": [question]})
        
        try:
            # Generate response
            response = self.client.generate_content(
                messages,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    top_p=0.95,
                    max_output_tokens=2048,
                )
            )
            
            return response.text if response.text else "I understand your question, but couldn't generate a response. Please try again."
            
        except Exception as e:
            logger.error(f"Chat generation failed: {e}")
            return f"I encountered an error: {str(e)}. Please try rephrasing your question."
