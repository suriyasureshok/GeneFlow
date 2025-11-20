"""
PDF Report Generator for GeneFlow

Generates comprehensive PDF reports combining sequence analysis, visualizations,
literature review, and research hypotheses.

Features:
    - Professional PDF formatting
    - Embedded plots and images
    - Multi-section reports (Analysis, Structure, Literature, Hypotheses)
    - Automatic pagination

Usage:
    from src.utils.reporter import create_pdf
    
    report_data = {
        "sequence_analysis": {...},
        "structure_image": "path/to/image.png",
        "literature": {...},
        "hypotheses": [...]
    }
    pdf_path = create_pdf(report_data, "plots_dir", "output.pdf")
"""

from fpdf import FPDF
import os
from typing import Dict, Any

class ReportGenerator(FPDF):
    """
    Custom FPDF-based generator for professional research reports.
    
    Extends FPDF with specialized methods for bioinformatics report creation
    including headers, footers, chapter formatting, and image embedding.
    
    Methods:
        header: Adds page header (called automatically per page)
        footer: Adds page number footer (called automatically per page)
        chapter_title: Formats and displays section headings
        chapter_body: Renders formatted multi-line paragraph text
        add_image_section: Embeds titled images with validation
    """
    
    def header(self):
        """
        Renders page header with title (called automatically by FPDF).
        
        Displays "GeneFlow Research Report" at the top of each page
        with professional formatting.
        """
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'GeneFlow Research Report', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        """
        Renders page footer with page number (called automatically by FPDF).
        
        Displays current page number at bottom center of each page.
        """
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        """
        Formats and displays styled chapter/section title.
        
        Renders title with light blue background for visual distinction.
        
        Args:
            title (str): Chapter title text
        """
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, title, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        """
        Renders formatted multi-line chapter body text.
        
        Args:
            body (str): Chapter body text with automatic line wrapping
        """
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 5, body)
        self.ln()

    def add_image_section(self, title, image_path, w=150):
        """
        Embeds titled image section in report with validation.
        
        Checks for file existence before embedding to prevent errors.
        
        Args:
            title (str): Section title for the image
            image_path (str): File path to image (PNG, JPG, etc.)
            w (int, optional): Image width in mm. Default: 150
        """
        if image_path and os.path.exists(image_path):
            self.chapter_title(title)
            self.image(image_path, x=30, w=w)
            self.ln(5)

def create_pdf(data: Dict[str, Any], plots_dir: str, output_path: str = "report.pdf") -> str:
    """
    Generates comprehensive multi-section PDF research report.
    
    Creates professional report combining sequence analysis summary, GC content
    visualization, 3D structure image, literature review, and hypotheses.
    
    Args:
        data (Dict[str, Any]): Complete analysis data containing:
            - sequence_analysis (Dict): From analyze_sequence()
            - sequence_length (int): Sequence length in bp
            - structure_image (str, optional): Path to 3D structure PNG
            - literature (Dict or str): Literature findings
            - hypotheses (List[Dict]): Generated hypotheses
        plots_dir (str): Directory containing generated plots
        output_path (str, optional): Output PDF filename. Default: "report.pdf"
        
    Returns:
        str: Path to generated PDF file or None on error
    
    Report Sections:
        1. Sequence Analysis: Length, GC%, ORF count
        2. GC Content Plot: Distribution visualization
        3. DNA Structure: 3D helix visualization
        4. Literature Review: Key papers summary
        5. Hypotheses: Generated research hypotheses with evidence
    
    Example:
        >>> data = {"sequence_analysis": {...}, "hypotheses": [...]}
        >>> pdf_path = create_pdf(data, "plots", "report.pdf")
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    pdf = ReportGenerator()
    pdf.add_page()
    
    # 1. Sequence Summary
    pdf.chapter_title("1. Sequence Analysis")
    seq_analysis = data.get("sequence_analysis", {})
    seq_len = data.get("sequence_length", "N/A")
    
    summary = f"""
    Sequence Length: {seq_len} bp
    GC Content: {seq_analysis.get('gc_percent', 'N/A')}%
    ORFs Found: {len(seq_analysis.get('orfs', []))}
    """
    pdf.chapter_body(summary)
    
    # Add GC Plot
    pdf.add_image_section("GC Content Distribution", os.path.join(plots_dir, "gc_plot.png"))
    
    # 2. 3D Structure
    struct_img = data.get("structure_image")
    if struct_img:
        pdf.add_image_section("2. 3D DNA Structure Model", struct_img)
    
    # 3. Literature Review
    pdf.chapter_title("3. Literature Review")
    lit = data.get("literature", "No literature review available.")
    if isinstance(lit, dict):
        # If it's a dict (from JSON parsing), convert to string summary
        lit_text = "Key papers found:\n"
        for paper in lit.get('papers', []):
            lit_text += f"- {paper.get('title')} ({paper.get('authors')})\n"
        pdf.chapter_body(lit_text)
    else:
        pdf.chapter_body(str(lit)[:2000]) # Truncate if too long to avoid overflow issues
    
    # 4. Research Hypotheses
    pdf.chapter_title("4. Research Hypotheses")
    hyps = data.get("hypotheses", [])
    
    if isinstance(hyps, list):
        for i, h in enumerate(hyps):
            if isinstance(h, dict):
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(0, 5, f"Hypothesis {i+1} ({h.get('confidence', 'N/A')} Confidence)", 0, 1)
                pdf.set_font('Arial', '', 11)
                pdf.multi_cell(0, 5, h.get('hypothesis', ''))
                pdf.ln(2)
                pdf.set_font('Arial', 'I', 10)
                pdf.multi_cell(0, 5, f"Rationale: {h.get('rationale', '')}")
                pdf.ln(5)
    elif isinstance(hyps, str):
        pdf.chapter_body(hyps)
        
    try:
        pdf.output(output_path)
        return output_path
    except Exception as e:
        print(f"Error saving PDF: {e}")
        return None
