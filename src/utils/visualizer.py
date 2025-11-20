"""
Visualization Manager for Genomic Data

Generates interactive plots and visualizations for DNA sequence analysis.

Features:
    - GC content sliding window plots
    - ORF linear maps
    - Motif distribution charts
    - Interactive Plotly visualizations

Usage:
    from src.utils.visualizer import VisualizationManager
    
    vis = VisualizationManager()
    gc_fig = vis.plot_gc_content(sequence, window_size=100)
    orf_fig = vis.plot_orf_map(orfs, seq_length)
    gc_fig.write_image("gc_plot.png")
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Any
import os

class VisualizationManager:
    """
    Interactive visualization generator for genomic data using Plotly.
    
    Produces publication-quality interactive plots for sequence properties,
    ORF maps, and protein analysis. All methods are static and return
    Plotly Figure objects for display, saving, or embedding.
    
    Methods:
        plot_gc_content: Sliding window GC% distribution
        plot_orf_map: Linear ORF position mapping
        plot_protein_scatter: Protein property correlation plot
        save_plot_image: PNG export utility
    """

    @staticmethod
    def plot_gc_content(sequence: str, window_size: int = 100) -> go.Figure:
        """
        Generates sliding window GC content distribution plot.
        
        Calculates GC percentage for overlapping windows across sequence.
        Uses 10 bp step size for performance optimization.
        
        Args:
            sequence (str): DNA sequence string
            window_size (int, optional): Window size in bp. Default: 100
        
        Returns:
            go.Figure: Interactive Plotly line plot with:
                - X-axis: Sequence position (bp)
                - Y-axis: GC content (%)
                - Title: "GC Content (Window Size: Xbp)"
        
        Example:
            >>> fig = VisualizationManager.plot_gc_content("ATGCGTAC...", window_size=50)
            >>> fig.show()
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
        Generates linear genomic map showing ORF positions and orientations.
        
        Displays ORFs as colored blocks on horizontal sequence backbone.
        Forward strand ORFs shown in blue, reverse strand in red.
        
        Args:
            orfs (List[Dict]): ORF dictionaries with keys:
                - start (int): Start position (1-based)
                - end (int): End position (1-based)  
                - strand (str, optional): "+" or "-" for orientation
            seq_length (int): Total sequence length for scaling
        
        Returns:
            go.Figure: Interactive Plotly figure with:
                - Horizontal sequence backbone (gray line)
                - ORF blocks colored by strand
                - Hover labels with position information
        
        Example:
            >>> orfs = [{"start": 100, "end": 300, "strand": "+"}]
            >>> fig = VisualizationManager.plot_orf_map(orfs, 5000)
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
        Creates protein property correlation scatter plot.
        
        Visualizes molecular weight vs hydrophobicity relationships.
        Point size represents protein length in amino acids.
        
        Args:
            proteins (List[Dict]): Protein data with keys:
                - properties (Dict): MW and hydrophobicity values
                - aa_sequence (str): Amino acid sequence
        
        Returns:
            go.Figure: Scatter plot with:
                - X-axis: Molecular Weight (Da)
                - Y-axis: Hydrophobicity score
                - Point size: Protein length (aa)
                - Hover: Protein identifier and full properties
        
        Example:
            >>> proteins = [{"properties": {"molecular_weight": 25000, "hydrophobicity": 0.5}, "aa_sequence": "MVFG..."}]
            >>> fig = VisualizationManager.plot_protein_scatter(proteins)
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
        Saves Plotly figure as static PNG image file.
        
        Exports interactive figure to high-resolution PNG for reports
        and presentations. Automatically creates output directory.
        
        Args:
            fig (go.Figure): Plotly Figure object to save
            filename (str): Output filename (e.g., "plot.png")
            output_dir (str): Output directory path (created if needed)
        
        Returns:
            str: Full path to saved image file
        
        Requires:
            kaleido package: Must be installed for image export
        
        Example:
            >>> fig = VisualizationManager.plot_gc_content("ATGC...")
            >>> path = VisualizationManager.save_plot_image(fig, "gc.png", "plots")
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        path = os.path.join(output_dir, filename)
        fig.write_image(path)
        return path
