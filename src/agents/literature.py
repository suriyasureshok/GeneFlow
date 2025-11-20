"""
Literature Agent: Scientific Literature Search

Searches scientific literature using ADK agent with function calling to find
relevant papers based on keywords.

Features:
    - PubMed search integration
    - Keyword-based literature discovery
    - AI-powered paper summarization
    - Offline mode support

Usage:
    from src.agents.literature import LiteratureAgent
    agent = LiteratureAgent()
    papers = agent.search(["DNA methylation", "epigenetics"])
"""

import logging
import os
from typing import List, Dict, Any
from src.core.agent_factory import ADKAgentFactory
import google.generativeai as genai

logger = logging.getLogger(__name__)

class LiteratureAgent:
    """
    Scientific literature search using AI-powered agent interface.
    
    Searches PubMed and scientific literature databases using natural language
    queries through Google's Generative AI. Provides paper discovery and
    summarization for research context.
    
    Attributes:
        offline_mode (bool): Use mock data instead of live API calls
        agent: ADK agent for search coordination
        chat_model: GenerativeModel for natural language interaction
    
    Methods:
        search: Main search entry point
        _search_pubmed_tool: Tool function for PubMed API
        _mock_search: Returns demonstration data for offline mode
    
    Example:
        >>> agent = LiteratureAgent(offline_mode=True)
        >>> papers = agent.search(["TATA box", "transcription"])
    """

    def __init__(self, offline_mode: bool = False):
        self.offline_mode = offline_mode
        
        # Define tools for the agent
        tools = [self._search_pubmed_tool]
        
        instruction = """
        You are a Literature Research Assistant.
        Your goal is to find relevant scientific papers based on keywords.
        Use the `search_pubmed` tool to find papers.
        Summarize the findings concisely.
        """
        
        self.agent = ADKAgentFactory.create_adk_agent(
            name="literature_searcher",
            description="Searches scientific literature for relevant papers",
            instruction=instruction,
            tools=tools,
            model="gemini-2.5-flash"
        )
        
        # Create GenerativeModel for chat
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.chat_model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=instruction,
                tools=tools
            )
        else:
            self.chat_model = None

    def search(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Searches scientific literature for papers matching keywords.
        
        Uses AI-powered search with tool calling to query literature databases.
        Falls back to mock data if offline_mode=True or on API errors.
        
        Args:
            keywords: List of search keywords/terms
        
        Returns:
            List of paper dictionaries containing:
                - title (str): Paper title
                - authors (str): Author list
                - year (int/str): Publication year
                - summary (str): Abstract or summary
                - doi (str): DOI identifier
        """
        logger.info(f"Searching literature for: {keywords}")
        
        if self.offline_mode:
            # Fallback to mock for demo speed/reliability if requested
            return self._mock_search(keywords)

        if not self.chat_model:
            logger.warning("Chat model not initialized, using mock search")
            return self._mock_search(keywords)

        try:
            # Ask GenerativeModel to perform the search
            prompt = f"Find 3 key papers related to: {', '.join(keywords)}"
            
            # Use GenerativeModel chat
            chat = self.chat_model.start_chat()
            response = chat.send_message(prompt)
            
            # In a real full implementation, we would parse the tool output or the natural language summary.
            # For this V1, we'll return a structured representation of what Gemini found
            # or just the raw text if it didn't call the tool properly.
            
            # Since we can't easily return the tool output directly in this simple interface without more parsing logic,
            # we will return a simplified structure based on the response text.
            text = response.text if hasattr(response, 'text') else str(response)
            
            return [{
                "title": "Gemini Search Result",
                "year": "2024",
                "authors": "AI Assistant",
                "summary": text,
                "doi": "N/A"
            }]

        except Exception as e:
            logger.error(f"Literature search failed: {e}")
            return self._mock_search(keywords)

    def _search_pubmed_tool(self, query: str):
        """
        Tool function exposed to Gemini for PubMed searches.
        
        In production, this would call NCBI Entrez E-utilities API.
        Currently returns mock data structure for demonstration.
        
        Args:
            query: Search query string
        
        Returns:
            Dictionary with search results
        """
        # In a real app, this would call Entrez API
        return {
            "results": [
                {"title": f"Paper about {query}", "abstract": "This is a relevant paper found via tool."}
            ]
        }

    def _mock_search(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Returns mock literature data for offline/demo mode.
        
        Provides sample papers related to common bioinformatics topics.
        
        Args:
            keywords: Search keywords (unused in mock mode)
        
        Returns:
            List of mock paper dictionaries
        """
        return [
            {
                "title": "Structure and function of the TATA-box binding protein",
                "authors": "Kim Y, et al.",
                "year": 1993,
                "summary": "The TATA-box binding protein (TBP) is required for transcription of all three classes of nuclear genes...",
                "doi": "10.1038/365520a0"
            },
            {
                "title": "Signal peptides: exquisitely designed sequences for secretion",
                "authors": "Von Heijne G.",
                "year": 1985,
                "summary": "Signal peptides have a common structure: a positively charged n-region, a hydrophobic h-region, and a polar c-region...",
                "doi": "10.1016/0022-2836(85)90267-X"
            }
        ]

if __name__ == "__main__":
    # Test
    agent = LiteratureAgent(offline_mode=True)
    print(agent.search(["TATA"]))
