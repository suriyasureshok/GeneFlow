"""
Memory Manager: Shared Context for Agentic Workflow

Manages shared context and history for multi-agent workflows, acting as a
central store for findings from different agents.

Features:
    - Centralized context storage
    - Cross-agent data sharing
    - Context summarization
    - History tracking

Usage:
    from src.core.memory import MemoryManager
    memory = MemoryManager()
    memory.update("sequence_data", analysis_result)
    context = memory.get_context()
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Centralized memory and context storage for multi-agent bioinformatics workflows.
    
    Manages shared state across specialized agents (sequence analyzer, protein predictor,
    literature searcher, etc.), enabling seamless data exchange and result aggregation.
    
    Attributes:
        context (Dict[str, Any]): Central context store with predefined sections:
            - sequence_data (Dict): Sequence analysis results
            - protein_data (List): Protein prediction results  
            - literature_findings (List): Literature search results
            - homology_matches (List): BLAST comparison matches
            - hypotheses (List): Generated research hypotheses
            - chat_history (List): Conversation message history
    
    Methods:
        update: Add or merge data into context
        get_context: Retrieve full or partial context
        get_summary: Generate text summary of current findings
    """

    def __init__(self):
        """
        Initializes memory with predefined context structure for bioinformatics workflow.
        
        Sets up context sections for different analysis stages and data types,
        enabling organized data storage across the pipeline.
        
        Context Sections:
            sequence_data (Dict): Sequence analysis results (GC%, motifs, ORFs)
            protein_data (List): Protein properties and predictions
            literature_findings (List): Research papers and citations
            homology_matches (List): BLAST/database search results
            hypotheses (List): Generated research hypotheses with evidence
            chat_history (List): Conversation messages for context retention
        """
        self.context: Dict[str, Any] = {
            "sequence_data": {},
            "protein_data": [],
            "literature_findings": [],
            "homology_matches": [],
            "hypotheses": [],
            "chat_history": []
        }

    def update(self, key: str, value: Any):
        """
        Updates or merges data into context with type-aware logic.
        
        Intelligently handles different data types:
            - Lists: Appends new items or extends with list values
            - Dicts: Merges/updates values
            - Other types: Replaces value
        
        Args:
            key (str): Context section key (e.g., "sequence_data", "protein_data")
            value (Any): New value or data to merge. Type determines merge strategy.
        
        Returns:
            None
        
        Raises:
            None - Silently creates new key if not in predefined context
        
        Example:
            >>> memory = MemoryManager()
            >>> memory.update("sequence_data", {"gc_percent": 45.5})
            >>> memory.update("protein_data", [{"length": 150}])
        """
        if key in self.context:
            if isinstance(self.context[key], list) and isinstance(value, list):
                self.context[key].extend(value)
            elif isinstance(self.context[key], list):
                self.context[key].append(value)
            elif isinstance(self.context[key], dict) and isinstance(value, dict):
                self.context[key].update(value)
            else:
                self.context[key] = value
        else:
            self.context[key] = value
        
        logger.info(f"Memory updated: {key}")

    def get_context(self) -> Dict[str, Any]:
        """
        Retrieves the complete context dictionary.
        
        Returns full context state including all analysis results, findings,
        and chat history accumulated during the workflow.
        
        Returns:
            Dict[str, Any]: Full context with all stored sections and data
        
        Example:
            >>> context = memory.get_context()
            >>> gc_percent = context["sequence_data"].get("gc_percent")
        """
        return self.context

    def get_summary(self) -> str:
        """
        Generates human-readable summary of current context state.
        
        Useful for injecting context into LLM prompts or displaying
        workflow progress to users.
        
        Returns:
            str: Newline-separated summary of context sections with item counts.
                 Includes: sequence analysis, protein data, literature, homology,
                 and hypothesis counts.
        
        Example:
            >>> summary = memory.get_summary()
            >>> print(summary)
            Sequence Analysis: {...}
            Protein Predictions: 2 ORFs analyzed.
            Literature: 5 papers found.
        """
        summary = []
        if self.context["sequence_data"]:
            summary.append(f"Sequence Analysis: {self.context['sequence_data']}")
        if self.context["protein_data"]:
            summary.append(f"Protein Predictions: {len(self.context['protein_data'])} ORFs analyzed.")
        if self.context["literature_findings"]:
            summary.append(f"Literature: {len(self.context['literature_findings'])} papers found.")
        if self.context["homology_matches"]:
            summary.append(f"Homology: {len(self.context['homology_matches'])} matches found.")
        
        return "\n".join(summary)
