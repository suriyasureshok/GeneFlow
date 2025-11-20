import logging
import os
from typing import List, Dict, Any
from geneflow.core.agent_factory import ADKAgentFactory
import google.generativeai as genai

logger = logging.getLogger(__name__)

class LiteratureAgent:
    """
    Searches for literature using ADK Agent with Tools (Function Calling).
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
        Uses ADK agent to search and summarize.
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
        Tool exposed to Gemini to search PubMed.
        (Stub for actual API call to keep it simple for now, but structure is there)
        """
        # In a real app, this would call Entrez API
        return {
            "results": [
                {"title": f"Paper about {query}", "abstract": "This is a relevant paper found via tool."}
            ]
        }

    def _mock_search(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Mock data for offline mode.
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
