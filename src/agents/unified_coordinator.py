"""
Unified Coordinator: Intelligent Router Between Chat and Analysis Agents

Main coordinator that routes user requests to the appropriate agent based on content.

Routing Logic:
    - DNA sequence (20+ nucleotides) → ADKCoordinator (full analysis)
    - General questions → ChatAgent (fast responses)

Features:
    - Intelligent content-based routing
    - Unified session management across agents
    - Conversation history sharing
    - Performance monitoring

Usage:
    from src.agents.unified_coordinator import UnifiedCoordinator
    coordinator = UnifiedCoordinator()
    
    # General question → Chat Agent (1-3 sec)
    result = coordinator.process_message("What are ORFs?")
    
    # DNA analysis → Analysis Agent (30-60 sec)
    result = coordinator.process_message("ATCGATCGATCG...")

Thread-Safe: Yes
"""

import logging
import re
import time
from typing import Dict, Any, Optional
from datetime import datetime

from src.agents.chat_agent import ChatAgent
from src.agents.adk_coordinator import ADKCoordinator
from src.core.session_manager import SessionManager
from src.core.monitoring import PerformanceMonitor

logger = logging.getLogger(__name__)


class UnifiedCoordinator:
    """
    Intelligent request router between specialized agents with unified session management.
    
    Automatically routes user messages to appropriate agent based on content type:
    - DNA sequences (20+ bp) → ADKCoordinator for full analysis pipeline
    - General questions → ChatAgent for fast conversational responses
    
    Maintains unified session context across both agents ensuring seamless
    conversation continuity and shared analysis state.
    
    Attributes:
        session_manager (SessionManager): Manages conversation sessions
        performance_monitor (PerformanceMonitor): Tracks execution metrics
        chat_agent (ChatAgent): Fast conversational agent (1-3 sec responses)
        analysis_agent (ADKCoordinator): Full analysis agent (30-60 sec)
    
    Methods:
        process_message: Main entry point for message routing
        _contains_dna_sequence: Detects DNA sequence in message
    
    Example:
        >>> coord = UnifiedCoordinator()
        >>> result = coord.process_message(
        ...     "What is GC content?",
        ...     session_id="user_123"
        ... )
        >>> print(result['response'])
    """
    
    def __init__(
        self,
        session_manager: SessionManager = None,
        performance_monitor: PerformanceMonitor = None,
        model: str = "gemini-2.5-flash"
    ):
        self.session_manager = session_manager or SessionManager()
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        
        # Initialize specialized agents
        self.chat_agent = ChatAgent(model="gemini-2.5-flash")
        self.analysis_agent = ADKCoordinator(
            session_manager=self.session_manager,
            performance_monitor=self.performance_monitor,
            model=model
        )
        
        logger.info("UnifiedCoordinator initialized with Chat and Analysis agents")
    
    def _contains_dna_sequence(self, message: str) -> bool:
        """Check if message contains a DNA sequence (20+ nucleotides)"""
        dna_pattern = r'[ATCGURYKMSWBDHVN]{20,}'
        return bool(re.search(dna_pattern, message.upper()))
    
    def process_message(
        self,
        message: str,
        session_id: str = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Process message by routing to appropriate agent.
        
        Args:
            message: User's message
            session_id: Session ID for continuity
            user_id: User ID
            
        Returns:
            Response dictionary
        """
        start_time = time.time()
        execution_id = self.performance_monitor.start_execution("unified_coordinator")
        
        # Get or create session
        session = self.session_manager.get_or_create_session(session_id, user_id)
        session.add_message("user", message)
        
        try:
            # Simple routing: DNA sequence → Analysis Agent, everything else → Chat Agent
            contains_dna = self._contains_dna_sequence(message)
            
            if contains_dna:
                # Route to Analysis Agent (ADK with tools)
                logger.info("Routing to Analysis Agent (DNA sequence detected)")
                
                result = self.analysis_agent.process_message(
                    message=message,
                    session_id=session.session_id,
                    user_id=user_id
                )
                
                agent_used = "analysis"
            else:
                # Route to Chat Agent (lightweight, no tools)
                logger.info("Routing to Chat Agent (general question)")
                
                response_text = self.chat_agent.answer_question(
                    question=message,
                    conversation_history=session.conversation_history[:-1]  # Exclude current message
                )
                
                # Add to session
                session.add_message("assistant", response_text)
                
                result = {
                    "success": True,
                    "session_id": session.session_id,
                    "response": response_text,
                    "timestamp": datetime.now().isoformat()
                }
                
                agent_used = "chat"
            
            # Record metrics
            execution_time = time.time() - start_time
            tokens_input = len(message) // 4
            tokens_output = len(result.get('response', '')) // 4
            
            self.performance_monitor.end_execution(
                agent_name=f"unified_coordinator_{agent_used}",
                execution_id=execution_id,
                start_time=start_time,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                model=self.chat_agent.model if agent_used == "chat" else self.analysis_agent.model,
                success=result.get('success', True)
            )
            
            return result
            
        except Exception as e:
            logger.exception("Unified coordinator failed")
            
            self.performance_monitor.end_execution(
                agent_name="unified_coordinator",
                execution_id=execution_id,
                start_time=start_time,
                tokens_input=0,
                tokens_output=0,
                model="unknown",
                success=False
            )
            
            return {
                "success": False,
                "session_id": session.session_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def run_pipeline(
        self,
        sequence: str,
        session_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Run full analysis pipeline.
        Delegates directly to Analysis Agent.
        """
        logger.info("Running full pipeline via Analysis Agent")
        return self.analysis_agent.run_pipeline(
            sequence=sequence,
            session_id=session_id,
            metadata=metadata
        )
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get session summary"""
        return self.analysis_agent.get_session_summary(session_id)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return self.performance_monitor.get_summary_stats()
