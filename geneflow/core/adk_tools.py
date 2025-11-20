"""
ADK Tool Definitions for GeneFlow Bioinformatics Pipeline
All analysis functions exposed as ADK-compatible tools
"""

import logging
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)


# Import analysis modules
from geneflow.agents.sequence_analyzer import SequenceAnalyzerAgent
from geneflow.agents.protein_prediction import ProteinPredictionAgent
from geneflow.agents.comparison import ComparisonAgent
from geneflow.utils.visualizer import VisualizationManager
from geneflow.utils.reporter import create_pdf


def analyze_sequence(sequence: str) -> str:
    """
    Analyzes a DNA/RNA sequence to determine GC content, find Open Reading Frames (ORFs), 
    and scan for regulatory motifs like TATA box, CAAT box, Kozak consensus, etc.
    
    This is the first step in any sequence analysis pipeline.
    
    Args:
        sequence: DNA or RNA sequence string (e.g., "ATGCGTACG...")
        
    Returns:
        JSON string containing:
        - valid: Boolean indicating if sequence is valid
        - sequence_type: "DNA" or "RNA"
        - length: Length of the sequence
        - gc_percent: GC content percentage
        - orfs: List of ORFs with start, end, frame, length, and sequence
        - motifs: List of regulatory motifs found
        - cleaned_sequence: Cleaned and validated sequence
    """
    logger.info(f"Tool called: analyze_sequence with sequence length {len(sequence)}")
    
    try:
        agent = SequenceAnalyzerAgent()
        result = agent.analyze(sequence)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Sequence analysis failed: {e}")
        return json.dumps({"error": str(e), "valid": False})


def predict_protein_properties(orf_sequence: str, orf_start: int = 0, orf_end: int = None) -> str:
    """
    Predicts protein properties from a DNA ORF sequence including amino acid sequence,
    molecular weight, hydrophobicity, and signal peptide presence.
    
    Use this after finding ORFs with analyze_sequence.
    
    Args:
        orf_sequence: DNA sequence of the ORF (e.g., "ATGAAATAG...")
        orf_start: Start position of the ORF (default: 0)
        orf_end: End position of the ORF (default: length of sequence)
        
    Returns:
        JSON string containing:
        - orf_id: Identifier for the ORF
        - aa_sequence: Translated amino acid sequence
        - length: Length of the protein in amino acids
        - properties: Dict with molecular_weight and hydrophobicity
        - signal_peptide: Boolean indicating if signal peptide detected
    """
    logger.info(f"Tool called: predict_protein_properties for ORF length {len(orf_sequence)}")
    
    try:
        agent = ProteinPredictionAgent()
        orf_dict = {
            "sequence": orf_sequence,
            "start": orf_start,
            "end": orf_end or len(orf_sequence)
        }
        result = agent.predict(orf_dict)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Protein prediction failed: {e}")
        return json.dumps({"error": str(e)})


def search_literature(keywords: str, max_results: int = 5) -> str:
    """
    Searches scientific literature databases for relevant papers based on keywords.
    Returns papers with titles, authors, summaries, and DOIs.
    
    Use this to find research context for your findings.
    
    Args:
        keywords: Comma-separated keywords (e.g., "TATA box, transcription, protein binding")
        max_results: Maximum number of papers to return (default: 5)
        
    Returns:
        JSON string with list of papers containing:
        - title: Paper title
        - authors: Author names
        - year: Publication year
        - summary: Abstract or summary
        - doi: Digital Object Identifier
    """
    logger.info(f"Tool called: search_literature with keywords: {keywords}")
    
    try:
        from geneflow.agents.literature import LiteratureAgent
        
        # Split keywords
        keyword_list = [k.strip() for k in keywords.split(",")]
        
        # Use offline mode for reliability in demo
        agent = LiteratureAgent(offline_mode=True)
        results = agent.search(keyword_list)
        
        # Limit results
        results = results[:max_results]
        
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Literature search failed: {e}")
        return json.dumps({"error": str(e), "results": []})


def compare_with_database(sequence: str, database: str = "nt", program: str = "blastn") -> str:
    """
    Compares a DNA sequence against NCBI databases using BLAST to find homologous sequences
    and potential evolutionary relationships.
    
    WARNING: This tool makes online API calls and may take 1-2 minutes.
    
    Args:
        sequence: DNA sequence to compare
        database: NCBI database to search (default: "nt" for nucleotide)
        program: BLAST program to use (default: "blastn")
        
    Returns:
        JSON string with list of matches containing:
        - header: Match description
        - similarity: Similarity score (0-1)
        - e_value: Statistical significance
        - alignment: Alignment preview
    """
    logger.info(f"Tool called: compare_with_database for sequence length {len(sequence)}")
    
    try:
        agent = ComparisonAgent()
        orf_dict = {
            "sequence": sequence,
            "start": 0,
            "end": len(sequence)
        }
        results = agent.compare([orf_dict])
        
        if results:
            return json.dumps(results[0], indent=2)
        else:
            return json.dumps({"matches": [], "message": "No matches found"})
            
    except Exception as e:
        logger.error(f"Database comparison failed: {e}")
        return json.dumps({"error": str(e), "matches": []})


def generate_hypothesis(analysis_summary: str, confidence_threshold: float = 0.7) -> str:
    """
    Generates research hypotheses based on analysis findings including sequence features,
    protein properties, literature context, and homology matches.
    
    This is typically the final analytical step.
    
    Args:
        analysis_summary: Text summary of all analysis findings
        confidence_threshold: Minimum confidence level (0-1, default: 0.7)
        
    Returns:
        JSON string with list of hypotheses containing:
        - hypothesis: The research hypothesis
        - confidence: Confidence score (0-1)
        - evidence: Supporting evidence from analysis
        - suggested_experiments: Recommended validation experiments
    """
    logger.info(f"Tool called: generate_hypothesis")
    
    try:
        # Generate structured hypotheses based on the summary
        # This uses rule-based logic as a fallback
        hypotheses = []
        
        # Parse the summary for key findings
        if "TATA" in analysis_summary.upper() or "CAAT" in analysis_summary.upper():
            hypotheses.append({
                "hypothesis": "This sequence contains transcriptional regulatory elements that may control gene expression",
                "confidence": 0.85,
                "evidence": "Presence of TATA box and/or CAAT box promoter elements",
                "suggested_experiments": ["Promoter activity assay", "ChIP-seq analysis", "Mutagenesis study"]
            })
        
        if "SIGNAL PEPTIDE" in analysis_summary.upper() or "HYDROPHOBIC" in analysis_summary.upper():
            hypotheses.append({
                "hypothesis": "The encoded protein may be secreted or membrane-associated",
                "confidence": 0.78,
                "evidence": "Signal peptide detected and/or high hydrophobicity in N-terminal region",
                "suggested_experiments": ["Protein localization studies", "Western blot analysis", "Immunofluorescence"]
            })
        
        if "ORF" in analysis_summary.upper():
            hypotheses.append({
                "hypothesis": "This sequence encodes a functional protein with potential biological activity",
                "confidence": 0.75,
                "evidence": "Valid open reading frames detected with start and stop codons",
                "suggested_experiments": ["Protein expression and purification", "Functional assays", "Structural analysis"]
            })
        
        # If no specific hypotheses, generate a general one
        if not hypotheses:
            hypotheses.append({
                "hypothesis": "This sequence represents a genomic region requiring further characterization",
                "confidence": 0.60,
                "evidence": "Basic sequence features identified, detailed function unclear",
                "suggested_experiments": ["RNA-seq analysis", "Conservation analysis", "Database homology searches"]
            })
        
        # Filter by confidence
        hypotheses = [h for h in hypotheses if h["confidence"] >= confidence_threshold]
        
        return json.dumps(hypotheses, indent=2)
        
    except Exception as e:
        logger.error(f"Hypothesis generation failed: {e}")
        return json.dumps({"error": str(e), "hypotheses": []})


def create_visualizations(
    sequence: str,
    analysis_data: str,
    output_dir: str = "geneflow_plots"
) -> str:
    """
    Generates publication-quality visualizations including GC content plot, ORF map,
    and protein property scatter plots.
    
    Args:
        sequence: DNA sequence
        analysis_data: JSON string containing analysis results (from analyze_sequence and predict_protein_properties)
        output_dir: Directory to save plots (default: "geneflow_plots")
        
    Returns:
        JSON string with paths to generated plots:
        - gc_plot: Path to GC content visualization
        - orf_map: Path to ORF map
        - protein_scatter: Path to protein properties plot
        - output_directory: Base directory for all plots
    """
    logger.info(f"Tool called: create_visualizations")
    
    try:
        import os
        from pathlib import Path
        
        # Parse analysis data
        data = json.loads(analysis_data) if isinstance(analysis_data, str) else analysis_data
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        plots = {}
        
        # GC Content Plot
        if sequence:
            fig_gc = VisualizationManager.plot_gc_content(sequence)
            gc_path = VisualizationManager.save_plot_image(fig_gc, "gc_content.png", output_dir)
            plots["gc_plot"] = gc_path
        
        # ORF Map
        if "orfs" in data:
            fig_orf = VisualizationManager.plot_orf_map(data["orfs"], len(sequence))
            orf_path = VisualizationManager.save_plot_image(fig_orf, "orf_map.png", output_dir)
            plots["orf_map"] = orf_path
        
        # Protein Properties (if we have protein data)
        if "proteins" in data:
            fig_prot = VisualizationManager.plot_protein_scatter(data["proteins"])
            prot_path = VisualizationManager.save_plot_image(fig_prot, "protein_properties.png", output_dir)
            plots["protein_scatter"] = prot_path
        
        plots["output_directory"] = output_dir
        plots["success"] = True
        
        return json.dumps(plots, indent=2)
        
    except Exception as e:
        logger.error(f"Visualization generation failed: {e}")
        return json.dumps({"error": str(e), "success": False})


def generate_report(
    analysis_results: str,
    plots_directory: str = "geneflow_plots",
    output_filename: str = "geneflow_report.pdf"
) -> str:
    """
    Generates a comprehensive PDF research report with all analysis findings,
    visualizations, hypotheses, and literature references.
    
    This should be called last after all analyses are complete.
    
    Args:
        analysis_results: JSON string with all analysis results
        plots_directory: Directory containing generated plots
        output_filename: Name for the output PDF file
        
    Returns:
        JSON string with:
        - success: Boolean indicating if report was generated
        - report_path: Path to the generated PDF
        - pages: Number of pages in the report
    """
    logger.info(f"Tool called: generate_report")
    
    try:
        # Parse results
        results = json.loads(analysis_results) if isinstance(analysis_results, str) else analysis_results
        
        # Generate PDF report
        report_path = create_pdf(
            data=results,
            plots_dir=plots_directory,
            output_path=output_filename
        )
        
        return json.dumps({
            "success": True,
            "report_path": report_path,
            "message": f"Report generated successfully at {report_path}"
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return json.dumps({"error": str(e), "success": False})


# Tool registry for easy access
ADK_TOOLS = [
    analyze_sequence,
    predict_protein_properties,
    search_literature,
    compare_with_database,
    generate_hypothesis,
    create_visualizations,
    generate_report
]


def get_all_tools() -> List:
    """Returns all ADK-compatible tools"""
    return ADK_TOOLS


def get_tool_by_name(tool_name: str):
    """Get a specific tool by name"""
    tool_map = {tool.__name__: tool for tool in ADK_TOOLS}
    return tool_map.get(tool_name)
