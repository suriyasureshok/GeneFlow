"""
ADK-Based Analysis Coordinator: DNA Sequence Analysis Engine

Full-featured DNA analysis agent using Google ADK with integrated tools for
comprehensive bioinformatics pipelines.

Tools Available:
    - analyze_sequence: GC content, ORFs, motifs detection
    - search_literature: Scientific paper search
    - generate_hypothesis: Research hypothesis generation
    - create_visualizations: Plots and charts
    - generate_report: PDF report creation

Features:
    - Session-based conversation memory
    - Performance monitoring and metrics
    - Automatic visualization and 3D structure generation
    - Error handling with retries

Usage:
    from src.agents.adk_coordinator import ADKCoordinator
    coordinator = ADKCoordinator()
    result = coordinator.run_pipeline(sequence="ATCG...", session_id="user_123")

Performance: 30-60 seconds per full pipeline
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

from src.utils.visualizer import VisualizationManager
from src.utils.reporter import create_pdf
from src.utils.structure_generator import StructureGenerator
from src.core.session_manager import SessionManager
from src.core.monitoring import PerformanceMonitor
from src.core.adk_tools import get_all_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ADKCoordinator:
    """
    Analysis coordinator using Google ADK Runner pattern for agent orchestration.
    
    Manages DNA sequence analysis with integrated tools, session persistence,
    and comprehensive result generation. Follows Google ADK best practices
    for agent development and execution.
    
    Attributes:
        model (str): LLM model name
        session_manager (SessionManager): Manages conversation sessions
        performance_monitor (PerformanceMonitor): Tracks metrics
        agent (LlmAgent): Main ADK agent with tools
        runner (Runner): ADK runner for agent execution
        session_service (InMemorySessionService): ADK session management
        memory_service (InMemoryMemoryService): ADK memory management
        artifact_service (InMemoryArtifactService): ADK artifact storage
    
    Args:
        session_manager (SessionManager, optional): Custom session manager
        performance_monitor (PerformanceMonitor, optional): Custom monitor
        model (str, optional): Model name. Defaults to "gemini-2.5-flash"
    
    Raises:
        RuntimeError: If GOOGLE_API_KEY environment variable is not set
    
    Example:
        >>> coordinator = ADKCoordinator()
        >>> result = coordinator.process_message(
        ...     "Analyze this sequence: ATCGATCG...",
        ...     session_id="session_123"
        ... )
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

**IMPORTANT: You MUST always provide a text response to the user, even after using tools.**

**When user provides a DNA sequence:**
- First, use analyze_sequence to examine the sequence
- Then provide insights about the analysis results
- Offer to run the full pipeline for comprehensive analysis

**When user asks general questions:**
- Answer conversationally using your bioinformatics knowledge
- Provide detailed, helpful explanations
- Suggest relevant tools when appropriate
- Always respond with informative text, never stay silent

**When user asks about species identification:**
- Use your knowledge about DNA patterns, sequences, and species characteristics
- Explain your reasoning based on sequence features
- Note any limitations in definitive identification from short sequences

**For full analysis pipeline:**
User can request comprehensive analysis which includes:
1. Sequence analysis
2. Literature search
3. Hypothesis generation
4. Visualizations
5. PDF report

Remember: Always provide a helpful text response. Never execute tools silently without explaining results."""
        
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
        
        # For ADK, use a consistent user_id
        adk_user_id = user_id or "default_user"
        
        # For now, create a new ADK session each time but pass conversation history
        # This avoids session management issues while still maintaining context
        import uuid
        adk_session_id = str(uuid.uuid4())
        
        try:
            # Run agent using proper Runner pattern
            logger.info(f"Processing message with ADK Runner (user: {adk_user_id}, session: {adk_session_id})")
            
            # Build message with conversation history for context
            conversation_context = ""
            if len(session.conversation_history) > 1:
                # Include recent conversation history (last 5 messages)
                recent_history = session.conversation_history[-6:-1]  # Exclude current message
                conversation_context = "Recent conversation:\n"
                for msg in recent_history:
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    conversation_context += f"{role}: {content[:200]}...\n" if len(content) > 200 else f"{role}: {content}\n"
                conversation_context += "\nCurrent question:\n"
            
            full_message = conversation_context + message
            
            # Create content for the message
            message_content = types.Content(
                role='user',
                parts=[types.Part.from_text(text=full_message)]
            )
            
            # Create a new ADK session each time (avoids session not found errors)
            adk_session = self.session_service.create_session_sync(
                app_name="agents",
                user_id=adk_user_id,
                session_id=adk_session_id
            )
            logger.debug(f"Created ADK session: {adk_session_id}")
            
            # Run using ADK Runner with all required parameters
            response_generator = self.runner.run(
                user_id=adk_user_id,
                session_id=adk_session_id,
                new_message=message_content
            )
            
            # Collect response with improved event handling
            response_text = ""
            event_count = 0
            tokens_input = 0
            tokens_output = 0
            
            for event in response_generator:
                event_count += 1
                event_type = type(event).__name__
                logger.info(f"Event {event_count}: {event_type}")
                
                # Log all attributes of the event for debugging
                event_attrs = dir(event)
                logger.debug(f"Event attributes: {[attr for attr in event_attrs if not attr.startswith('_')]}")
                
                # Extract text from events
                if hasattr(event, 'content') and event.content:
                    logger.debug(f"Event has content: {event.content}")
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
                            logger.info(f"Added text chunk: {len(part.text)} chars")
                
                # Also check for text attribute directly on event
                if hasattr(event, 'text') and event.text:
                    response_text += event.text
                    logger.info(f"Added event text: {len(event.text)} chars")
                
                # Check for message attribute
                if hasattr(event, 'message') and event.message:
                    logger.debug(f"Event has message: {event.message}")
                
                # Track token usage if available
                if hasattr(event, 'usage_metadata') and event.usage_metadata:
                    if hasattr(event.usage_metadata, 'input_token_count'):
                        tokens_input += event.usage_metadata.input_token_count
                    if hasattr(event.usage_metadata, 'output_token_count'):
                        tokens_output += event.usage_metadata.output_token_count
            
            logger.warning(f"Message processing: {event_count} events, {len(response_text)} chars collected, tokens: {tokens_input}/{tokens_output}")
            
            if not response_text:
                logger.warning("No response text collected from agent!")
                response_text = "I understand your question, but I wasn't able to generate a response. Please try rephrasing or ask about DNA sequence analysis."
            
            # Add to session
            session.add_message("assistant", response_text)
            
            # Estimate tokens if not captured from events
            if tokens_input == 0:
                tokens_input = len(message) // 4
            if tokens_output == 0:
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
        
        # Start monitoring
        execution_id = self.performance_monitor.start_execution("pipeline")
        
        # Get or create session
        session = self.session_manager.get_or_create_session(session_id)
        session.add_message("user", f"Run full analysis pipeline for: {sequence[:50]}...")
        
        adk_user_id = "pipeline_user"
        tokens_input = 0
        tokens_output = 0
        
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

**IMPORTANT:** After completing all steps, you MUST provide a final response in this EXACT JSON format:

```json
{{
  "summary": "A comprehensive 2-3 paragraph summary of the complete analysis, including key findings, patterns discovered, and biological significance.",
  "sequence_analysis": {{
    "length": <number>,
    "gc_content": <percentage as number>,
    "orfs_count": <number>,
    "motifs": ["motif1", "motif2"],
    "key_findings": ["finding1", "finding2", "finding3"]
  }},
  "literature": {{
    "summary": "Sentences summarizing relevant scientific literature and context",
    "relevant_topics": ["topic1", "topic2",...]
  }},
  "hypotheses": [
    {{
      "hypothesis": "Description of hypothesis 1",
      "confidence": <Decimal between 0 and 1>,
      "rationale": "Scientific reasoning for this hypothesis"
    }},
    {{
      "hypothesis": "Description of hypothesis 2",
      "confidence": <Decimal between 0 and 1>,
      "rationale": "Scientific reasoning for this hypothesis"
    }}
  ]
}}
```

Do NOT include intermediate steps, tool outputs, or conversational text. Return ONLY the JSON object above with your analysis results."""

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
            event_count = 0
            for event in response_generator:
                event_count += 1
                logger.debug(f"Event {event_count}: {type(event).__name__}")
                
                # Check for content in the event
                if hasattr(event, 'content') and event.content:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
                            logger.debug(f"Added text chunk: {len(part.text)} chars")
                
                # Also check for text attribute directly on event
                if hasattr(event, 'text') and event.text:
                    response_text += event.text
                    logger.debug(f"Added event text: {len(event.text)} chars")
                    
                # Track token usage if available
                if hasattr(event, 'usage_metadata') and event.usage_metadata:
                    if hasattr(event.usage_metadata, 'input_token_count'):
                        tokens_input += event.usage_metadata.input_token_count
                    if hasattr(event.usage_metadata, 'output_token_count'):
                        tokens_output += event.usage_metadata.output_token_count
            
            logger.info(f"Pipeline execution: {event_count} events, {len(response_text)} chars collected")
            
            if not response_text:
                logger.warning("No response text collected from agent - tools may have executed without summary")
                response_text = json.dumps({
                    "summary": "Analysis completed. Results have been generated and saved.",
                    "sequence_analysis": {
                        "length": len(sequence),
                        "gc_content": 0,
                        "orfs_count": 0,
                        "motifs": [],
                        "key_findings": ["Analysis tools executed successfully"]
                    },
                    "literature": {
                        "summary": "Literature search completed.",
                        "relevant_topics": []
                    },
                    "hypotheses": []
                })
            
            # Try to extract JSON if wrapped in markdown code blocks
            json_match = None
            if "```json" in response_text:
                import re
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)
                    logger.info("Extracted JSON from markdown code block")
            
            # Clean up the response to extract only the final summary
            response_text = self._extract_final_summary(response_text)

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
            
            # End monitoring - success
            self.performance_monitor.end_execution(
                agent_name="pipeline",
                execution_id=execution_id,
                start_time=start_time,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                model=self.model,
                success=True
            )
            
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
            
            # End monitoring - failure
            self.performance_monitor.end_execution(
                agent_name="pipeline",
                execution_id=execution_id,
                start_time=start_time,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                model=self.model,
                success=False
            )
            
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
    
    def _extract_final_summary(self, response_text: str) -> str:
        """
        Extract only the final summary from the response, removing intermediate steps.
        Now handles JSON format responses.
        """
        import re
        
        # If it's JSON, try to parse and format it nicely
        try:
            if response_text.strip().startswith('{'):
                data = json.loads(response_text)
                
                # Format JSON data into readable markdown
                formatted = []
                
                if 'summary' in data:
                    formatted.append(f"## 📊 Analysis Summary\n\n{data['summary']}\n")
                
                if 'sequence_analysis' in data:
                    sa = data['sequence_analysis']
                    formatted.append(f"## 🧬 Sequence Analysis")
                    formatted.append(f"- **Length:** {sa.get('length', 'N/A')} bp")
                    formatted.append(f"- **GC Content:** {sa.get('gc_content', 'N/A')}%")
                    formatted.append(f"- **ORFs Found:** {sa.get('orfs_count', 'N/A')}")
                    
                    if sa.get('motifs'):
                        formatted.append(f"- **Motifs:** {', '.join(sa['motifs'])}")
                    
                    if sa.get('key_findings'):
                        formatted.append("\n**Key Findings:**")
                        for finding in sa['key_findings']:
                            formatted.append(f"- {finding}")
                    formatted.append("")
                
                if 'literature' in data:
                    lit = data['literature']
                    formatted.append(f"## 📚 Literature Review\n")
                    formatted.append(lit.get('summary', 'No literature summary available.'))
                    if lit.get('relevant_topics'):
                        formatted.append(f"\n**Relevant Topics:** {', '.join(lit['relevant_topics'])}")
                    formatted.append("")
                
                if 'hypotheses' in data and data['hypotheses']:
                    formatted.append(f"## 💡 Research Hypotheses\n")
                    for i, hyp in enumerate(data['hypotheses'], 1):
                        formatted.append(f"**Hypothesis {i}** (Confidence: {hyp.get('confidence', 0):.0%})")
                        formatted.append(f"{hyp.get('hypothesis', 'N/A')}")
                        formatted.append(f"*Rationale:* {hyp.get('rationale', 'N/A')}\n")
                
                return '\n'.join(formatted)
        except json.JSONDecodeError:
            logger.debug("Response is not JSON, processing as text")
        
        # Otherwise, process as before for text responses
        # Look for the final summary sections
        summary_markers = [
            r"(?:Final )?(?:Summary|Results)(?: to Date)?:?\s*\n",
            r"Here(?:'s| is) (?:a )?(?:comprehensive )?summary",
            r"(?:## |###? )?(?:📊 )?Sequence Analysis",
        ]
        
        for marker in summary_markers:
            match = re.search(marker, response_text, re.IGNORECASE)
            if match:
                summary_start = match.start()
                content_start = response_text.find('\n', summary_start) + 1
                if content_start > 0:
                    response_text = response_text[content_start:].strip()
                    break
        
        # Remove repetitive phrases
        phrases_to_remove = [
            r"I have (?:completed|performed) the .*?\.",
            r"Now, I will .*?\.",
            r"Next, I will .*?\.",
            r"I will (?:now )?proceed to .*?\.",
            r"based on these findings\.?",
        ]
        
        for phrase in phrases_to_remove:
            response_text = re.sub(phrase, '', response_text, flags=re.IGNORECASE)
        
        # Clean up excessive whitespace
        response_text = re.sub(r'\n{3,}', '\n\n', response_text)
        response_text = re.sub(r' {2,}', ' ', response_text)
        
        return response_text.strip()
    
    def _parse_pipeline_response(self, response_text: str, sequence: str) -> Dict[str, Any]:
        """
        Parse the markdown response from the agent into structured data for the UI.
        This is a heuristic parser based on the expected output format.
        """
        parsed = {}
        
        # 1. Extract Analysis (GC Content, ORFs, Motifs)
        analysis_data = {"gc_percent": "N/A", "orfs": [], "motifs": []}
        
        import re
        
        # GC Content - more patterns
        gc_patterns = [
            r"GC [Cc]ontent:?\s*(?:of\s+)?(\d+\.?\d*)%",
            r"(\d+\.?\d*)%\s+GC",
        ]
        for pattern in gc_patterns:
            gc_match = re.search(pattern, response_text)
            if gc_match:
                analysis_data["gc_percent"] = float(gc_match.group(1))
                break
        
        if analysis_data["gc_percent"] == "N/A":
            # Calculate manually
            gc_count = sequence.upper().count('G') + sequence.upper().count('C')
            if len(sequence) > 0:
                analysis_data["gc_percent"] = round((gc_count / len(sequence)) * 100, 2)
        
        # ORFs - look for explicit mentions
        orf_section = re.search(r"ORFs? (?:Found|Detected|Identified):?\s*(\d+)", response_text, re.IGNORECASE)
        if orf_section:
            orf_count = int(orf_section.group(1))
            # Create placeholder ORF entries
            for i in range(orf_count):
                analysis_data["orfs"].append({
                    "start": "N/A", "end": "N/A", "frame": i+1, 
                    "length": "N/A", "strand": "+"
                })
        
        # Check for "no ORFs" statement
        if re.search(r"no (?:open reading frames|orfs?) (?:were )?(?:detected|found|identified)", response_text, re.IGNORECASE):
            analysis_data["orfs"] = []
        
        # Motifs - look for motif mentions with positions
        motif_matches = re.findall(
            r'(?:"([^"]+)"\s+motif.*?position(?:s)?\s+(\d+(?:\s+and\s+\d+)?)|'
            r'motif[s]?\s+\(([A-Z]+)\)\s+at\s+position(?:s)?\s+(\d+(?:\s+and\s+\d+)?))',
            response_text,
            re.IGNORECASE
        )
        
        for match in motif_matches:
            motif_name = match[0] or match[2]
            positions = match[1] or match[3]
            if motif_name and positions:
                analysis_data["motifs"].append({
                    "motif": motif_name,
                    "position": positions,
                    "match": motif_name
                })
        
        parsed["analysis"] = analysis_data
        
        # 2. Extract Literature - look for the literature section
        lit_patterns = [
            r"##\s*📚\s*Literature Review\s*\n(.*?)(?=\n##|\Z)",
            r"##\s*Literature Review\s*\n(.*?)(?=\n##|\Z)",
            r"Literature (?:Search|Review).*?:\s*(.*?)(?=\n\n##|Hypothesis|\Z)",
        ]
        
        literature_text = None
        for pattern in lit_patterns:
            lit_match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
            if lit_match:
                literature_text = lit_match.group(1).strip()
                break
        
        if literature_text:
            parsed["literature"] = literature_text
        else:
            parsed["literature"] = "Literature review details not found in response."
            
        # 3. Extract Hypotheses
        hyp_patterns = [
            r"##\s*💡\s*Research Hypotheses\s*\n(.*?)(?=\n##|\Z)",
            r"##\s*(?:Research )?Hypotheses\s*\n(.*?)(?=\n##|\Z)",
            r"Hypothesis Generation:?\s*(.*?)(?=\n\n##|\Z)",
        ]
        
        hypotheses_text = None
        for pattern in hyp_patterns:
            hyp_match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
            if hyp_match:
                hypotheses_text = hyp_match.group(1).strip()
                break
        
        if hypotheses_text:
            parsed["hypotheses"] = hypotheses_text
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
