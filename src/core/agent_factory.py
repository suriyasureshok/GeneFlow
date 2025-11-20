"""
Agent Factory for GeneFlow

Creates and configures Google ADK agents with proper tool integration.

Features:
    - ADK agent creation with tools
    - Legacy agent support (fallback to google-generativeai)
    - Automatic API key configuration

Usage:
    from src.core.agent_factory import ADKAgentFactory
    agent = ADKAgentFactory.create_adk_agent(
        name="analyzer",
        description="DNA analysis",
        instruction="Analyze sequences...",
        tools=[tool1, tool2]
    )
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
    Factory for creating and configuring Google ADK Agents with integrated tools.
    
    Provides static methods for instantiating ADK agents with proper tool integration,
    API key configuration, and multi-agent system orchestration.
    Uses ADK as the primary interface for 95% of functionality.
    
    Methods:
        create_adk_agent: Creates a single ADK agent with tools
        create_tool_from_function: Wraps Python functions as ADK tools
        create_multi_agent_system: Creates coordinated multi-agent systems
    
    Example:
        >>> agent = ADKAgentFactory.create_adk_agent(
        ...     name="analyzer",
        ...     description="DNA analysis",
        ...     instruction="Analyze sequences...",
        ...     tools=[analyze_sequence, predict_protein]
        ... )
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
        Creates a Google ADK Agent with integrated tools and system instructions.
        
        Initializes an ADK agent with API key configuration, tool integration,
        and custom system instructions for specialized bioinformatics tasks.
        
        Args:
            name (str): Unique agent identifier
            description (str): Human-readable agent purpose description
            instruction (str): System instruction prompt defining agent behavior
            tools (List[Callable], optional): Python functions exposed as tools. Default: None
            model (str, optional): LLM model identifier. Default: "gemini-2.5-flash"
                                 Options: "gemini-2.5-flash", "gemini-1.5-pro", etc.
            **kwargs: Additional ADK agent configuration parameters
        
        Returns:
            Agent: Configured ADK Agent instance, or None if creation fails
        
        Raises:
            None - Returns None if GOOGLE_API_KEY not set or ADK unavailable
        
        Requires:
            GOOGLE_API_KEY: Google API key in environment variables
            google-adk package: Must be installed and available
        
        Example:
            >>> agent = ADKAgentFactory.create_adk_agent(
            ...     name="dna_analyzer",
            ...     description="DNA sequence analysis",
            ...     instruction="You analyze DNA sequences...",
            ...     tools=[analyze_sequence, predict_protein],
            ...     model="gemini-2.5-flash"
            ... )
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
        Wraps Python functions as ADK-compatible tool functions.
        
        Automatically handles function introspection for tool registration.
        ADK handles conversion without explicit wrapper code.
        
        Args:
            func (Callable): The function to wrap as a tool
            name (str, optional): Custom tool name (default: function name)
            description (str, optional): Custom tool description
        
        Returns:
            Callable: The function (optionally with updated docstring)
        
        Note:
            ADK automatically converts Python functions to tools.
            Docstring update aids discovery and documentation.
        
        Example:
            >>> def my_analysis(sequence):
            ...     '''Analyze DNA sequence'''
            ...     return process(sequence)
            >>> tool = ADKAgentFactory.create_tool_from_function(my_analysis)
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
        Creates a coordinated multi-agent system for complex workflows.
        
        Instantiates a coordinator agent with specialized subordinate agents
        for distributed analysis tasks and result aggregation.
        
        Args:
            coordinator_config (Dict[str, Any]): Configuration dict for coordinator agent.
                                               Must include: name, description, instruction
            agent_configs (List[Dict[str, Any]]): List of configs for specialized agents.
                                                Each must include: name, description, instruction
        
        Returns:
            Dict[str, Agent]: Mapping of agent names to Agent instances.
                             Keys: "coordinator" + agent names from configs
                             Values: Configured ADK Agent instances
        
        Raises:
            None - Returns partial system if some agents fail to create
        
        Example:
            >>> coordinator_cfg = {
            ...     "name": "master",
            ...     "description": "Master coordinator",
            ...     "instruction": "Coordinate analysis..."
            ... }
            >>> agent_cfgs = [
            ...     {"name": "analyzer", "description": "Sequence analysis", ...},
            ...     {"name": "predictor", "description": "Protein prediction", ...}
            ... ]
            >>> system = ADKAgentFactory.create_multi_agent_system(coordinator_cfg, agent_cfgs)
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
    Fallback factory for creating agents using google-generativeai directly.
    
    Used only when ADK is unavailable or for specific edge cases requiring
    direct Gemini API access without ADK Runner overhead.
    
    Methods:
        create_agent: Creates a Gemini model with configuration
        create_chat: Starts a chat session with automatic function calling
    """
    
    @staticmethod
    def create_agent(
        model_name: str = "gemini-2.5-flash",
        system_instruction: str = None,
        tools: List[Any] = None
    ) -> genai.GenerativeModel:
        """
        Creates a Gemini GenerativeModel with system instructions and tools.
        
        This is the fallback implementation when ADK is not available.
        Provides direct access to Gemini API with function calling.
        
        Args:
            model_name (str, optional): LLM model identifier. Default: "gemini-2.5-flash"
            system_instruction (str, optional): System prompt for model behavior
            tools (List[Any], optional): List of tools to expose to the model
        
        Returns:
            genai.GenerativeModel: Configured Gemini model instance
        
        Requires:
            GOOGLE_API_KEY: Google API key in environment variables (warning if missing)
        
        Example:
            >>> model = LegacyAgentFactory.create_agent(
            ...     model_name="gemini-2.5-flash",
            ...     system_instruction="You are a DNA analyzer",
            ...     tools=[analyze_sequence]
            ... )
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
        Starts a chat session with automatic function calling enabled.
        
        Args:
            model (genai.GenerativeModel): The Gemini model instance
            history (List[Any], optional): Conversation history for context
        
        Returns:
            ChatSession: Active chat session with function calling enabled
        
        Example:
            >>> model = LegacyAgentFactory.create_agent()
            >>> chat = LegacyAgentFactory.create_chat(model)
            >>> response = chat.send_message("Analyze this DNA sequence...")
        """
        return model.start_chat(history=history or [], enable_automatic_function_calling=True)
