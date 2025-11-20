import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Manages the shared context and history for the agentic workflow.
    Acts as a central store for findings from different agents.
    """

    def __init__(self):
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
        Updates a specific section of the memory.
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
        Returns the full context.
        """
        return self.context

    def get_summary(self) -> str:
        """
        Returns a string summary of the current state for prompt injection.
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
