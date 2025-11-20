"""
GeneFlow Statistics Page
Detailed performance metrics and usage analytics
"""

import streamlit as st
import sys
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from geneflow.core.monitoring import PerformanceMonitor

# Page configuration
st.set_page_config(
    page_title="Statistics",
    page_icon="📊",
    layout="wide"
)

# Initialize monitor
if 'performance_monitor' not in st.session_state:
    st.session_state.performance_monitor = PerformanceMonitor(storage_path="metrics")

# Header
st.title("📊 Performance Statistics")
st.markdown("### Detailed metrics and analytics")
st.markdown("---")

# Get stats
stats = st.session_state.performance_monitor.get_summary_stats()

# Overview metrics
st.subheader("📈 Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Executions", stats.get("total_executions", 0))
with col2:
    st.metric("Success Rate", f"{stats.get('success_rate', 0):.1f}%")
with col3:
    st.metric("Total Tokens", f"{stats.get('total_tokens', 0):,}")
with col4:
    st.metric("Est. Cost", f"${stats.get('total_cost_estimate_usd', 0):.4f}")

st.markdown("---")

# Performance metrics
st.subheader("⚡ Performance Metrics")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Avg Duration", f"{stats.get('avg_duration_seconds', 0):.3f}s")
with col2:
    st.metric("Min Duration", f"{stats.get('min_duration_seconds', 0):.3f}s")
with col3:
    st.metric("Max Duration", f"{stats.get('max_duration_seconds', 0):.3f}s")

st.markdown("---")

# Agent breakdown
st.subheader("🤖 Agent Breakdown")
agent_stats = stats.get("agent_breakdown", {})

if agent_stats:
    df = pd.DataFrame([
        {
            "Agent": agent,
            "Count": data.get("count", 0),
            "Tokens": data.get("tokens", 0),
            "Cost ($)": data.get("cost", 0)
        }
        for agent, data in agent_stats.items()
    ])
    
    st.dataframe(df, width="stretch", hide_index=True)
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        if not df.empty:
            fig = px.pie(df, values='Count', names='Agent', title='Execution Distribution')
            st.plotly_chart(fig, width="stretch")
    
    with col2:
        if not df.empty:
            fig = px.bar(df, x='Agent', y='Tokens', title='Token Usage by Agent')
            st.plotly_chart(fig, width="stretch")
else:
    st.info("No agent statistics available yet.")

st.markdown("---")

# System metrics
st.subheader("💻 System Resources")
sys_metrics = stats.get("system_metrics", {})

if sys_metrics:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("CPU Usage", f"{sys_metrics.get('cpu_percent', 0):.1f}%")
    with col2:
        st.metric("Memory Usage", f"{sys_metrics.get('memory_percent', 0):.1f}%")
    with col3:
        st.metric("Free Memory", f"{sys_metrics.get('memory_available_gb', 0):.1f} GB")

# Navigation
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🏠 Dashboard", width="stretch"):
        st.switch_page("pages/1_🏠_Dashboard.py")

with col2:
    if st.button("💬 Chat", width="stretch"):
        st.switch_page("pages/2_💬_Chat.py")

with col3:
    if st.button("🔬 Analysis", width="stretch"):
        st.switch_page("pages/3_🔬_Analysis_Results.py")
