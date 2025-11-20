"""
Advanced Context Management for GeneFlow

Manages conversation context, token limits, and context window optimization.

Features:
    - Sliding context window with token limits
    - Automatic message trimming
    - Token counting and estimation
    - Context compression and summarization

Usage:
    from src.core.context_manager import ContextWindow
    window = ContextWindow(max_tokens=32000)
    window.add_message("user", "Hello")
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from collections import deque
import tiktoken
import json

logger = logging.getLogger(__name__)


class ContextWindow:
    """Manages a sliding context window with token limits for LLM interactions.
    
    Maintains conversation history with automatic trimming when token limits
    are exceeded. Tracks token usage and supports serialization for context export.
    
    Attributes:
        max_tokens (int): Maximum token budget for context window
        messages (deque): Circular buffer of conversation messages
        tokenizer: tiktoken encoder for accurate token counting
        total_tokens (int): Current token usage
    
    Methods:
        add_message: Append message to context
        count_tokens: Estimate token usage
        get_messages: Retrieve formatted messages
        _trim_to_limit: Remove old messages if over limit
    """
    
    def __init__(self, max_tokens: int = 32000, model: str = "gpt-4"):
        self.max_tokens = max_tokens
        self.model = model
        self.messages: deque = deque()
        self.system_message: Optional[Dict[str, str]] = None
        self.total_tokens = 0
        
        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base for unknown models
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed: {e}, using char estimate")
            return len(text) // 4  # Rough estimate
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add a message to the context window"""
        message = {
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "tokens": self.count_tokens(content)
        }
        
        self.messages.append(message)
        self.total_tokens += message["tokens"]
        
        # Trim if over limit
        self._trim_to_limit()
    
    def set_system_message(self, content: str):
        """Set the system message"""
        self.system_message = {
            "role": "system",
            "content": content,
            "tokens": self.count_tokens(content)
        }
    
    def _trim_to_limit(self):
        """Remove oldest messages to stay under token limit"""
        # Reserve space for system message
        system_tokens = self.system_message["tokens"] if self.system_message else 0
        available_tokens = self.max_tokens - system_tokens
        
        while self.total_tokens > available_tokens and len(self.messages) > 1:
            removed = self.messages.popleft()
            self.total_tokens -= removed["tokens"]
            logger.debug(f"Trimmed message with {removed['tokens']} tokens")
    
    def get_messages(self, include_system: bool = True) -> List[Dict[str, str]]:
        """Get all messages formatted for API"""
        messages = []
        
        if include_system and self.system_message:
            messages.append({
                "role": self.system_message["role"],
                "content": self.system_message["content"]
            })
        
        for msg in self.messages:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return messages
    
    def get_stats(self) -> Dict[str, Any]:
        """Get context window statistics"""
        return {
            "total_messages": len(self.messages),
            "total_tokens": self.total_tokens,
            "max_tokens": self.max_tokens,
            "utilization": (self.total_tokens / self.max_tokens) * 100,
            "has_system_message": self.system_message is not None
        }
    
    def clear(self):
        """Clear all messages"""
        self.messages.clear()
        self.total_tokens = 0


class ContextManager:
    """
    Advanced context management for multi-agent analysis workflows.
    
    Maintains comprehensive execution state including conversation history,
    analysis results, tool execution logs, and performance metrics.
    Central hub for data flow across specialized analysis agents.
    
    Attributes:
        context_window (ContextWindow): Manages message context with token limits
        analysis_context (Dict): Aggregated analysis results from all stages
        tool_results (List): Tool execution history and outputs
        execution_log (List): Event log of all operations
    
    Methods:
        add_user_message: Record user input
        add_assistant_message: Record assistant response
        add_tool_result: Record tool execution
        update_analysis_context: Update analysis findings
        get_context_summary: Generate text summary for prompts
    """
    
    def __init__(self, max_tokens: int = 32000):
        self.context_window = ContextWindow(max_tokens=max_tokens)
        self.analysis_context: Dict[str, Any] = {
            "sequence_data": {},
            "protein_data": [],
            "literature_findings": [],
            "homology_matches": [],
            "hypotheses": [],
            "metadata": {}
        }
        self.tool_results: List[Dict[str, Any]] = []
        self.execution_log: List[Dict[str, Any]] = []
        
    def add_user_message(self, content: str, metadata: Dict[str, Any] = None):
        """Add user message to context"""
        self.context_window.add_message("user", content, metadata)
        self.log_event("user_message", {"content_length": len(content)})
    
    def add_assistant_message(self, content: str, metadata: Dict[str, Any] = None):
        """Add assistant message to context"""
        self.context_window.add_message("assistant", content, metadata)
        self.log_event("assistant_message", {"content_length": len(content)})
    
    def add_tool_result(self, tool_name: str, result: Any, metadata: Dict[str, Any] = None):
        """Record tool execution result"""
        tool_record = {
            "tool_name": tool_name,
            "result": result,
            "metadata": metadata or {},
            "timestamp": self._get_timestamp()
        }
        self.tool_results.append(tool_record)
        self.log_event("tool_execution", {"tool_name": tool_name})
    
    def update_analysis_context(self, key: str, value: Any):
        """Update analysis context"""
        if key in self.analysis_context:
            if isinstance(self.analysis_context[key], list) and isinstance(value, list):
                self.analysis_context[key].extend(value)
            elif isinstance(self.analysis_context[key], list):
                self.analysis_context[key].append(value)
            elif isinstance(self.analysis_context[key], dict) and isinstance(value, dict):
                self.analysis_context[key].update(value)
            else:
                self.analysis_context[key] = value
        else:
            self.analysis_context[key] = value
        
        self.log_event("context_update", {"key": key})
    
    def get_analysis_context(self, key: str = None) -> Any:
        """Get analysis context"""
        if key:
            return self.analysis_context.get(key)
        return self.analysis_context
    
    def get_context_summary(self) -> str:
        """Generate a text summary of current context for prompts"""
        summary_parts = []
        
        # Sequence analysis
        if self.analysis_context["sequence_data"]:
            seq_data = self.analysis_context["sequence_data"]
            summary_parts.append(
                f"Sequence Analysis: Length={seq_data.get('length', 'N/A')}, "
                f"GC%={seq_data.get('gc_percent', 'N/A')}, "
                f"ORFs={len(seq_data.get('orfs', []))}, "
                f"Motifs={len(seq_data.get('motifs', []))}"
            )
        
        # Protein predictions
        if self.analysis_context["protein_data"]:
            summary_parts.append(
                f"Protein Predictions: {len(self.analysis_context['protein_data'])} proteins analyzed"
            )
        
        # Literature
        if self.analysis_context["literature_findings"]:
            summary_parts.append(
                f"Literature: {len(self.analysis_context['literature_findings'])} papers found"
            )
        
        # Homology
        if self.analysis_context["homology_matches"]:
            summary_parts.append(
                f"Homology: {len(self.analysis_context['homology_matches'])} matches found"
            )
        
        # Hypotheses
        if self.analysis_context["hypotheses"]:
            summary_parts.append(
                f"Hypotheses: {len(self.analysis_context['hypotheses'])} generated"
            )
        
        return "\n".join(summary_parts) if summary_parts else "No analysis data available"
    
    def get_tool_history(self, tool_name: str = None) -> List[Dict[str, Any]]:
        """Get tool execution history"""
        if tool_name:
            return [t for t in self.tool_results if t["tool_name"] == tool_name]
        return self.tool_results
    
    def log_event(self, event_type: str, data: Dict[str, Any] = None):
        """Log an execution event"""
        self.execution_log.append({
            "event_type": event_type,
            "data": data or {},
            "timestamp": self._get_timestamp()
        })
    
    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get full execution log"""
        return self.execution_log
    
    def export_context(self) -> Dict[str, Any]:
        """Export full context for serialization"""
        return {
            "messages": self.context_window.get_messages(),
            "analysis_context": self.analysis_context,
            "tool_results": self.tool_results,
            "execution_log": self.execution_log,
            "stats": self.get_stats()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get context statistics"""
        return {
            "context_window": self.context_window.get_stats(),
            "total_tool_calls": len(self.tool_results),
            "total_events": len(self.execution_log),
            "analysis_keys": list(self.analysis_context.keys())
        }
    
    def clear(self):
        """Clear all context"""
        self.context_window.clear()
        self.analysis_context = {
            "sequence_data": {},
            "protein_data": [],
            "literature_findings": [],
            "homology_matches": [],
            "hypotheses": [],
            "metadata": {}
        }
        self.tool_results.clear()
        self.execution_log.clear()
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
