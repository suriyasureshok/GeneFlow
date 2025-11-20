"""
Simplified Coordinator using Direct Gemini API with Function Calling
This bypasses ADK Runner complexity and directly uses Gemini's function calling
"""

import logging
import time
import os
from typing import Dict, Any, Optional
from datetime import datetime
import google.generativeai as genai

from geneflow.core.session_manager import SessionManager
from geneflow.core.monitoring import PerformanceMonitor
from geneflow.core.adk_tools import get_all_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleCoordinator:
    """
    Simplified coordinator using direct Gemini API with function calling.
    This approach avoids ADK Runner session management complexity.
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
        
        # Get tools - they're just Python functions
        tool_functions = get_all_tools()
        self.tool_map = {func.__name__: func for func in tool_functions}
        
        # Create model with tools (Gemini will auto-convert from Python functions)
        self.genai_model = genai.GenerativeModel(
            model_name=self.model,
            tools=tool_functions,
            system_instruction="""You are GeneFlow, an expert bioinformatics research assistant.

**Your capabilities:**
1. **analyze_sequence** - Analyze DNA sequences for GC content, ORFs, and motifs
2. **search_literature** - Search scientific literature for relevant research
3. **generate_hypothesis** - Generate research hypotheses based on findings
4. **create_visualizations** - Create plots and figures
5. **generate_report** - Generate comprehensive PDF reports

**When user provides a DNA sequence:**
- Use analyze_sequence to examine the sequence
- Provide insights based on the analysis
- Offer to run the full pipeline if requested

**When user asks general questions:**
- Answer conversationally using your knowledge
- Suggest relevant tools when appropriate

Always be helpful, clear, and scientific in your responses."""
        )
        
        logger.info("Simple Coordinator initialized with Gemini function calling")
    
    def process_message(
        self,
        message: str,
        session_id: str = None,
        user_id: str = None,
        auto_pipeline: bool = False
    ) -> Dict[str, Any]:
        """Process a single user message using Gemini function calling"""
        start_time = time.time()
        execution_id = self.performance_monitor.start_execution("coordinator")
        
        # Get or create session
        session = self.session_manager.get_or_create_session(session_id, user_id)
        session.add_message("user", message)
        
        try:
            logger.info(f"Processing message for session {session.session_id}")
            
            # Start chat with history
            chat = self.genai_model.start_chat(history=[
                {"role": msg["role"], "parts": [msg["content"]]}
                for msg in session.messages[:-1]  # Exclude the latest user message
            ])
            
            # Send message and handle function calls
            response = chat.send_message(message)
            
            # Handle function calls iteratively
            max_iterations = 10
            iteration = 0
            
            while response.candidates[0].content.parts[0].function_call and iteration < max_iterations:
                iteration += 1
                function_call = response.candidates[0].content.parts[0].function_call
                
                logger.info(f"Function call: {function_call.name}")
                
                # Execute the function
                tool = self.tool_map.get(function_call.name)
                if tool:
                    try:
                        # Convert function call args to dict
                        func_args = dict(function_call.args)
                        # tool is the function itself, call it directly
                        result = tool(**func_args)
                        
                        # Send result back to model
                        response = chat.send_message(
                            genai.protos.Content(
                                parts=[genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(
                                        name=function_call.name,
                                        response={"result": result}
                                    )
                                )]
                            )
                        )
                    except Exception as e:
                        logger.error(f"Function execution error: {e}")
                        error_response = f"Error executing {function_call.name}: {str(e)}"
                        response = chat.send_message(
                            genai.protos.Content(
                                parts=[genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(
                                        name=function_call.name,
                                        response={"error": error_response}
                                    )
                                )]
                            )
                        )
                else:
                    logger.warning(f"Unknown function: {function_call.name}")
                    break
            
            # Extract final text response
            response_text = response.text if hasattr(response, 'text') else "I processed your request."
            
            # Add to session
            session.add_message("assistant", response_text)
            
            # Estimate tokens
            tokens_input = len(message) // 4
            tokens_output = len(response_text) // 4
            
            # Record metrics
            self.performance_monitor.end_execution(
                agent_name="coordinator",
                execution_id=execution_id,
                start_time=start_time,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                model=self.model,
                success=True
            )
            
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
                }
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
    
    def run_pipeline(
        self,
        sequence: str,
        session_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute complete bioinformatics pipeline.
        Returns structured data for display.
        """
        start_time = time.time()
        logger.info(f"🧬 Starting pipeline for sequence (length: {len(sequence)})")
        
        results = {
            "sequence": sequence,
            "sequence_length": len(sequence),
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        try:
            # Step 1: Sequence Analysis
            logger.info("📊 Step 1/5: Analyzing sequence...")
            from geneflow.agents.sequence_analyzer import SequenceAnalyzer
            analyzer = SequenceAnalyzer()
            analysis_result = analyzer.analyze(sequence)
            results['analysis'] = analysis_result
            
            # Step 2: Literature Search
            logger.info("📚 Step 2/5: Searching literature...")
            from geneflow.agents.literature import LiteratureAgent
            lit_agent = LiteratureAgent()
            lit_result = lit_agent.search(f"DNA sequence analysis GC content {analysis_result.get('gc_percent', '')}%")
            results['literature'] = lit_result
            
            # Step 3: Hypothesis Generation
            logger.info("💡 Step 3/5: Generating hypotheses...")
            from geneflow.agents.hypothesis import HypothesisAgent
            hyp_agent = HypothesisAgent()
            hyp_result = hyp_agent.generate(sequence, analysis_result, lit_result)
            results['hypotheses'] = hyp_result
            
            # Step 4: Create Visualizations
            logger.info("📊 Step 4/5: Creating visualizations...")
            from geneflow.utils.visualizer import Visualizer
            viz = Visualizer()
            viz_result = viz.create_sequence_plots(sequence, analysis_result)
            results['visualizations'] = viz_result
            
            # Step 5: Generate Report
            logger.info("📄 Step 5/5: Generating PDF report...")
            from geneflow.utils.reporter import Reporter
            reporter = Reporter()
            report_path = reporter.generate(results)
            results['report_path'] = report_path
            
            results['success'] = True
            results['execution_time'] = round(time.time() - start_time, 2)
            
            logger.info(f"✅ Pipeline completed in {results['execution_time']}s")
            return results
            
        except Exception as e:
            logger.exception("Pipeline execution failed")
            results['success'] = False
            results['error'] = str(e)
            return results
