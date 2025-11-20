"""
GeneFlow Statistics Page

Detailed performance metrics and usage analytics dashboard.

Features:
    - Execution metrics (time, tokens, cost)
    - Success/failure rates
    - Agent performance comparison
    - Historical trends
    - Interactive charts and graphs

Navigation: Accessible via Dashboard or sidebar
"""

import streamlit as st
import sys
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.core.monitoring import PerformanceMonitor

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

# Add refresh button
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

st.markdown("---")

# Get stats
stats = st.session_state.performance_monitor.get_summary_stats()

# Debug information
with st.expander("🔍 Debug Information"):
    st.write(f"**Monitor Instance ID:** {id(st.session_state.performance_monitor)}")
    st.write(f"**Storage Path:** {st.session_state.performance_monitor.storage_path}")
    st.write(f"**Total Executions Tracked:** {len(st.session_state.performance_monitor.executions)}")
    st.write(f"**Counters:** {dict(st.session_state.performance_monitor.counters)}")
    st.json(stats)

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
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        if not df.empty:
            fig = px.pie(df, values='Count', names='Agent', title='Execution Distribution')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if not df.empty:
            fig = px.bar(df, x='Agent', y='Tokens', title='Token Usage by Agent')
            st.plotly_chart(fig, use_container_width=True)
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
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/1_🏠_Dashboard.py")

with col2:
    if st.button("💬 Chat", use_container_width=True):
        st.switch_page("pages/2_💬_Chat.py")

with col3:
    if st.button("🔬 Analysis", use_container_width=True):
        st.switch_page("pages/3_🔬_Analysis_Results.py")
