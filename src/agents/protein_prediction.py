"""
Protein Prediction Agent: Protein Property Analysis

Predicts protein properties from DNA ORF sequences including amino acid translation,
molecular weight, hydrophobicity, and signal peptide detection.

Features:
    - DNA to protein translation using codon table
    - Molecular weight calculation
    - Hydrophobicity analysis (Kyte-Doolittle scale)
    - Signal peptide detection

Usage:
    from src.agents.protein_prediction import ProteinPredictionAgent
    agent = ProteinPredictionAgent()
    result = agent.predict(orf_dict)
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ProteinPredictionAgent:
    """
    Protein property prediction from DNA sequences using translation and analysis.
    
    Translates DNA ORF sequences to amino acids using the standard genetic code,
    then computes molecular weight, hydrophobicity, and signal peptide presence.
    Provides physicochemical properties useful for functional annotation.
    
    Attributes:
        codon_table (Dict[str, str]): Standard genetic code (61 codons + 3 stops)
        hydrophobicity_scale (Dict[str, float]): Kyte-Doolittle scale (-4.5 to +4.5)
    
    Methods:
        predict: Main prediction entry point  
        _translate: DNA to amino acid conversion
        _compute_properties: Calculate MW and hydrophobicity
        _detect_signal_peptide: Identify N-terminal signal sequences
    
    Example:
        >>> agent = ProteinPredictionAgent()
        >>> orf = {"sequence": "ATGAAATAAGCG...", "start": 1, "end": 100}
        >>> result = agent.predict(orf)
        >>> print(f"Protein length: {result['length']} aa")
    """

    def __init__(self):
        self.codon_table = {
            'ATA':'I', 'ATC':'I', 'ATT':'I', 'ATG':'M',
            'ACA':'T', 'ACC':'T', 'ACG':'T', 'ACT':'T',
            'AAC':'N', 'AAT':'N', 'AAA':'K', 'AAG':'K',
            'AGC':'S', 'AGT':'S', 'AGA':'R', 'AGG':'R',
            'CTA':'L', 'CTC':'L', 'CTG':'L', 'CTT':'L',
            'CCA':'P', 'CCC':'P', 'CCG':'P', 'CCT':'P',
            'CAC':'H', 'CAT':'H', 'CAA':'Q', 'CAG':'Q',
            'CGA':'R', 'CGC':'R', 'CGG':'R', 'CGT':'R',
            'GTA':'V', 'GTC':'V', 'GTG':'V', 'GTT':'V',
            'GCA':'A', 'GCC':'A', 'GCG':'A', 'GCT':'A',
            'GAC':'D', 'GAT':'D', 'GAA':'E', 'GAG':'E',
            'GGA':'G', 'GGC':'G', 'GGG':'G', 'GGT':'G',
            'TCA':'S', 'TCC':'S', 'TCG':'S', 'TCT':'S',
            'TTC':'F', 'TTT':'F', 'TTA':'L', 'TTG':'L',
            'TAC':'Y', 'TAT':'Y', 'TAA':'_', 'TAG':'_',
            'TGC':'C', 'TGT':'C', 'TGA':'_', 'TGG':'W',
        }
        
        # Kyte-Doolittle hydrophobicity scale
        self.hydrophobicity_scale = {
            'A': 1.8, 'R':-4.5, 'N':-3.5, 'D':-3.5, 'C': 2.5,
            'Q':-3.5, 'E':-3.5, 'G':-0.4, 'H':-3.2, 'I': 4.5,
            'L': 3.8, 'K':-3.9, 'M': 1.9, 'F': 2.8, 'P':-1.6,
            'S':-0.8, 'T':-0.7, 'W':-0.9, 'Y':-1.3, 'V': 4.2
        }

    def predict(self, orf: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predicts protein properties from an ORF dictionary.
        
        Args:
            orf: Dictionary containing:
                - sequence (str): DNA sequence
                - start (int): Start position
                - end (int): End position
        
        Returns:
            Dictionary containing:
                - orf_id (str): Identifier (ORF_start_end)
                - aa_sequence (str): Translated amino acid sequence
                - length (int): Protein length in amino acids
                - properties (Dict): Molecular weight and hydrophobicity
                - signal_peptide (bool): Signal peptide detection result
                - error (str, optional): Error message if sequence missing
        """
        dna_seq = orf.get("sequence", "")
        if not dna_seq:
            return {"error": "No sequence provided"}

        aa_seq = self._translate(dna_seq)
        properties = self._compute_properties(aa_seq)
        signal_peptide = self._detect_signal_peptide(aa_seq)

        return {
            "orf_id": f"ORF_{orf.get('start')}_{orf.get('end')}",
            "aa_sequence": aa_seq,
            "length": len(aa_seq),
            "properties": properties,
            "signal_peptide": signal_peptide
        }

    def _translate(self, dna_seq: str) -> str:
        """
        Translates DNA sequence to amino acid sequence using standard genetic code.
        
        Translation stops at first stop codon (TAA, TAG, TGA).
        Unknown codons are translated to 'X'.
        
        Args:
            dna_seq: DNA sequence (must be multiple of 3)
        
        Returns:
            Amino acid sequence string
        """
        protein = []
        if len(dna_seq) % 3 == 0:
            for i in range(0, len(dna_seq), 3):
                codon = dna_seq[i:i+3]
                aa = self.codon_table.get(codon, 'X')
                if aa == '_': # Stop codon
                    break
                protein.append(aa)
        return "".join(protein)

    def _compute_properties(self, aa_seq: str) -> Dict[str, float]:
        """
        Calculates basic physicochemical properties of the protein.
        
        Molecular weight: Approximated as 110 Da per amino acid
        Hydrophobicity: Average Kyte-Doolittle score
        
        Args:
            aa_seq: Amino acid sequence string
        
        Returns:
            Dictionary with molecular_weight and hydrophobicity values
        """
        if not aa_seq:
            return {"molecular_weight": 0, "hydrophobicity": 0}

        # Simple MW approximation (average ~110 Da per AA)
        mw = len(aa_seq) * 110.0
        
        # Average Hydrophobicity
        hyd_sum = sum(self.hydrophobicity_scale.get(aa, 0) for aa in aa_seq)
        avg_hyd = round(hyd_sum / len(aa_seq), 2)

        return {
            "molecular_weight": mw,
            "hydrophobicity": avg_hyd
        }

    def _detect_signal_peptide(self, aa_seq: str) -> bool:
        """
        Detects potential signal peptide using heuristic approach.
        
        Checks for hydrophobic stretch in N-terminal region (first 30 AA).
        A stretch of 5+ consecutive hydrophobic residues (A, L, I, V, F, M)
        indicates potential signal peptide.
        
        Args:
            aa_seq: Amino acid sequence string
        
        Returns:
            True if signal peptide likely present, False otherwise
        """
        if len(aa_seq) < 20:
            return False
        
        n_term = aa_seq[:30]
        # Look for a stretch of 5+ hydrophobic residues (A, L, I, V, F, M)
        hydrophobic_residues = set("ALIVFM")
        streak = 0
        for aa in n_term:
            if aa in hydrophobic_residues:
                streak += 1
                if streak >= 5:
                    return True
            else:
                streak = 0
        return False

if __name__ == "__main__":
    agent = ProteinPredictionAgent()
    # Test translation
    print(agent.predict({"sequence": "ATGAAATATAAAGCGTACGTGCTTGAATGCC", "start": 1, "end": 33}))
