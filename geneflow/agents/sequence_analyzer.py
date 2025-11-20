import re
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class SequenceAnalyzerAgent:
    """
    Analyzes DNA/RNA sequences for basic properties, ORFs, and motifs.
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
        Main entry point for sequence analysis.
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
        Removes whitespace and newlines, converts to uppercase.
        """
        return re.sub(r"\s+", "", sequence).upper()

    def _validate_sequence(self, sequence: str) -> Tuple[bool, str]:
        """
        Checks if sequence contains only valid bases (A, T, G, C, N).
        """
        if not sequence:
            return False, "Empty sequence"
        
        invalid_chars = re.sub(r"[ATGCN]", "", sequence)
        if len(invalid_chars) > len(sequence) * 0.02: # Allow 2% noise
            return False, f"Too many invalid characters: {invalid_chars[:10]}..."
        return True, ""

    def _calculate_gc(self, sequence: str) -> float:
        """
        Computes GC percentage.
        """
        g = sequence.count("G")
        c = sequence.count("C")
        return round((g + c) / len(sequence) * 100, 2)

    def _find_orfs(self, sequence: str, min_len_aa: int = 30) -> List[Dict[str, Any]]:
        """
        Finds Open Reading Frames (ORFs).
        Currently only scans forward strand (frames 0, 1, 2).
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
        Scans for known motifs using regex.
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
