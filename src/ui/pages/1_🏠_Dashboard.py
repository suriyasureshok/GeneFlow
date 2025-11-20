"""
GeneFlow Dashboard Page

Comprehensive dashboard showing system status, recent analyses, and quick statistics.

Features:
    - System status and health metrics
    - Recent analysis history
    - Quick statistics overview
    - Session summary

Navigation: Accessible via Home page or sidebar
"""

import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.core.session_manager import SessionManager
from src.core.monitoring import PerformanceMonitor

# Page configuration
st.set_page_config(
    page_title="GeneFlow Dashboard",
    page_icon="🏠",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #60a5fa, #93c5fd);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .dashboard-card {
        background-color: #1f2937;
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        color: white;
        text-align: center;
    }
    .stat-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .stat-label {
        font-size: 0.875rem;
        opacity: 0.9;
    }
    .recent-item {
        background-color: #374151;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 3px solid #10b981;
    }
</style>
""", unsafe_allow_html=True)

# Initialize managers
if 'session_manager' not in st.session_state:
    st.session_state.session_manager = SessionManager(storage_path="sessions")
if 'performance_monitor' not in st.session_state:
    st.session_state.performance_monitor = PerformanceMonitor(storage_path="metrics")

# Header
st.markdown('<p class="main-header">🧬 GeneFlow Dashboard</p>', unsafe_allow_html=True)
st.markdown("### Welcome to your Agentic Bioinformatics Copilot")
st.markdown("---")

# System Status
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("#### 🤖 System Status")
    if os.getenv("GOOGLE_API_KEY"):
        st.success("✅ API Key Configured")
    else:
        st.error("❌ API Key Missing")
    st.markdown("**Model:** Gemini 2.5 Flash")
    st.markdown("**Framework:** Google ADK")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("#### 📊 Session Stats")
    session_stats = st.session_state.session_manager.get_session_stats()
    st.metric("Total Sessions", session_stats.get("total_sessions", 0))
    st.metric("Active Today", session_stats.get("active_today", 0))
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("#### 💰 Usage Stats")
    perf_stats = st.session_state.performance_monitor.get_summary_stats()
    st.metric("Total Executions", perf_stats.get("total_executions", 0))
    st.metric("Est. Cost", f"${perf_stats.get('total_cost_estimate_usd', 0):.4f}")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# Key Metrics
st.subheader("📈 Performance Metrics")
col1, col2, col3, col4 = st.columns(4)

perf_stats = st.session_state.performance_monitor.get_summary_stats()

with col1:
    st.markdown("""
    <div class="stat-card">
        <div class="stat-label">Success Rate</div>
        <div class="stat-value">{:.1f}%</div>
    </div>
    """.format(perf_stats.get('success_rate', 0)), unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="stat-card">
        <div class="stat-label">Avg Duration</div>
        <div class="stat-value">{:.2f}s</div>
    </div>
    """.format(perf_stats.get('avg_duration_seconds', 0)), unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="stat-card">
        <div class="stat-label">Total Tokens</div>
        <div class="stat-value">{:,}</div>
    </div>
    """.format(perf_stats.get('total_tokens', 0)), unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="stat-card">
        <div class="stat-label">Messages</div>
        <div class="stat-value">{}</div>
    </div>
    """.format(session_stats.get('total_messages', 0)), unsafe_allow_html=True)

st.markdown("---")

# Recent Activities
st.subheader("🕒 Recent Sessions")

sessions_path = Path("sessions")
if sessions_path.exists():
    session_files = sorted(sessions_path.glob("*.json"), key=os.path.getmtime, reverse=True)[:5]
    
    if session_files:
        for session_file in session_files:
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    
                st.markdown(f"""
                <div class="recent-item">
                    <strong>Session:</strong> {session_data.get('session_id', 'Unknown')[:16]}...<br>
                    <strong>Created:</strong> {session_data.get('created_at', 'Unknown')}<br>
                    <strong>Messages:</strong> {len(session_data.get('conversation_history', []))}
                </div>
                """, unsafe_allow_html=True)
            except:
                pass
    else:
        st.info("No recent sessions found. Start a chat to create your first session!")
else:
    st.info("No sessions directory found. Start using the system to see recent activities.")

st.markdown("---")

# Quick Actions
st.subheader("🚀 Quick Actions")
col1, col2 = st.columns(2)

with col1:
    if st.button("💬 Start New Chat", use_container_width=True, type="primary"):
        st.switch_page("pages/2_💬_Chat.py")

with col2:
    if st.button("🔬 View Analysis Results", use_container_width=True):
        st.switch_page("pages/3_🔬_Analysis_Results.py")

# Footer
st.markdown("---")
st.caption("GeneFlow v1.0 - Powered by Google ADK & Gemini 2.5 Flash")
