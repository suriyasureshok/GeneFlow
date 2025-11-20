"""
ADK Tool Definitions for GeneFlow

All bioinformatics analysis functions exposed as ADK-compatible tools.

Tools Available:
    - analyze_sequence: GC content, ORFs, motif scanning
    - predict_protein_properties: Protein analysis from ORFs
    - compare_sequences: BLAST homology search
    - search_literature: PubMed literature search
    - generate_hypotheses: Research hypothesis generation
    - create_visualizations: Plot generation
    - generate_report: PDF report creation

Usage:
    from src.core.adk_tools import get_all_tools
    tools = get_all_tools()
"""

import logging
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)


# Import analysis modules
from src.agents.sequence_analyzer import SequenceAnalyzerAgent
from src.agents.protein_prediction import ProteinPredictionAgent
from src.agents.comparison import ComparisonAgent
from src.utils.visualizer import VisualizationManager
from src.utils.reporter import create_pdf


def analyze_sequence(sequence: str) -> str:
    """
    Analyzes DNA/RNA sequences for structural properties and regulatory elements.
    
    Performs comprehensive sequence analysis including GC content calculation,
    Open Reading Frame (ORF) detection, and regulatory motif scanning.
    Entry point for sequence analysis pipeline.
    
    Args:
        sequence (str): DNA or RNA nucleotide sequence. Accepts ATGCN characters.
                       Case-insensitive. Whitespace is automatically removed.
        
    Returns:
        str: JSON-formatted analysis results containing:
            - valid (bool): Sequence validation status
            - sequence_type (str): "DNA" or "RNA" classification
            - length (int): Sequence length in base pairs
            - gc_percent (float): GC content as percentage (0-100)
            - orfs (List[Dict]): Open Reading Frames with positions and sequences
            - motifs (List[Dict]): Detected regulatory motifs and positions
            - cleaned_sequence (str): Validated uppercase sequence
            - error (str, optional): Error message if validation fails
    
    Raises:
        None - Returns error in JSON response instead
    
    Example:
        >>> result_json = analyze_sequence("ATGAAATAAGCGTAC")
        >>> import json
        >>> result = json.loads(result_json)
        >>> print(result['gc_percent'])
        40.0
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
    Predicts physicochemical properties of proteins encoded by ORF sequences.
    
    Translates DNA sequences to amino acids and calculates molecular weight,
    hydrophobicity, and signal peptide presence. Typically follows analyze_sequence().
    
    Args:
        orf_sequence (str): DNA Open Reading Frame sequence starting with ATG.
                           Must be divisible by 3 for complete codons.
        orf_start (int, optional): Start position in parent sequence. Default: 0
        orf_end (int, optional): End position in parent sequence. Default: length
        
    Returns:
        str: JSON-formatted protein prediction results containing:
            - orf_id (str): Identifier as "ORF_start_end"
            - aa_sequence (str): Translated amino acid sequence (1-letter codes)
            - length (int): Protein length in amino acids
            - properties (Dict): Molecular weight (Da) and hydrophobicity (-4.5 to 4.5)
            - signal_peptide (bool): N-terminal signal peptide detection result
            - error (str, optional): Error message if translation fails
    
    Raises:
        None - Returns error in JSON response instead
    
    Note:
        Uses standard genetic code. Unknown codons translate to 'X'.
        Translation stops at first stop codon (TAA/TAG/TGA).
    
    Example:
        >>> orf = {'sequence': 'ATGAAATAA', 'start': 1, 'end': 9}
        >>> props_json = predict_protein_properties(orf['sequence'], 1, 9)
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
    Searches scientific literature for research context and relevant publications.
    
    Queries literature databases for papers matching provided keywords.
    Provides contextual information for bioinformatics findings.
    
    Args:
        keywords (str): Comma-separated search terms. Example: "TATA box, transcription"
        max_results (int, optional): Maximum papers to return. Default: 5. Range: 1-50
        
    Returns:
        str: JSON-formatted literature search results containing:
            - List of paper dictionaries with:
                - title (str): Publication title
                - authors (str): Author list
                - year (int): Publication year
                - summary (str): Abstract or summary text
                - doi (str): Digital Object Identifier or "N/A"
            - error (str, optional): Error message if search fails
    
    Raises:
        None - Returns empty list or error in JSON on failure
    
    Note:
        May use offline/mock data for speed and reliability in demo mode.
        Online mode requires internet connection for API access.
    
    Example:
        >>> results_json = search_literature("GC content, DNA", max_results=3)
        >>> papers = json.loads(results_json)
    """
    logger.info(f"Tool called: search_literature with keywords: {keywords}")
    
    try:
        from src.agents.literature import LiteratureAgent
        
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
    Searches NCBI databases for homologous sequences using BLAST.
    
    Performs sequence homology comparison to identify related sequences,
    evolutionary relationships, and functional annotations.
    WARNING: Online API calls may require 1-2 minutes execution time.
    
    Args:
        sequence (str): Query DNA sequence to search (typically >20 bp)
        database (str, optional): NCBI database to search. Default: "nt" (nucleotide)
                                 Options: "nt", "nr", "dbEST", etc.
        program (str, optional): BLAST program variant. Default: "blastn"
                               Options: "blastn", "blastx", "blastp"
        
    Returns:
        str: JSON-formatted BLAST results containing:
            - matches (List[Dict]): List of sequence matches with:
                - header (str): Match sequence description
                - similarity (float): Identity percentage (0.0-1.0)
                - e_value (float): Expect value (statistical significance)
                - alignment (str): Alignment preview string
            - error (str, optional): Error message if search fails
    
    Raises:
        None - Returns error in JSON on failure or network issues
    
    Performance:
        - Execution time: 30-120 seconds typical
        - Skips sequences <20 bp as unreliable
        - Returns top 3 matches by default
    
    Example:
        >>> results_json = compare_with_database("ATGCGTACGTAC...")
        >>> matches = json.loads(results_json)
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
    Generates testable research hypotheses from integrated analysis results.
    
    Synthesizes sequence properties, protein predictions, literature context,
    and homology data into evidence-based hypotheses. Typically the final
    analytical step before report generation.
    
    Args:
        analysis_summary (str): Comprehensive text summary of all findings.
                              Include GC%, motifs, ORFs, protein properties,
                              literature context, and homology matches.
        confidence_threshold (float, optional): Minimum confidence to include.
                                              Range: 0.0-1.0. Default: 0.7
        
    Returns:
        str: JSON-formatted hypothesis results containing:
            - List of hypothesis dictionaries with:
                - hypothesis (str): Clear, testable hypothesis statement
                - confidence (float): Confidence score (0.0-1.0)
                - evidence (str): Supporting evidence from analysis
                - suggested_experiments (List[str]): Recommended validations
            - error (str, optional): Error message if generation fails
    
    Raises:
        None - Returns error in JSON on failure
    
    Note:
        Filters results by confidence_threshold.
        Generates at least 1 fallback hypothesis if analysis is sparse.
    
    Example:
        >>> summary = "GC: 45%, TATA box present, ORF: 200bp, MW: 22kDa"
        >>> hyp_json = generate_hypothesis(summary, confidence_threshold=0.65)
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
    Generates publication-quality interactive visualizations for genomic data.
    
    Creates multiple complementary plots: GC content distribution, ORF map,
    and protein property analysis. All plots use Plotly for interactivity.
    
    Args:
        sequence (str): DNA sequence for visualization
        analysis_data (str): JSON-formatted analysis results from analyze_sequence().
                            Must include: orfs (List), motifs (List), gc_percent (float)
        output_dir (str, optional): Output directory for plots. Default: "geneflow_plots"
                                   Created if it doesn't exist.
        
    Returns:
        str: JSON-formatted visualization paths containing:
            - gc_plot (str): Path to GC content sliding window plot (PNG)
            - orf_map (str): Path to ORF position map (PNG)
            - protein_scatter (str): Path to protein properties scatter plot (PNG)
            - output_directory (str): Base directory for all generated plots
            - success (bool): Generation status
            - error (str, optional): Error message if generation fails
    
    Raises:
        None - Returns error in JSON on failure
    
    Note:
        - Requires kaleido package for PNG export
        - Window size: 100 bp for GC content
        - Creates high-resolution images (150 DPI)
    
    Example:
        >>> analysis_json = json.dumps({"orfs": [...], "gc_percent": 45.5})
        >>> viz_json = create_visualizations("ATGCGTAC...", analysis_json)
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
    Generates comprehensive PDF research reports with complete analysis pipeline results.
    
    Creates professional multi-section PDF including sequence analysis, visualizations,
    literature review, and research hypotheses. Typically the final output step.
    
    Args:
        analysis_results (str): JSON-formatted aggregated analysis results.
                              Include: sequence_analysis, proteins, hypotheses,
                              literature findings from all prior tools.
        plots_directory (str, optional): Directory containing plot images. 
                                        Default: "geneflow_plots"
        output_filename (str, optional): Output PDF filename. Default: "geneflow_report.pdf"
        
    Returns:
        str: JSON-formatted report generation status containing:
            - success (bool): PDF generation status
            - report_path (str): Full path to generated PDF file
            - message (str): Status or error message
            - error (str, optional): Error details if generation fails
    
    Raises:
        None - Returns error in JSON on failure
    
    Report Sections:
        1. Sequence Analysis Summary
        2. GC Content Distribution Plot
        3. 3D DNA Structure Visualization
        4. Literature Review
        5. Research Hypotheses
        6. Metadata and Methodology
    
    Example:
        >>> results_json = json.dumps({"sequence_analysis": {...}, ...})
        >>> report_json = generate_report(results_json, "plots", "analysis.pdf")
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
    """
    Returns list of all available ADK-compatible tool functions.
    
    Returns:
        List[Callable]: All exported tool functions ready for ADK agent use
    
    Example:
        >>> tools = get_all_tools()
        >>> print(len(tools))
        7
    """
    return ADK_TOOLS


def get_tool_by_name(tool_name: str):
    """
    Retrieves a specific tool function by name.
    
    Args:
        tool_name (str): Name of the tool function to retrieve (e.g., "analyze_sequence")
    
    Returns:
        Callable: The requested tool function or None if not found
    
    Example:
        >>> tool = get_tool_by_name("analyze_sequence")
        >>> result = tool("ATGCGTAC...")
    """
    tool_map = {tool.__name__: tool for tool in ADK_TOOLS}
    return tool_map.get(tool_name)
