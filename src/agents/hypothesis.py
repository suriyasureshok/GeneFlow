"""
Hypothesis Agent: Research Hypothesis Generation

Synthesizes experimental findings into testable research hypotheses using
ADK-powered AI analysis.

Features:
    - AI-powered hypothesis formulation
    - Confidence level assessment
    - Evidence-based reasoning
    - Multiple hypothesis generation

Usage:
    from src.agents.hypothesis import HypothesisAgent
    agent = HypothesisAgent()
    hypotheses = agent.generate(analysis_context)
"""

import logging
import os
from typing import Dict, Any, List
from src.core.agent_factory import ADKAgentFactory
import google.generativeai as genai

logger = logging.getLogger(__name__)

class HypothesisAgent:
    """
    Research hypothesis generation from experimental data using AI synthesis.
    
    Analyzes integrated bioinformatics findings (sequences, proteins, literature,
    homology) to formulate testable research hypotheses with supporting evidence
    and confidence scoring.
    
    Attributes:
        agent: ADK agent for hypothesis coordination
        chat_model: GenerativeModel for natural language synthesis
    
    Methods:
        generate: Main hypothesis generation entry point
    
    Example:
        >>> agent = HypothesisAgent()
        >>> context = {"sequence_analysis": {...}, "literature": [...]}
        >>> hypotheses = agent.generate(context)
    """

    def __init__(self):
        instruction = """
        You are a Senior Principal Investigator.
        Your goal is to formulate scientific hypotheses based on experimental data.
        
        Input:
        - Sequence properties (GC%, Motifs)
        - Protein predictions (MW, Hydrophobicity, Signal Peptides)
        - Literature summaries
        - Homology matches
        
        Output:
        - A list of 3 distinct hypotheses.
        - For each, provide a confidence level (Low/Medium/High) and cite specific evidence from the input.
        
        Format: JSON list of objects: [{"hypothesis": "...", "confidence": "...", "evidence": "..."}]
        """
        self.agent = ADKAgentFactory.create_adk_agent(
            name="hypothesis_generator",
            description="Generates research hypotheses from experimental data",
            instruction=instruction,
            model="gemini-2.5-flash"
        )
        
        # Create GenerativeModel for chat
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.chat_model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=instruction
            )
        else:
            self.chat_model = None

    def generate(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generates research hypotheses from aggregated analysis results.
        
        Args:
            context: Dictionary containing:
                - sequence_analysis (Dict): GC%, motifs, ORFs
                - protein_predictions (List): Protein properties
                - literature (List): Relevant papers
                - comparison (List): Homology matches
        
        Returns:
            List of hypothesis dictionaries containing:
                - hypothesis (str): Hypothesis statement
                - confidence (str): "Low", "Medium", or "High"
                - evidence (str): Supporting evidence from data
        
        Note:
            Returns fallback hypothesis on API errors or missing key
        """
        logger.info("Generating hypotheses with ADK agent...")
        
        if not self.chat_model:
            logger.error("Chat model not initialized")
            return [{
                "hypothesis": "Unable to generate hypothesis (Model not initialized).",
                "confidence": "Low",
                "evidence": "Please set GOOGLE_API_KEY"
            }]
        
        try:
            # Construct a detailed prompt from the context
            prompt = f"""
            Analyze the following data:
            
            Sequence: {context.get('sequence_analysis')}
            Proteins: {context.get('protein_predictions')}
            Literature: {context.get('literature')}
            Homology: {context.get('comparison')}
            
            Generate 3 hypotheses.
            """
            
            # Use GenerativeModel chat
            chat = self.chat_model.start_chat()
            response = chat.send_message(prompt)
            
            # Parse JSON output
            import json
            import re
            text = response.text if hasattr(response, 'text') else str(response)
            json_match = re.search(r"```json\n(.*)\n```", text, re.DOTALL)
            
            if json_match:
                return json.loads(json_match.group(1))
            else:
                # Try to parse raw text or return a text-based hypothesis wrapped in structure
                try:
                    return json.loads(text)
                except:
                    return [{
                        "hypothesis": "Gemini generated a text response.",
                        "confidence": "Medium",
                        "evidence": text[:200] + "..."
                    }]

        except Exception as e:
            logger.error(f"Hypothesis generation failed: {e}")
            # Fallback stub
            return [{
                "hypothesis": "Unable to generate hypothesis (LLM Error).",
                "confidence": "Low",
                "evidence": str(e)
            }]

if __name__ == "__main__":
    agent = HypothesisAgent()
    # Mock context
    ctx = {"sequence_analysis": {"gc_percent": 50}}
    # print(agent.generate(ctx)) # Requires API key
