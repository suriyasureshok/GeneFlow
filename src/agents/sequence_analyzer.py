"""
Sequence Analyzer Agent: DNA/RNA Sequence Analysis

Analyzes DNA/RNA sequences for basic properties, ORFs, and regulatory motifs.

Features:
    - GC content calculation
    - Open Reading Frame (ORF) detection
    - Regulatory motif scanning (TATA box, CAAT box, Kozak, etc.)
    - Sequence validation and cleaning

Usage:
    from src.agents.sequence_analyzer import SequenceAnalyzerAgent
    agent = SequenceAnalyzerAgent()
    result = agent.analyze("ATCGATCG...")
"""

import re
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class SequenceAnalyzerAgent:
    """
    DNA/RNA sequence analysis engine with regulatory motif detection.
    
    Provides comprehensive sequence analysis including GC content calculation,
    Open Reading Frame (ORF) discovery, and regulatory element identification
    using pattern matching against known motif databases.
    
    Attributes:
        motifs_db (Dict[str, str]): Regex patterns for common regulatory motifs
            - TATA_box, CAAT_box, PolyA_signal, Kozak_consensus
            - Start/Stop codons for ORF boundaries
    
    Methods:
        analyze: Main entry point for sequence analysis
        _clean_sequence: Normalize and validate sequence format
        _validate_sequence: Check sequence composition
        _calculate_gc: Compute GC content percentage
        _find_orfs: Detect open reading frames
        _scan_motifs: Identify regulatory elements
    
    Example:
        >>> agent = SequenceAnalyzerAgent()
        >>> result = agent.analyze("ATGAAATAAGCG...")
        >>> print(f"GC%: {result['gc_percent']}%, ORFs: {len(result['orfs'])}")
    """

    def __init__(self):
        # Simple regex motifs for demonstration
        self.motifs_db = {
            "TATA_box": r"TATA[AT]A",
            "CAAT_box": r"CAAT",
            "PolyA_signal": r"AATAAA",
            "Kozak_consensus": r"[AG]CCATGG",
            "Start_codon": r"ATG",
            "Stop_codon": r"TAA|TAG|TGA"
        }

    def analyze(self, sequence: str) -> Dict[str, Any]:
        """
        Performs comprehensive DNA/RNA sequence analysis.
        
        Args:
            sequence: DNA or RNA sequence string (case insensitive, whitespace allowed)
        
        Returns:
            Dict containing:
                - valid (bool): Whether sequence passed validation
                - sequence_type (str): "DNA" or "RNA"
                - length (int): Sequence length in bases
                - gc_percent (float): GC content percentage
                - orfs (List[Dict]): Detected open reading frames
                - motifs (List[Dict]): Detected regulatory motifs
                - cleaned_sequence (str): Cleaned uppercase sequence
                - error (str, optional): Error message if invalid
        
        Example:
            >>> agent = SequenceAnalyzerAgent()
            >>> result = agent.analyze("ATGAAATAA")
            >>> print(result['gc_percent'])
        """
        cleaned_seq = self._clean_sequence(sequence)
        valid, error = self._validate_sequence(cleaned_seq)
        
        if not valid:
            return {"valid": False, "error": error, "sequence_id": "unknown"}

        gc_percent = self._calculate_gc(cleaned_seq)
        orfs = self._find_orfs(cleaned_seq)
        motifs = self._scan_motifs(cleaned_seq)

        return {
            "valid": True,
            "sequence_type": "DNA", # Assuming DNA for now
            "length": len(cleaned_seq),
            "gc_percent": gc_percent,
            "orfs": orfs,
            "motifs": motifs,
            "cleaned_sequence": cleaned_seq
        }

    def _clean_sequence(self, sequence: str) -> str:
        """
        Cleans sequence by removing whitespace and converting to uppercase.
        
        Args:
            sequence: Raw sequence string
        
        Returns:
            Cleaned uppercase sequence string
        """
        return re.sub(r"\s+", "", sequence).upper()

    def _validate_sequence(self, sequence: str) -> Tuple[bool, str]:
        """
        Validates sequence contains only valid nucleotide characters.
        
        Allows up to 2% invalid characters (noise tolerance).
        Valid characters: A, T, G, C, N
        
        Args:
            sequence: Sequence string to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not sequence:
            return False, "Empty sequence"
        
        invalid_chars = re.sub(r"[ATGCN]", "", sequence)
        if len(invalid_chars) > len(sequence) * 0.02: # Allow 2% noise
            return False, f"Too many invalid characters: {invalid_chars[:10]}..."
        return True, ""

    def _calculate_gc(self, sequence: str) -> float:
        """
        Calculates GC content percentage.
        
        GC content = (count of G + count of C) / total length * 100
        
        Args:
            sequence: DNA sequence string
        
        Returns:
            GC percentage rounded to 2 decimal places
        """
        g = sequence.count("G")
        c = sequence.count("C")
        return round((g + c) / len(sequence) * 100, 2)

    def _find_orfs(self, sequence: str, min_len_aa: int = 30) -> List[Dict[str, Any]]:
        """
        Identifies Open Reading Frames (ORFs) in the sequence.
        
        Scans forward strand in all three reading frames (0, 1, 2) for
        start codons (ATG) followed by in-frame stop codons (TAA, TAG, TGA).
        
        Args:
            sequence: DNA sequence string
            min_len_aa: Minimum ORF length in amino acids (default: 30)
        
        Returns:
            List of ORF dictionaries containing:
                - start (int): 1-based start position
                - end (int): 1-based end position (inclusive)
                - frame (int): Reading frame (1, 2, or 3)
                - length (int): Length in nucleotides
                - sequence (str): ORF sequence including start/stop codons
        """
        orfs = []
        seq_len = len(sequence)
        min_len_nt = min_len_aa * 3

        # Standard genetic code start/stop
        start_codon = "ATG"
        stop_codons = {"TAA", "TAG", "TGA"}

        for frame in range(3):
            # Iterate through codons in this frame
            for i in range(frame, seq_len - 2, 3):
                codon = sequence[i:i+3]
                if codon == start_codon:
                    # Found start, look for stop
                    for j in range(i + 3, seq_len - 2, 3):
                        stop_codon = sequence[j:j+3]
                        if stop_codon in stop_codons:
                            # Found ORF
                            orf_len = j + 3 - i
                            if orf_len >= min_len_nt:
                                orfs.append({
                                    "start": i + 1, # 1-based index
                                    "end": j + 3,
                                    "frame": frame + 1,
                                    "length": orf_len,
                                    "sequence": sequence[i:j+3]
                                })
                            break # Move to next start codon search
        return orfs

    def _scan_motifs(self, sequence: str) -> List[Dict[str, Any]]:
        """
        Scans sequence for known regulatory motifs using regex patterns.
        
        Detected motifs include:
            - TATA box: TATA[AT]A
            - CAAT box: CAAT
            - Poly-A signal: AATAAA
            - Kozak consensus: [AG]CCATGG
            - Start/Stop codons
        
        Args:
            sequence: DNA sequence string
        
        Returns:
            List of motif dictionaries containing:
                - motif (str): Motif name
                - position (int): 1-based start position
                - match_sequence (str): Actual matched sequence
        """
        found_motifs = []
        for name, pattern in self.motifs_db.items():
            for match in re.finditer(pattern, sequence):
                found_motifs.append({
                    "motif": name,
                    "position": match.start() + 1, # 1-based
                    "match_sequence": match.group()
                })
        return found_motifs

if __name__ == "__main__":
    # Test
    agent = SequenceAnalyzerAgent()
    seq = "ATGAAATATAAAGCGTACGTGCTTGAATGCC" # Too short for default ORF but good for motif
    print(agent.analyze(seq))
