"""
Proper ADK-Based Coordinator using Runner Pattern
Follows Google ADK best practices for agent orchestration
"""

import logging
import time
import os
import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.apps import App
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService
import google.generativeai as genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable

from geneflow.utils.visualizer import VisualizationManager
from geneflow.utils.reporter import create_pdf
from geneflow.utils.structure_generator import StructureGenerator
from geneflow.core.session_manager import SessionManager
from geneflow.core.monitoring import PerformanceMonitor
from geneflow.core.adk_tools import get_all_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ADKCoordinator:
    """
    Proper ADK-powered coordinator using Runner pattern for agent orchestration.
    This follows Google ADK best practices from the documentation.
    """

    def __init__(
        self,
        session_manager: SessionManager = None,
        performance_monitor: PerformanceMonitor = None,
        model: str = "gemini-2.5-flash"
    ):
        self.model = model
        self.session_manager = session_manager or SessionManager()
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        
        # Configure API
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not found in environment")
        
        genai.configure(api_key=api_key)
        
        # Create ADK services
        self.session_service = InMemorySessionService()
        self.memory_service = InMemoryMemoryService()
        self.artifact_service = InMemoryArtifactService()
        
        # Create ADK agent with proper configuration
        self.agent = self._create_agent()
        
        # Create ADK App with name field (required)
        # "agents" matches the package location where ADK loads agents from
        self.app = App(
            name="agents",
            root_agent=self.agent,
            plugins=[]
        )
        
        # Create Runner with services and explicit app_name to avoid mismatch
        self.runner = Runner(
            app=self.app,
            session_service=self.session_service,
            memory_service=self.memory_service,
            artifact_service=self.artifact_service
        )
        
        logger.info("ADK Coordinator initialized with Runner pattern")
    
    def _create_agent(self) -> LlmAgent:
        """Create the main coordinating agent"""
        
        instruction = """You are GeneFlow, an expert bioinformatics research assistant.

**Your capabilities:**
1. **analyze_sequence** - Analyze DNA sequences for GC content, ORFs, and motifs
2. **search_literature** - Search scientific literature for relevant research
3. **generate_hypothesis** - Generate research hypotheses based on findings
4. **create_visualizations** - Create plots and figures
5. **generate_report** - Generate comprehensive PDF reports

**When user provides a DNA sequence:**
- First, use analyze_sequence to examine the sequence
- Then provide insights and offer to run the full pipeline

**When user asks general questions:**
- Answer conversationally using your knowledge
- Suggest relevant tools when appropriate

**For full analysis pipeline:**
User can request comprehensive analysis which includes:
1. Sequence analysis
2. Literature search
3. Hypothesis generation
4. Visualizations
5. PDF report
"""
        
        return LlmAgent(
            name="geneflow_coordinator",
            model=self.model,
            instruction=instruction,
            tools=get_all_tools()
        )

    def process_message(
        self,
        message: str,
        session_id: str = None,
        user_id: str = None,
        auto_pipeline: bool = False
    ) -> Dict[str, Any]:
        """
        Process a message using the ADK Runner pattern.
        
        Args:
            message: User's input message
            session_id: Optional session ID
            user_id: Optional user ID
            auto_pipeline: Whether to auto-detect and run pipeline
            
        Returns:
            Response dictionary with results
        """
        start_time = time.time()
        execution_id = self.performance_monitor.start_execution("coordinator")
        
        # Get or create session for tracking (our own session manager)
        session = self.session_manager.get_or_create_session(session_id, user_id)
        session.add_message("user", message)
        
        # For ADK, use a consistent user_id and let ADK manage its own sessions
        # Don't try to sync session IDs - ADK will create its own
        adk_user_id = user_id or "default_user"
        
        try:
            # Run agent using proper Runner pattern
            # ADK will create and manage its own session internally
            logger.info(f"Processing message with ADK Runner (user: {adk_user_id})")
            
            # Create content for the message
            message_content = types.Content(
                role='user',
                parts=[types.Part.from_text(text=message)]
            )
            
            # Let ADK Runner create its own session by not specifying session_id
            # This avoids the session mismatch issue
            import uuid
            adk_session_id = str(uuid.uuid4())  # Generate new session for each interaction
            
            # Create the session in ADK's service first
            # Create the session in ADK's service first
            # Use "agents" to match the App name and directory structure
            adk_session = self.session_service.create_session_sync(
                app_name="agents",
                user_id=adk_user_id,
                session_id=adk_session_id
            )
            
            # Run using ADK Runner with all required parameters
            response_generator = self.runner.run(
                user_id=adk_user_id,
                session_id=adk_session_id,
                new_message=message_content
            )
            
            # Collect response
            response_text = ""
            for event in response_generator:
                # Extract text from events
                if hasattr(event, 'content') and event.content:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
            
            if not response_text:
                response_text = "I processed your request."
            
            # Add to session
            session.add_message("assistant", response_text)
            
            # Estimate tokens
            tokens_input = len(message) // 4
            tokens_output = len(response_text) // 4
            # Record success
            self.performance_monitor.end_execution(
                agent_name="coordinator",
                execution_id=execution_id,
                start_time=start_time,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                model=self.model,
                success=True
            )
            
            return {
                "success": True,
                "session_id": session.session_id,
                "response": response_text,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.exception("Message processing failed")
            
            # Record failure
            self.performance_monitor.end_execution(
                agent_name="coordinator",
                execution_id=execution_id,
                start_time=start_time,
                tokens_input=len(message) // 4,
                tokens_output=0,
                model=self.model,
                success=False,
                error=str(e)
            )
            
            return {
                "success": False,
                "session_id": session.session_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    @retry(
        retry=retry_if_exception_type((ResourceExhausted, ServiceUnavailable)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=5, min=10, max=120)
    )
    def run_pipeline(
        self,
        sequence: str,
        session_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute complete bioinformatics pipeline using ADK Runner.
        
        Args:
            sequence: DNA/RNA sequence to analyze
            session_id: Optional session ID
            metadata: Optional metadata
            
        Returns:
            Complete analysis results
        """
        start_time = time.time()
        logger.info(f"🧬 Starting pipeline for sequence (length: {len(sequence)})")
        
        # Get or create session
        session = self.session_manager.get_or_create_session(session_id)
        session.add_message("user", f"Run full analysis pipeline for: {sequence[:50]}...")
        
        adk_user_id = "pipeline_user"
        
        try:
            # Create new ADK session for this pipeline run
            import uuid
            adk_session_id = str(uuid.uuid4())
            
            # Create session in ADK's service with detected app name
            # Create session in ADK's service with detected app name
            # Use "agents" to match the App name and directory structure
            adk_session = self.session_service.create_session_sync(
                app_name="agents",
                user_id=adk_user_id,
                session_id=adk_session_id
            )
            
            # Create detailed pipeline request
            pipeline_request = f"""Perform a COMPLETE bioinformatics analysis on this DNA sequence:

{sequence}

Please execute the following steps in order:

1. **Analyze the sequence** using analyze_sequence tool
2. **Search literature** for relevant research on the findings
3. **Generate hypotheses** based on the analysis and literature
4. **Create visualizations** of the sequence characteristics
5. **Generate a PDF report** with all findings

Provide a comprehensive summary of all results."""

            content = types.Content(
                role='user',
                parts=[types.Part.from_text(text=pipeline_request)]
            )
            
            response_generator = self.runner.run(
                user_id=adk_user_id,
                session_id=adk_session_id,
                new_message=content
            )
            
            # Collect all results
            response_text = ""
            for event in response_generator:
                if hasattr(event, 'content') and event.content:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
            
            if not response_text:
                response_text = "I processed your request."

            # Build results structure
            # Parse results from the response text
            parsed_results = self._parse_pipeline_response(response_text, sequence)
            
            # Define output directories
            plots_dir = "geneflow_plots"
            os.makedirs(plots_dir, exist_ok=True)
            structure_dir = "geneflow_structures"
            os.makedirs(structure_dir, exist_ok=True)

            # Generate 3D Structure
            try:
                pdb_path = os.path.join(structure_dir, f"dna_model_{session_id}.pdb")
                struct_img_path = os.path.join(plots_dir, "structure_3d.png")
                
                StructureGenerator.generate_dna_pdb(sequence, pdb_path)
                StructureGenerator.render_dna_image(pdb_path, struct_img_path)
                logger.info(f"Generated 3D structure: {pdb_path}")
            except Exception as e:
                logger.error(f"Structure generation failed: {e}")
                pdb_path = None
                struct_img_path = None

            # Generate Visualizations
            try:
                # GC Plot
                gc_fig = VisualizationManager.plot_gc_content(sequence)
                VisualizationManager.save_plot_image(gc_fig, "gc_plot.png", plots_dir)
                
                # ORF Map
                if parsed_results.get('analysis', {}).get('orfs'):
                    orf_fig = VisualizationManager.plot_orf_map(
                        parsed_results['analysis']['orfs'], 
                        len(sequence)
                    )
                    VisualizationManager.save_plot_image(orf_fig, "orf_map.png", plots_dir)
            except Exception as e:
                logger.error(f"Visualization generation failed: {e}")

            # Generate PDF Report
            try:
                report_data = {
                    "sequence_analysis": parsed_results.get('analysis', {}),
                    "sequence_length": len(sequence),
                    "literature": parsed_results.get('literature', {}),
                    "hypotheses": parsed_results.get('hypotheses', []),
                    "structure_image": struct_img_path
                }
                report_path = create_pdf(report_data, plots_dir, f"reports/report_{session_id}.pdf")
            except Exception as e:
                logger.error(f"Report generation failed: {e}")
                report_path = None
            
            # Merge with base results
            results = {
                "sequence": sequence[:100] + "..." if len(sequence) > 100 else sequence,
                "sequence_length": len(sequence),
                "analysis": parsed_results.get("analysis", "See full response"),
                "literature": parsed_results.get("literature", "See full response"),
                "hypotheses": parsed_results.get("hypotheses", "See full response"),
                "visualizations": {
                    "output_directory": plots_dir,
                    "structure_pdb": pdb_path,
                    "structure_image": struct_img_path
                },
                "report": {"report_path": report_path}
            }
            
            execution_time = time.time() - start_time
            
            # Add to session
            session.add_message("assistant", response_text)
            
            logger.info(f"✅ Pipeline completed in {execution_time:.1f}s")
            
            return {
                "success": True,
                "session_id": session.session_id,
                "response": response_text,
                "results": results,
                "execution_time_seconds": round(execution_time, 3),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.exception("❌ Pipeline execution failed")
            
            return {
                "success": False,
                "session_id": session.session_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of a session"""
        session = self.session_manager.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        return {
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat(),
            "last_accessed": session.last_accessed.isoformat(),
            "message_count": len(session.conversation_history),
            "context_keys": list(session.context_data.keys())
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return self.performance_monitor.get_summary_stats()
    
    def _parse_pipeline_response(self, response_text: str, sequence: str) -> Dict[str, Any]:
        """
        Parse the markdown response from the agent into structured data for the UI.
        This is a heuristic parser based on the expected output format.
        """
        parsed = {}
        
        # 1. Extract Analysis (GC Content, ORFs)
        # Look for sections like "Sequence Analysis", "GC Content", etc.
        analysis_data = {"gc_percent": "N/A", "orfs": [], "motifs": []}
        
        # Simple extraction logic (can be enhanced with regex or structured output from LLM)
        import re
        
        # GC Content
        gc_match = re.search(r"GC [Cc]ontent:?\s*(\d+\.?\d*)%", response_text)
        if gc_match:
            analysis_data["gc_percent"] = gc_match.group(1)
        else:
            # Calculate it manually if not found
            gc_count = sequence.upper().count('G') + sequence.upper().count('C')
            if len(sequence) > 0:
                analysis_data["gc_percent"] = round((gc_count / len(sequence)) * 100, 2)
        
        # ORFs (heuristic count)
        orf_matches = re.findall(r"ORF\s*#?(\d+)", response_text, re.IGNORECASE)
        if orf_matches:
            # Create dummy ORF objects for UI if we found mentions
            for i in range(len(orf_matches)):
                analysis_data["orfs"].append({
                    "start": "N/A", "end": "N/A", "frame": "N/A", "length": "N/A", "strand": "+"
                })
        
        parsed["analysis"] = analysis_data
        
        # 2. Extract Literature
        # Look for "Literature Review" or "Scientific Context" section
        lit_section = re.search(r"(?:##\s+)?(?:Literature Review|Scientific Context)(.*?)(?:##|$)", response_text, re.DOTALL | re.IGNORECASE)
        if lit_section:
            parsed["literature"] = lit_section.group(1).strip()
        else:
            parsed["literature"] = "Literature review details not found in response."
            
        # 3. Extract Hypotheses
        # Look for "Hypotheses" section
        hyp_section = re.search(r"(?:##\s+)?(?:Hypotheses|Research Hypotheses)(.*?)(?:##|$)", response_text, re.DOTALL | re.IGNORECASE)
        if hyp_section:
            parsed["hypotheses"] = hyp_section.group(1).strip()
        else:
            parsed["hypotheses"] = "Hypotheses not found in response."
            
        return parsed

    def cleanup(self):
        """Cleanup old sessions and export metrics"""
        self.session_manager.cleanup_old_sessions()
        self.performance_monitor.export_metrics()


if __name__ == "__main__":
    # Test the coordinator
    coordinator = ADKCoordinator()
    
    # Test sequence
    test_sequence = "ATGAAATATAAAGCGTACGTGCTTGAATGCCTTATAAACGTAGCTAG"
    
    result = coordinator.run_pipeline(test_sequence)
    print(json.dumps(result, indent=2))
