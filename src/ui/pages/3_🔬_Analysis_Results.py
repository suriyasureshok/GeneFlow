"""
GeneFlow Analysis Results Page

Comprehensive display of DNA sequence analysis results with download functionality.

Features:
    - Sequence analysis summary (GC content, ORFs, motifs)
    - Interactive visualizations
    - 3D DNA structure viewer
    - Literature review section
    - Research hypotheses
    - PDF report download

Navigation: Accessible after analysis completion or via sidebar
"""

import streamlit as st
import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Page configuration
st.set_page_config(
    page_title="Analysis Results",
    page_icon="🔬",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .analysis-section {
        background-color: #1f2937;
        padding: 2rem;
        border-radius: 0.75rem;
        margin: 1.5rem 0;
    }
    .metric-box {
        background-color: #374151;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #10b981;
        margin: 1rem 0;
    }
    .download-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 0.75rem;
        color: white;
        text-align: center;
        margin: 2rem 0;
    }
    .content-section {
        background-color: #1f2937;
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
        border-left: 4px solid #3b82f6;
    }
    .orf-card {
        background-color: #374151;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .motif-card {
        background-color: #374151;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 3px solid #f59e0b;
    }
    .hypothesis-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        color: white;
        margin: 1rem 0;
    }
    .literature-card {
        background-color: #374151;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 3px solid #8b5cf6;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🔬 Analysis Report")
st.markdown("### Complete DNA Sequence Analysis Report")
st.markdown("---")

# Check if results exist
if 'latest_analysis_results' not in st.session_state or not st.session_state.latest_analysis_results:
    st.warning("⚠️ No analysis results available. Please analyze a DNA sequence first.")
    
    if st.button("💬 Go to Chat", type="primary"):
        st.switch_page("pages/2_💬_Chat.py")
    
    st.stop()

results = st.session_state.latest_analysis_results
analysis = results.get('analysis', {})

# Navigation Buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("💬 Back to Chat", use_container_width=True):
        st.switch_page("pages/2_💬_Chat.py")
with col2:
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/1_🏠_Dashboard.py")
with col3:
    if st.button("🔄 New Analysis", use_container_width=True):
        st.session_state.chat_messages = []
        st.switch_page("pages/2_💬_Chat.py")

st.markdown("---")

# --- ANALYSIS OVERVIEW ---
st.markdown("## 📊 Analysis Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="metric-box">', unsafe_allow_html=True)
    st.metric("Sequence Length", f"{results.get('sequence_length', 'N/A')} bp")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    if isinstance(analysis, dict):
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("GC Content", f"{analysis.get('gc_percent', 'N/A')}%")
        st.markdown('</div>', unsafe_allow_html=True)

with col3:
    if isinstance(analysis, dict):
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("ORFs Found", len(analysis.get('orfs', [])))
        st.markdown('</div>', unsafe_allow_html=True)

# Analysis Summary
if st.session_state.get('latest_analysis_response'):
    st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
    st.markdown(st.session_state.latest_analysis_response)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# --- SEQUENCE DETAILS ---
st.markdown("## 🧬 Sequence Details")

st.markdown('<div class="content-section">', unsafe_allow_html=True)
sequence = results.get('sequence', 'N/A')
st.markdown("### DNA Sequence")
st.code(sequence, language="")
st.markdown('</div>', unsafe_allow_html=True)

# --- SEQUENCE ANALYSIS ---
if isinstance(analysis, dict):
    st.markdown("## 🔬 Detailed Analysis")
    
    # ORFs Section
    if analysis.get('orfs'):
        st.markdown("### 🎯 Open Reading Frames (ORFs)")
        st.markdown('<div class="content-section">', unsafe_allow_html=True)
        
        for i, orf in enumerate(analysis['orfs'], 1):
            st.markdown(f"""
            <div class="orf-card">
                <strong>ORF {i}</strong><br>
                <strong>Position:</strong> {orf.get('start', 'N/A')} - {orf.get('end', 'N/A')}<br>
                <strong>Frame:</strong> {orf.get('frame', 'N/A')} | 
                <strong>Strand:</strong> {orf.get('strand', 'N/A')}<br>
                <strong>Length:</strong> {orf.get('length', 'N/A')} bp
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Motifs Section
    if analysis.get('motifs'):
        st.markdown("### 🔍 Detected Motifs")
        st.markdown('<div class="content-section">', unsafe_allow_html=True)
        
        for motif in analysis['motifs']:
            st.markdown(f"""
            <div class="motif-card">
                <strong>Motif:</strong> {motif.get('motif', 'Unknown')}<br>
                <strong>Position:</strong> {motif.get('position', 'N/A')}<br>
                <strong>Match:</strong> {motif.get('match', 'N/A')}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- VISUALIZATIONS ---
st.markdown("## 📊 Visualizations")

viz = results.get('visualizations', {})
if isinstance(viz, dict):
    plots_dir = viz.get('output_directory', 'geneflow_plots')
    structure_image = viz.get('structure_image')
    structure_pdb = viz.get('structure_pdb')
    
    # 3D Structure
    if structure_image and os.path.exists(structure_image):
        st.markdown("### 🧊 3D Structure Model")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.image(structure_image, caption="3D B-DNA Model", use_container_width=True)
        
        with col2:
            st.markdown("""
            **Model Details:**
            - Format: PDB
            - Type: B-DNA (Right-handed helix)
            - Generated from sequence
            """)
            
            if structure_pdb and os.path.exists(structure_pdb):
                with open(structure_pdb, 'rb') as f:
                    st.download_button(
                        label="📥 Download PDB File",
                        data=f,
                        file_name=os.path.basename(structure_pdb),
                        mime="chemical/x-pdb",
                        use_container_width=True
                    )
    
    # Other Plots
    plots_path = Path(plots_dir)
    if plots_path.exists():
        plot_files = list(plots_path.glob("*.png")) + list(plots_path.glob("*.jpg"))
        plot_files = [p for p in plot_files if "structure_3d" not in p.name]
        
        if plot_files:
            st.markdown("### 📈 Analysis Plots")
            cols = st.columns(2)
            for i, plot_file in enumerate(plot_files):
                with cols[i % 2]:
                    st.image(str(plot_file), caption=plot_file.stem.replace('_', ' ').title(), use_container_width=True)

st.markdown("---")

# --- DOWNLOAD REPORT SECTION ---
st.markdown("## 📥 Download Complete Report")

report = results.get('report', {})

# Check for report path or default
report_path_str = report.get('report_path') if isinstance(report, dict) else None
if not report_path_str:
    # Check default location
    default_report = Path("reports/geneflow_analysis_report.pdf")
    if default_report.exists():
        report_path_str = str(default_report)

if report_path_str:
    report_path = Path(report_path_str)
    
    if report_path.exists():
        st.markdown('<div class="download-section">', unsafe_allow_html=True)
        st.markdown("### ✅ Report Ready for Download")
        st.markdown(f"""
        Your comprehensive analysis report is ready. This report includes:
        - Detailed sequence analysis
        - ORF and motif detection results
        - 3D structure information
        - Literature review
        - Research hypotheses
        - All visualizations
        """)
        
        # Download button
        with open(report_path, 'rb') as f:
            st.download_button(
                label="📥 Download PDF Report",
                data=f,
                file_name=report_path.name,
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
        
        st.markdown(f"**File location:** `{report_path}`")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.error("❌ Report file not found at expected location.")
        st.info(f"Expected location: `{report_path}`")
else:
    st.warning("⚠️ Report generation may have failed or is in progress.")
    if isinstance(report, str):
        st.code(report)

# Footer
st.markdown("---")
st.caption("🔬 GeneFlow - Advanced DNA Sequence Analysis")
