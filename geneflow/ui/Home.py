"""
GeneFlow - Main Landing Page
Bioinformatics Copilot powered by Google ADK
"""

import streamlit as st
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from geneflow.core.session_manager import SessionManager
from geneflow.core.monitoring import PerformanceMonitor

# Page configuration
st.set_page_config(
    page_title="GeneFlow - Bioinformatics Copilot",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .hero-header {
        font-size: 3.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #60a5fa, #93c5fd);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin: 2rem 0;
    }
    .hero-subtitle {
        font-size: 1.5rem;
        text-align: center;
        color: #9ca3af;
        margin-bottom: 3rem;
    }
    .feature-card {
        background-color: #1f2937;
        padding: 2rem;
        border-radius: 1rem;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
        transition: transform 0.2s;
    }
    .feature-card:hover {
        transform: translateY(-5px);
    }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        color: white;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Initialize managers
if 'session_manager' not in st.session_state:
    st.session_state.session_manager = SessionManager(storage_path="sessions")
if 'performance_monitor' not in st.session_state:
    st.session_state.performance_monitor = PerformanceMonitor(storage_path="metrics")

# Hero Section
st.markdown('<p class="hero-header">🧬 GeneFlow</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Your Agentic Bioinformatics Copilot</p>', unsafe_allow_html=True)

# Main CTA Buttons
col1, col2, col3 = st.columns(3)

with col1:
    st.write("")  # Spacing

with col2:
    if st.button("🚀 Launch GeneFlow", type="primary", width="stretch"):
        st.switch_page("pages/1_🏠_Dashboard.py")
    
    if st.button("💬 Start Chat", width="stretch"):
        st.switch_page("pages/2_💬_Chat.py")

with col3:
    st.write("")  # Spacing

st.markdown("---")

# Features Section
st.subheader("✨ Key Features")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>🤖 AI-Powered Analysis</h3>
        <p>Advanced DNA sequence analysis using Google's Gemini 2.5 Flash model</p>
        <ul>
            <li>GC Content Analysis</li>
            <li>ORF Detection</li>
            <li>Motif Recognition</li>
            <li>Protein Predictions</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <h3>📚 Literature Integration</h3>
        <p>Automatic scientific literature search and synthesis</p>
        <ul>
            <li>PubMed Integration</li>
            <li>Relevant Paper Discovery</li>
            <li>Context-Aware Research</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>💡 Hypothesis Generation</h3>
        <p>AI-driven research hypothesis formulation</p>
        <ul>
            <li>Data-Driven Insights</li>
            <li>Confidence Scoring</li>
            <li>Rationale Explanation</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <h3>📊 Visual Reports</h3>
        <p>Comprehensive visualization and reporting</p>
        <ul>
            <li>Interactive Plots</li>
            <li>PDF Report Generation</li>
            <li>Export Capabilities</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Technology Stack
st.subheader("🔧 Powered By")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="stat-box">
        <strong>Google ADK</strong><br>
        Agent Development Kit
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="stat-box">
        <strong>Gemini 2.5</strong><br>
        Flash Model
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="stat-box">
        <strong>Streamlit</strong><br>
        Web Framework
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="stat-box">
        <strong>BioPython</strong><br>
        Core Analysis
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Quick Stats
stats = st.session_state.performance_monitor.get_summary_stats()
session_stats = st.session_state.session_manager.get_session_stats()

st.subheader("📈 System Status")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Analyses", stats.get("total_executions", 0))
with col2:
    st.metric("Active Sessions", session_stats.get("active_today", 0))
with col3:
    st.metric("Success Rate", f"{stats.get('success_rate', 0):.1f}%")
with col4:
    if os.getenv("GOOGLE_API_KEY"):
        st.metric("API Status", "✅ Connected")
    else:
        st.metric("API Status", "❌ Not Configured")

st.markdown("---")

# Getting Started
st.subheader("🚀 Getting Started")

st.markdown("""
### How to Use GeneFlow

1. **Configure API Key**: Set your `GOOGLE_API_KEY` environment variable
2. **Start Chat**: Navigate to the Chat page to interact with the AI
3. **Analyze Sequences**: Paste DNA sequences for comprehensive analysis
4. **View Results**: Access detailed analysis results with visualizations
5. **Generate Reports**: Download PDF reports of your analyses

### Example DNA Sequence

```
ATGGATCAGAACAACAGCCTGCCACCTTACGCTCAGGGCTTGGCCTCCCCGCAGGGTGCCATG
```

### Navigation

- **🏠 Dashboard**: System overview and recent activities
- **💬 Chat**: Conversational interface with AI assistant  
- **🔬 Analysis**: Detailed results display
- **📊 Statistics**: Performance metrics and analytics
""")

# Footer
st.markdown("---")
st.caption("GeneFlow v1.0 - Advanced Bioinformatics with AI | Powered by Google ADK & Gemini 2.5 Flash")

# Sidebar
with st.sidebar:
    st.header("🧬 GeneFlow")
    st.markdown("**Version:** 1.0.0")
    st.markdown("**Model:** Gemini 2.5 Flash")
    st.markdown("**Framework:** Google ADK")
    
    st.markdown("---")
    
    st.header("🔑 API Configuration")
    
    api_key_status = "✅ Configured" if os.getenv("GOOGLE_API_KEY") else "❌ Not Set"
    st.info(f"**Status:** {api_key_status}")
    
    if not os.getenv("GOOGLE_API_KEY"):
        st.warning("Please set GOOGLE_API_KEY environment variable")
    
    st.markdown("---")
    
    st.header("📚 Quick Links")
    
    if st.button("📖 Documentation", width="stretch"):
        st.markdown("[View README](README.md)")
    
    if st.button("💻 GitHub", width="stretch"):
        st.markdown("[Repository](#)")
    
    st.markdown("---")
    
    st.caption("© 2024 GeneFlow")
