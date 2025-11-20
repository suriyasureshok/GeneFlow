"""
Legacy ADK Agents module - DEPRECATED
Please use geneflow.agents.coordinator.ADKCoordinator instead

This file is kept for backward compatibility only.
"""

import logging
import warnings

logger = logging.getLogger(__name__)

warnings.warn(
    "adk_agents.py is deprecated. Use geneflow.agents.coordinator.ADKCoordinator instead.",
    DeprecationWarning,
    stacklevel=2
)


def create_coordinator_agent():
    """
    Legacy function - creates ADK coordinator agent
    
    DEPRECATED: Use ADKCoordinator class instead
    """
    logger.warning("create_coordinator_agent() is deprecated. Use ADKCoordinator class instead.")
    
    from geneflow.agents.coordinator import ADKCoordinator
    coordinator = ADKCoordinator()
    return coordinator.agent
