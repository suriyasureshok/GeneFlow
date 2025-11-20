import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Any
import os

class VisualizationManager:
    """
    Generates interactive plots for genomic data.
    """

    @staticmethod
    def plot_gc_content(sequence: str, window_size: int = 100) -> go.Figure:
        """
        Generates a sliding window GC content plot.
        """
        gc_values = []
        positions = []
        
        for i in range(0, len(sequence) - window_size, 10): # Step of 10 for speed
            window = sequence[i:i+window_size]
            gc = (window.count('G') + window.count('C')) / len(window) * 100
            gc_values.append(gc)
            positions.append(i + window_size // 2)
            
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=positions, y=gc_values, mode='lines', name='GC Content'))
        fig.update_layout(
            title=f"GC Content (Window Size: {window_size}bp)",
            xaxis_title="Position (bp)",
            yaxis_title="GC %",
            template="plotly_white"
        )
        return fig

    @staticmethod
    def plot_orf_map(orfs: List[Dict[str, Any]], seq_length: int) -> go.Figure:
        """
        Generates a linear map of ORFs.
        """
        fig = go.Figure()
        
        # Draw the backbone
        fig.add_trace(go.Scatter(
            x=[0, seq_length], y=[0, 0],
            mode='lines', line=dict(color='gray', width=2),
            showlegend=False
        ))
        
        for i, orf in enumerate(orfs):
            start, end = orf['start'], orf['end']
            strand = orf.get('strand', '+')
            color = 'blue' if strand == '+' else 'red'
            
            # Draw ORF arrow/block
            fig.add_trace(go.Scatter(
                x=[start, end, end, start, start],
                y=[0.1, 0.1, -0.1, -0.1, 0.1],
                fill='toself',
                fillcolor=color,
                line=dict(color=color),
                name=f"ORF {i+1} ({start}-{end})",
                hoverinfo='name'
            ))
            
        fig.update_layout(
            title="ORF Map",
            xaxis_title="Position (bp)",
            yaxis_visible=False,
            height=300,
            template="plotly_white"
        )
        return fig

    @staticmethod
    def plot_protein_scatter(proteins: List[Dict[str, Any]]) -> go.Figure:
        """
        Scatter plot of Molecular Weight vs Hydrophobicity.
        """
        data = []
        for i, p in enumerate(proteins):
            props = p.get('properties', {})
            data.append({
                "Name": f"Protein {i+1}",
                "MW": props.get('molecular_weight', 0),
                "Hydrophobicity": props.get('hydrophobicity', 0),
                "Length": len(p.get('aa_sequence', ''))
            })
            
        df = pd.DataFrame(data)
        if df.empty:
            return go.Figure()
            
        fig = px.scatter(
            df, x="MW", y="Hydrophobicity",
            size="Length", hover_name="Name",
            title="Protein Properties: MW vs Hydrophobicity",
            template="plotly_white"
        )
        return fig

    @staticmethod
    def save_plot_image(fig: go.Figure, filename: str, output_dir: str):
        """
        Saves a plotly figure as a static image for PDF.
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        path = os.path.join(output_dir, filename)
        fig.write_image(path)
        return path
