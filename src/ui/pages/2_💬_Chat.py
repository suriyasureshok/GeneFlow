"""
GeneFlow Chat Interface

Conversational interface with intelligent routing and session memory.

Features:
    - Real-time chat with AI bioinformatics assistant
    - Automatic DNA sequence detection and analysis
    - Session-based conversation history
    - Response streaming
    - Export conversation history

Navigation: Accessible via Dashboard or sidebar
"""

import streamlit as st
import sys
import os
from datetime import datetime
import re

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.agents.unified_coordinator import UnifiedCoordinator
from src.core.session_manager import SessionManager
from src.core.monitoring import PerformanceMonitor

# Page configuration
st.set_page_config(
    page_title="GeneFlow Chat",
    page_icon="💬",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #374151;
        border-left: 3px solid #3b82f6;
    }
    .assistant-message {
        background-color: #064e3b;
        border-left: 3px solid #10b981;
    }
    .sequence-detected {
        background-color: #78350f;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f59e0b;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'performance_monitor' not in st.session_state:
    st.session_state.performance_monitor = PerformanceMonitor(storage_path="metrics")

if 'coordinator' not in st.session_state:
    try:
        session_manager = SessionManager(storage_path="sessions")
        st.session_state.coordinator = UnifiedCoordinator(
            session_manager=session_manager,
            performance_monitor=st.session_state.performance_monitor  # Use shared monitor
        )
    except Exception as e:
        st.error(f"Failed to initialize coordinator: {e}")
        st.stop()

if 'chat_session_id' not in st.session_state:
    st.session_state.chat_session_id = None
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'latest_analysis_id' not in st.session_state:
    st.session_state.latest_analysis_id = None
if 'example_input' not in st.session_state:
    st.session_state.example_input = ""

# Header
st.title("💬 Chat with GeneFlow")
st.markdown("Ask questions, get insights, or analyze DNA sequences")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("💬 Chat Session")
    
    if st.session_state.chat_session_id:
        st.info(f"**Session ID:** `{st.session_state.chat_session_id[:8]}...`")
        
        if st.button("🔄 New Chat Session", width='stretch'):
            st.session_state.chat_session_id = None
            st.session_state.chat_messages = []
            st.session_state.latest_analysis_id = None
            st.rerun()
    
    st.markdown("---")
    st.header("🎯 Quick Actions")
    
    if st.button("🏠 Dashboard", width='stretch'):
        st.switch_page("pages/1_🏠_Dashboard.py")
    
    if st.session_state.latest_analysis_id:
        if st.button("🔬 View Latest Analysis", width='stretch', type="primary"):
            st.switch_page("pages/3_🔬_Analysis_Results.py")
    
    st.markdown("---")
    st.header("📝 Example Queries")
    
    if st.button("Load: Short sequence", use_container_width=True):
        st.session_state.example_input = "Analyze this DNA sequence: ATGAAATATAAAGCGTACGTGCTTGAATGCCTTATAAACGTAGCTAG"
        st.rerun()
    
    if st.button("Load: Ask about GC content", use_container_width=True):
        st.session_state.example_input = "What is GC content and why is it important in genomics?"
        st.rerun()
    
    if st.button("Load: Explain ORFs", use_container_width=True):
        st.session_state.example_input = "Can you explain what Open Reading Frames (ORFs) are?"
        st.rerun()

# Display chat history
chat_container = st.container()
with chat_container:
    for message in st.session_state.chat_messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        
        css_class = "user-message" if role == "user" else "assistant-message"
        icon = "👤" if role == "user" else "🤖"
        
        st.markdown(
            f'<div class="chat-message {css_class}"><strong>{icon} {role.title()}</strong><br>{content}</div>',
            unsafe_allow_html=True
        )

# Chat input
st.markdown("---")

# Pre-filled example
default_input = st.session_state.get("example_input", "")
if default_input:
    st.session_state.example_input = ""

user_input = st.text_area(
    "Your message:",
    value=default_input,
    height=120,
    placeholder="Type your question or paste a DNA sequence (e.g., ATGCGTACG...)"
)

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    send_button = st.button("📤 Send Message", type="primary", width='stretch')

with col2:
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_messages = []
        st.rerun()

with col3:
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("pages/1_🏠_Dashboard.py")

# Process message
if send_button and user_input.strip():
    # Add user message
    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Check if message contains DNA sequence
    def contains_sequence(text):
        pattern = r'[ATCGURYKMSWBDHVN]{20,}'
        return bool(re.search(pattern, text.upper()))
    
    # Check if coordinator is initialized
    if not hasattr(st.session_state, 'coordinator') or st.session_state.coordinator is None:
        st.error("❌ Coordinator not initialized. Please refresh the page.")
        st.stop()
    
    # Process with coordinator
    with st.spinner("🔬 Processing your message..."):
        try:
            # Process message - coordinator will auto-detect sequences and route appropriately
            result = st.session_state.coordinator.process_message(
                message=user_input,
                session_id=st.session_state.chat_session_id
            )
            
            if result.get("success"):
                # Store session ID
                st.session_state.chat_session_id = result.get("session_id")
                response = result.get("response", "")
                
                # Check if sequence was detected
                if contains_sequence(user_input):
                    # Store analysis ID for later viewing
                    st.session_state.latest_analysis_id = st.session_state.chat_session_id
                    
                    # Show sequence detected message
                    st.success("🧬 DNA Sequence Detected!")
                    
                    # Run full pipeline automatically
                    with st.spinner("🧬 Running complete analysis pipeline..."):
                        sequence_match = re.search(r'[ATCGURYKMSWBDHVN]{20,}', user_input.upper())
                        if sequence_match:
                            analysis_result = st.session_state.coordinator.run_pipeline(
                                sequence=sequence_match.group(0),
                                session_id=st.session_state.chat_session_id
                            )
                            
                            if analysis_result.get("success"):
                                # Store results for analysis page
                                st.session_state.latest_analysis_results = analysis_result.get("results")
                                st.session_state.latest_analysis_response = analysis_result.get("response")
                                
                                # Show success message
                                st.success("✅ Analysis complete!")
                                
                                # Add message with button to view results
                                st.session_state.chat_messages.append({
                                    "role": "assistant",
                                    "content": f"I've completed the full analysis of your DNA sequence ({len(sequence_match.group(0))} bp). Click the button in the sidebar to view the comprehensive results including sequence analysis, literature review, hypotheses, visualizations, and PDF report."
                                })
                                
                                # Show button to view results
                                if st.button("🔬 View Complete Analysis Results", type="primary", use_container_width=True):
                                    st.switch_page("pages/3_🔬_Analysis_Results.py")
                            else:
                                st.error(f"❌ Analysis failed: {analysis_result.get('error', 'Unknown error')}")
                                st.session_state.chat_messages.append({
                                    "role": "assistant",
                                    "content": f"I detected a DNA sequence but the analysis failed: {analysis_result.get('error', 'Unknown error')}"
                                })
                else:
                    # Regular conversation response
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": response
                    })
                
                st.rerun()
                
            else:
                st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": f"Sorry, I encountered an error: {result.get('error', 'Unknown error')}"
                })
                st.rerun()
                
        except Exception as e:
            import traceback
            st.error(f"❌ Processing failed: {e}")
            st.code(traceback.format_exc())
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": f"Sorry, I encountered an error: {str(e)}"
            })
            st.rerun()

# Footer
st.markdown("---")
st.caption("💡 Tip: You can ask general questions or paste DNA sequences for analysis. The system will automatically detect sequences and offer comprehensive analysis.")
