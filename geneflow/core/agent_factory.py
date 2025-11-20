"""
ADK-based Agent Factory for GeneFlow
Creates and configures Google ADK agents with proper tool integration
"""

import os
import logging
from typing import List, Any, Optional, Callable, Dict
from dotenv import load_dotenv

try:
    from google.adk.agents.llm_agent import Agent
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    # Use the module-level logging without relying on a logger variable defined later
    logging.getLogger(__name__).warning("Google ADK not available, falling back to google-generativeai")

import google.generativeai as genai

load_dotenv()

logger = logging.getLogger(__name__)


class ADKAgentFactory:
    """
    Factory for creating Google ADK Agents with bioinformatics tools.
    Uses ADK as primary interface (95% of functionality).
    """
    
    @staticmethod
    def create_adk_agent(
        name: str,
        description: str,
        instruction: str,
        tools: List[Callable] = None,
        model: str = "gemini-2.5-flash",
        **kwargs
    ) -> Optional["Agent"]:
        """
        Creates a Google ADK Agent.
        
        Args:
            name: Agent name
            description: Agent description
            instruction: System instruction for the agent
            tools: List of Python functions to use as tools
            model: Model to use (default: gemini-2.5-flash)
            **kwargs: Additional agent configuration
            
        Returns:
            ADK Agent instance or None if ADK not available
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("GOOGLE_API_KEY not found in environment variables.")
            return None
        
        if not ADK_AVAILABLE:
            logger.error("Google ADK not available. Please install: pip install google-adk")
            return None
        
        try:
            # Configure API key
            genai.configure(api_key=api_key)
            
            # Create ADK agent
            agent = Agent(
                model=model,
                name=name,
                description=description,
                instruction=instruction,
                tools=tools or [],
                **kwargs
            )
            
            logger.info(f"Created ADK agent: {name} with model {model}")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create ADK agent: {e}")
            return None
    
    @staticmethod
    def create_tool_from_function(
        func: Callable,
        name: str = None,
        description: str = None
    ) -> Callable:
        """
        Wraps a Python function as an ADK-compatible tool.
        ADK automatically handles function introspection.
        
        Args:
            func: The function to wrap
            name: Optional custom name
            description: Optional custom description
            
        Returns:
            The function (ADK handles the rest automatically)
        """
        # ADK automatically converts Python functions to tools
        # We can optionally modify the docstring for better descriptions
        if description and func.__doc__ is None:
            func.__doc__ = description
        
        return func
    
    @staticmethod
    def create_multi_agent_system(
        coordinator_config: Dict[str, Any],
        agent_configs: List[Dict[str, Any]]
    ) -> Dict[str, "Agent"]:
        """
        Creates a multi-agent system with a coordinator and specialized agents.
        
        Args:
            coordinator_config: Configuration for coordinator agent
            agent_configs: List of configurations for specialized agents
            
        Returns:
            Dictionary mapping agent names to Agent instances
        """
        agents = {}
        
        # Create coordinator
        coordinator = ADKAgentFactory.create_adk_agent(**coordinator_config)
        if coordinator:
            agents["coordinator"] = coordinator
        
        # Create specialized agents
        for config in agent_configs:
            agent = ADKAgentFactory.create_adk_agent(**config)
            if agent:
                agents[config["name"]] = agent
        
        logger.info(f"Created multi-agent system with {len(agents)} agents")
        return agents


# Fallback factory for non-ADK usage (the 5% edge cases)
class LegacyAgentFactory:
    """
    Fallback factory using google-generativeai directly.
    Only used when ADK is not available or for specific edge cases.
    """
    
    @staticmethod
    def create_agent(
        model_name: str = "gemini-2.5-flash",
        system_instruction: str = None,
        tools: List[Any] = None
    ) -> genai.GenerativeModel:
        """
        Creates a Gemini model with instructions and tools.
        This is the fallback when ADK is not available.
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY not found in environment variables.")
        
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction,
            tools=tools
        )
        
        logger.info(f"Created legacy Gemini model: {model_name}")
        return model
    
    @staticmethod
    def create_chat(model: genai.GenerativeModel, history: List[Any] = None):
        """
        Starts a chat session with the model.
        """
        return model.start_chat(history=history or [], enable_automatic_function_calling=True)
