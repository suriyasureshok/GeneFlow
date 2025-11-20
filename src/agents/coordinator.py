"""
ADK Coordinator Agent: Legacy Bioinformatics Pipeline Orchestrator

ADK-powered coordinator that orchestrates the bioinformatics analysis pipeline
with full monitoring and session management.

Features:
    - Comprehensive tool integration
    - Session-based conversation tracking
    - Performance monitoring and metrics
    - Context management

Usage:
    from src.agents.coordinator import ADKCoordinator
    coord = ADKCoordinator()
    result = coord.run_pipeline(sequence, session_id)

Note: This is the legacy coordinator. Consider using UnifiedCoordinator instead.
"""

import logging
import time
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime

from src.core.context_manager import ContextManager
from src.core.session_manager import SessionManager, Session
from src.core.monitoring import PerformanceMonitor
from src.core.agent_factory import ADKAgentFactory
from src.core.adk_tools import get_all_tools
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ADKCoordinator:
    """
    ADK-powered coordinator for GeneFlow bioinformatics pipeline.
    Uses Google ADK for 95% of functionality with monitoring and session management.
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
        
        # Initialize ADK agent with all bioinformatics tools
        self.agent = self._create_coordinator_agent()
        
        # Create GenerativeModel for chat interface
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.chat_model = genai.GenerativeModel(
                model_name=self.model,
                tools=get_all_tools()
            )
        else:
            self.chat_model = None
        
        logger.info("ADK Coordinator initialized successfully")
    
    def _create_coordinator_agent(self):
        """Create the main ADK coordinator agent with all tools"""
        
        instruction = """
You are the GeneFlow Coordinator - execute the COMPLETE 5-step analysis pipeline for EVERY sequence.

**YOUR JOB: When user gives you a DNA sequence, call ALL 5 tools below in order. Do NOT stop after tool 1.**

**MANDATORY TOOL SEQUENCE:**
1. analyze_sequence(sequence="<USER_SEQUENCE>")
2. search_literature(keywords=["<motifs_found>", "DNA", "gene"])  
3. generate_hypothesis(analysis_results="<results_from_step_1>", literature_results="<results_from_step_2>")
4. create_visualizations(sequence="<USER_SEQUENCE>", analysis_results="<results_from_step_1>")
5. generate_report(analysis_results="<all_accumulated_results>", plots_directory="<from_step_4>")

**EXAMPLE EXECUTION:**
User: "Analyze this sequence: ATGCGTACG"
You MUST call:
- analyze_sequence(sequence="ATGCGTACG") 
- search_literature(keywords=["start codon", "DNA"])
- generate_hypothesis(analysis_results="{...}", literature_results="{...}")
- create_visualizations(sequence="ATGCGTACG", analysis_results="{...}")
- generate_report(analysis_results="{...}", plots_directory="plots/...")

Then provide summary of findings.

**RULES:**
✓ Call ALL 5 tools for every sequence analysis request
✓ Use results from previous tools as input to next tools  
✗ Do NOT ask "Would you like me to..." - just execute all tools
✗ Do NOT stop after analyze_sequence - continue automatically
✗ Do NOT wait for user permission between tools

Execute the full 5-tool pipeline NOW for any sequence given.
        """
        
        agent = ADKAgentFactory.create_adk_agent(
            name="geneflow_coordinator",
            description="Expert bioinformatics research coordinator with full analysis pipeline",
            instruction=instruction,
            tools=get_all_tools(),
            model=self.model
        )
        
        if not agent:
            logger.error("Failed to create ADK agent - falling back to basic mode")
            raise RuntimeError("ADK agent creation failed")
        
        return agent
    
    def process_message(
        self,
        message: str,
        session_id: str = None,
        user_id: str = None,
        auto_pipeline: bool = True
    ) -> Dict[str, Any]:
        """
        Process a user message through the ADK agent with full session and monitoring support.
        
        Args:
            message: User's input message/query
            session_id: Optional session ID for conversation continuity
            user_id: Optional user identifier
            auto_pipeline: If True, detect sequences and run full pipeline automatically
            
        Returns:
            Response dictionary with agent output, metrics, and session info
        """
        # Check if message contains a DNA/RNA sequence and auto_pipeline is enabled
        if auto_pipeline and self._contains_sequence(message):
            sequence = self._extract_sequence(message)
            if sequence and len(sequence) > 20:  # Only trigger for substantial sequences
                logger.info(f"Detected sequence (length {len(sequence)}), running full pipeline")
                return self.run_pipeline(sequence, session_id)
        
        # Otherwise, process as regular chat message
        start_time = time.time()
        execution_id = self.performance_monitor.start_execution("coordinator")
        
        # Get or create session
        session = self.session_manager.get_or_create_session(session_id, user_id)
        
        # Create context manager for this interaction
        context = ContextManager()
        
        # Load conversation history into context
        for msg in session.conversation_history[-10:]:  # Last 10 messages
            if msg["role"] == "user":
                context.add_user_message(msg["content"])
            elif msg["role"] == "assistant":
                context.add_assistant_message(msg["content"])
        
        # Add current message
        session.add_message("user", message)
        context.add_user_message(message)
        
        try:
            # Check if chat model is available
            if not self.chat_model:
                raise RuntimeError("Chat model not initialized. Please set GOOGLE_API_KEY.")
            
            # Start chat with GenerativeModel
            chat = self.chat_model.start_chat()
            
            # Send message and get response
            logger.info(f"Processing message in session {session.session_id}")
            response = chat.send_message(message)
            
            # Handle function calling loop - model may make multiple tool calls
            max_iterations = 5
            iteration = 0
            response_text = ""
            
            while iteration < max_iterations:
                iteration += 1
                
                # Try to extract text from response
                try:
                    response_text += response.text
                    break  # Got text response, we're done
                except ValueError:
                    # Response contains function calls
                    logger.info(f"Processing function calls (iteration {iteration})")
                    
                    # Execute all function calls in this response
                    function_responses = []
                    for part in response.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
                        elif hasattr(part, 'function_call'):
                            fc = part.function_call
                            logger.info(f"Executing tool: {fc.name}")
                            
                            # Execute the tool
                            tool_result = self._execute_tool(fc.name, dict(fc.args))
                            
                            # Create function response
                            from google.generativeai.protos import FunctionResponse, Content, Part
                            function_responses.append(
                                Part(function_response=FunctionResponse(
                                    name=fc.name,
                                    response={"result": tool_result}
                                ))
                            )
                    
                    # If we have function responses, send them back
                    if function_responses:
                        # Send function results back to model
                        response = chat.send_message(
                            Content(parts=function_responses)
                        )
                    else:
                        # No function calls found, break
                        break
            
            if not response_text:
                response_text = "I processed your request successfully."
            
            # Add to context and session
            context.add_assistant_message(response_text)
            session.add_message("assistant", response_text)
            
            # Estimate tokens (rough approximation)
            tokens_input = len(message) // 4
            tokens_output = len(response_text) // 4
            
            # Record execution metrics
            self.performance_monitor.end_execution(
                agent_name="coordinator",
                execution_id=execution_id,
                start_time=start_time,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                model=self.model,
                success=True
            )
            
            # Build response
            result = {
                "success": True,
                "session_id": session.session_id,
                "response": response_text,
                "timestamp": datetime.now().isoformat(),
                "execution_time_seconds": round(time.time() - start_time, 3),
                "tokens": {
                    "input": tokens_input,
                    "output": tokens_output,
                    "total": tokens_input + tokens_output
                },
                "context_summary": context.get_context_summary()
            }
            
            logger.info(f"Message processed successfully in {result['execution_time_seconds']}s")
            return result
            
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
    
    def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """
        Execute a tool by name with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments to pass to the tool
            
        Returns:
            Tool execution result as string
        """
        try:
            # Get all tools and find the requested one
            tools = get_all_tools()
            tool_func = None
            
            for tool in tools:
                if tool.__name__ == tool_name:
                    tool_func = tool
                    break
            
            if not tool_func:
                return f"Error: Tool '{tool_name}' not found"
            
            # Execute the tool
            logger.info(f"Executing tool {tool_name} with args: {tool_args}")
            result = tool_func(**tool_args)
            
            # Convert result to string if needed
            if isinstance(result, dict):
                import json
                return json.dumps(result, indent=2)
            else:
                return str(result)
                
        except Exception as e:
            logger.error(f"Tool execution failed for {tool_name}: {e}")
            return f"Error executing tool: {str(e)}"
    
    def _contains_sequence(self, message: str) -> bool:
        """Check if message contains a DNA/RNA sequence"""
        import re
        # Look for sequences of ATCG/AUCG letters
        sequence_pattern = r'[ATCGURYKMSWBDHVN]{20,}'
        return bool(re.search(sequence_pattern, message.upper()))
    
    def _extract_sequence(self, message: str) -> str:
        """Extract DNA/RNA sequence from message"""
        import re
        sequence_pattern = r'[ATCGURYKMSWBDHVN]{20,}'
        match = re.search(sequence_pattern, message.upper())
        return match.group(0) if match else None
    
    def run_pipeline(
        self,
        sequence: str,
        session_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a complete bioinformatics analysis pipeline by calling all tools directly.
        
        Args:
            sequence: DNA/RNA sequence to analyze
            session_id: Optional session ID
            metadata: Optional metadata (organism, experiment info, etc.)
            
        Returns:
            Complete analysis results with all findings
        """
        start_time = time.time()
        logger.info(f"🧬 Starting FULL pipeline for sequence (length: {len(sequence)})")
        
        # Get or create session
        session = self.session_manager.get_or_create_session(session_id)
        session.add_message("user", f"Analyze sequence: {sequence[:50]}...")
        
        results = {
            "sequence": sequence[:100] + "..." if len(sequence) > 100 else sequence,
            "sequence_length": len(sequence)
        }
        
        pipeline_steps = []
        
        try:
            # Step 1: Analyze sequence
            logger.info("📊 Step 1/5: Analyzing sequence...")
            pipeline_steps.append("Analyzing sequence structure...")
            analysis_result = self._execute_tool("analyze_sequence", {"sequence": sequence})
            results["analysis"] = json.loads(analysis_result) if isinstance(analysis_result, str) and analysis_result.startswith("{") else analysis_result
            
            # Step 2: Search literature
            logger.info("📚 Step 2/5: Searching literature...")
            pipeline_steps.append("Searching scientific literature...")
            # Extract keywords from analysis - search_literature expects a STRING not list
            keywords_str = "DNA sequence, gene regulation, start codon"
            if isinstance(results["analysis"], dict) and results["analysis"].get("motifs"):
                motifs_found = [m.get("motif", "") for m in results["analysis"]["motifs"]]
                keywords_str = ", ".join(motifs_found[:3]) if motifs_found else keywords_str
            literature_result = self._execute_tool("search_literature", {"keywords": keywords_str})
            results["literature"] = literature_result
            
            # Step 3: Generate hypotheses - expects analysis_summary not analysis_results
            logger.info("💡 Step 3/5: Generating hypotheses...")
            pipeline_steps.append("Generating research hypotheses...")
            analysis_summary = json.dumps(results["analysis"]) if isinstance(results["analysis"], dict) else str(results["analysis"])
            hypothesis_result = self._execute_tool("generate_hypothesis", {
                "analysis_summary": analysis_summary
            })
            results["hypotheses"] = hypothesis_result
            
            # Step 4: Create visualizations - expects sequence and analysis_data
            logger.info("📈 Step 4/5: Creating visualizations...")
            pipeline_steps.append("Creating visualizations...")
            viz_result = self._execute_tool("create_visualizations", {
                "sequence": sequence,
                "analysis_data": analysis_summary
            })
            results["visualizations"] = json.loads(viz_result) if isinstance(viz_result, str) and viz_result.startswith("{") else viz_result
            plots_dir = results["visualizations"].get("output_directory", "geneflow_plots") if isinstance(results["visualizations"], dict) else "geneflow_plots"
            
            # Step 5: Generate report
            logger.info("📄 Step 5/5: Generating PDF report...")
            pipeline_steps.append("Generating comprehensive PDF report...")
            report_result = self._execute_tool("generate_report", {
                "analysis_results": json.dumps(results),
                "plots_directory": plots_dir,
                "output_filename": f"reports/geneflow_report_{session.session_id[:8]}.pdf"
            })
            results["report"] = json.loads(report_result) if isinstance(report_result, str) and report_result.startswith("{") else report_result
            
            # Build comprehensive response
            execution_time = time.time() - start_time
            
            response_text = f"""✅ COMPLETE ANALYSIS FINISHED in {execution_time:.1f}s

📊 **Analysis Summary:**
- Sequence Length: {len(sequence)} bp
- GC Content: {results['analysis'].get('gc_percent', 'N/A')}% (if dict)
- ORFs Found: {len(results['analysis'].get('orfs', [])) if isinstance(results['analysis'], dict) else 'N/A'}
- Motifs Detected: {len(results['analysis'].get('motifs', [])) if isinstance(results['analysis'], dict) else 'N/A'}

📚 **Literature:** {len(results.get('literature', ''))} characters of research context

💡 **Hypotheses:** Generated research hypotheses based on findings

📈 **Visualizations:** Plots saved to {plots_dir}

📄 **Final Report:** {results['report'].get('report_path', 'Generated') if isinstance(results['report'], dict) else 'PDF report generated'}

**Pipeline Steps Completed:**
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(pipeline_steps))}

All analysis complete! Check the report for detailed findings.
"""
            
            # Add to session
            session.add_message("assistant", response_text)
            
            logger.info(f"✅ Full pipeline completed in {execution_time:.1f}s")
            
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
            error_msg = f"Pipeline failed at step {len(pipeline_steps)}: {str(e)}"
            
            return {
                "success": False,
                "session_id": session.session_id,
                "error": error_msg,
                "partial_results": results,
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
