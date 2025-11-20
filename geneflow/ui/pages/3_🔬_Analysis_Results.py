"""
GeneFlow Analysis Results Page
Comprehensive display of DNA sequence analysis with all components
"""

import streamlit as st
import sys
import os
import json
from pathlib import Path
import plotly.graph_objects as go

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
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #60a5fa;
        margin-bottom: 1rem;
        margin-top: 2rem;
        border-bottom: 1px solid #374151;
        padding-bottom: 0.5rem;
    }
    .metric-box {
        background-color: #374151;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #10b981;
        margin: 0.5rem 0;
    }
    .literature-item {
        background-color: #4b5563;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.75rem 0;
        border-left: 3px solid #8b5cf6;
    }
    .hypothesis-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        color: white;
        margin: 1rem 0;
    }
    .confidence-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        background-color: rgba(255, 255, 255, 0.2);
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🔬 Analysis Results")
st.markdown("### Comprehensive DNA Sequence Analysis")
st.markdown("---")

# Check if results exist
if 'latest_analysis_results' not in st.session_state or not st.session_state.latest_analysis_results:
    st.warning("⚠️ No analysis results available. Please analyze a DNA sequence first.")
    
    if st.button("💬 Go to Chat", type="primary"):
        st.switch_page("pages/2_💬_Chat.py")
    
    st.stop()

results = st.session_state.latest_analysis_results
analysis = results.get('analysis', {})

# Navigation Buttons (Top)
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("💬 Back to Chat", width="stretch"):
        st.switch_page("pages/2_💬_Chat.py")
with col2:
    if st.button("🏠 Dashboard", width="stretch"):
        st.switch_page("pages/1_🏠_Dashboard.py")
with col3:
    if st.button("🔄 Run New Analysis", width="stretch"):
        st.session_state.chat_messages = []
        st.switch_page("pages/2_💬_Chat.py")

# --- 1. OVERVIEW SECTION ---
st.markdown('<div class="section-header">📊 Analysis Overview</div>', unsafe_allow_html=True)

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

# Summary Text
if st.session_state.get('latest_analysis_response'):
    st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
    st.markdown("### 📝 Analysis Summary")
    st.markdown(st.session_state.latest_analysis_response)
    st.markdown('</div>', unsafe_allow_html=True)


# --- 2. SEQUENCE ANALYSIS SECTION ---
st.markdown('<div class="section-header">🧬 Sequence Analysis Details</div>', unsafe_allow_html=True)

if isinstance(analysis, dict):
    # Sequence display
    st.markdown("### 🧬 Sequence")
    sequence = results.get('sequence', 'N/A')
    st.code(sequence, language="")
    
    # ORFs
    if analysis.get('orfs'):
        st.markdown("### 🎯 Open Reading Frames (ORFs)")
        
        for i, orf in enumerate(analysis['orfs'], 1):
            st.markdown(f"""
            <div class="metric-box">
                <strong>ORF {i}</strong><br>
                Start: {orf.get('start', 'N/A')} | End: {orf.get('end', 'N/A')} | Frame: {orf.get('frame', 'N/A')}<br>
                Length: {orf.get('length', 'N/A')} bp | Strand: {orf.get('strand', 'N/A')}
            </div>
            """, unsafe_allow_html=True)
    
    # Motifs
    if analysis.get('motifs'):
        st.markdown("### 🔍 Detected Motifs")
        
        for motif in analysis['motifs']:
            st.markdown(f"""
            <div class="metric-box">
                <strong>{motif.get('motif', 'Unknown Motif')}</strong><br>
                Position: {motif.get('position', 'N/A')} | 
                Match: {motif.get('match', 'N/A')}
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("Analysis data is in text format:")
    st.text(analysis)


# --- 3. 3D STRUCTURE SECTION ---
st.markdown('<div class="section-header">🧊 3D Structure Model</div>', unsafe_allow_html=True)

viz = results.get('visualizations', {})
structure_pdb = viz.get('structure_pdb')
structure_image = viz.get('structure_image')

col1, col2 = st.columns([2, 1])

with col1:
    if structure_image and os.path.exists(structure_image):
        st.image(structure_image, caption="3D B-DNA Model Representation", width="stretch")
    else:
        st.info("3D structure image not available.")

with col2:
    st.markdown("### Model Details")
    st.markdown("""
    This 3D model represents a B-DNA helix generated from your sequence.
    
    **Format:** PDB (Protein Data Bank)
    **Type:** B-DNA (Right-handed helix)
    """)
    
    if structure_pdb and os.path.exists(structure_pdb):
        with open(structure_pdb, 'rb') as f:
            st.download_button(
                label="📥 Download PDB File",
                data=f,
                file_name=os.path.basename(structure_pdb),
                mime="chemical/x-pdb",
                width="stretch"
            )
    else:
        st.warning("PDB file not generated.")


# --- 4. VISUALIZATIONS SECTION ---
st.markdown('<div class="section-header">📈 Visualizations</div>', unsafe_allow_html=True)

if isinstance(viz, dict):
    plots_dir = viz.get('output_directory', 'geneflow_plots')
    plots_path = Path(plots_dir)
    
    if plots_path.exists():
        # Display plots (excluding the structure image we already showed)
        plot_files = list(plots_path.glob("*.png")) + list(plots_path.glob("*.jpg"))
        plot_files = [p for p in plot_files if "structure_3d" not in p.name]
        
        if plot_files:
            cols = st.columns(2)
            for i, plot_file in enumerate(plot_files):
                with cols[i % 2]:
                    st.image(str(plot_file), caption=plot_file.name, width="stretch")
        else:
            st.info("No other plot files found.")
    else:
        st.warning(f"Plots directory not found: {plots_dir}")
else:
    st.info("No visualizations available.")


# --- 5. LITERATURE SECTION ---
st.markdown('<div class="section-header">📚 Literature Review</div>', unsafe_allow_html=True)

literature = results.get('literature', '')

if literature:
    st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
    
    # Try to parse as JSON first
    try:
        if isinstance(literature, str) and literature.startswith('{'):
            lit_data = json.loads(literature)
            
            if 'papers' in lit_data:
                for paper in lit_data['papers']:
                    st.markdown(f"""
                    <div class="literature-item">
                        <strong>{paper.get('title', 'Untitled')}</strong><br>
                        <em>{paper.get('authors', 'Unknown authors')}</em><br>
                        {paper.get('summary', 'No summary available')}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.write(lit_data)
        else:
            # Display as text
            st.markdown(literature)
    except:
        st.markdown(literature)
    
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No literature review data available.")


# --- 6. HYPOTHESES SECTION ---
st.markdown('<div class="section-header">💡 Research Hypotheses</div>', unsafe_allow_html=True)

hypotheses = results.get('hypotheses', '')

if hypotheses:
    # Try to parse as JSON
    try:
        if isinstance(hypotheses, str) and hypotheses.startswith('{'):
            hyp_data = json.loads(hypotheses)
            
            if 'hypotheses' in hyp_data:
                for i, hyp in enumerate(hyp_data['hypotheses'], 1):
                    confidence = hyp.get('confidence', 0)
                    
                    st.markdown(f"""
                    <div class="hypothesis-card">
                        <h3>Hypothesis {i}</h3>
                        <p>{hyp.get('hypothesis', 'No hypothesis text')}</p>
                        <div class="confidence-badge">
                            Confidence: {confidence:.0%}
                        </div>
                        <br><br>
                        <strong>Rationale:</strong><br>
                        {hyp.get('rationale', 'No rationale provided')}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.write(hyp_data)
        else:
            # Display as text
            st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
            st.markdown(hypotheses)
            st.markdown('</div>', unsafe_allow_html=True)
    except:
        st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
        st.markdown(hypotheses)
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No hypotheses generated.")


# --- 7. REPORT SECTION ---
st.markdown('<div class="section-header">📄 PDF Report</div>', unsafe_allow_html=True)

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
    
    st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
    st.markdown("### 📑 Generated Report")
    
    if report_path.exists():
        st.success(f"✅ Report generated successfully!")
        st.info(f"**Location:** `{report_path}`")
        
        # Provide download button
        with open(report_path, 'rb') as f:
            st.download_button(
                label="📥 Download PDF Report",
                data=f,
                file_name=report_path.name,
                mime="application/pdf",
                width="stretch"
            )
    else:
        st.warning("Report file not found at expected location.")
    
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Report generation may have failed or is in progress.")
    
    if isinstance(report, str):
        st.text(report)

# Footer
st.markdown("---")
st.caption("🔬 GeneFlow Analysis Complete")
