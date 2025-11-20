import logging
import os
from typing import List, Dict, Any
from Bio.Blast import NCBIWWW, NCBIXML

logger = logging.getLogger(__name__)

class ComparisonAgent:
    """
    Compares sequences against online databases using NCBI BLAST.
    """

    def __init__(self):
        pass

    def compare(self, orfs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compares input ORFs against the database.
        """
        results = []
        for orf in orfs:
            query_seq = orf.get("sequence", "")
            if not query_seq:
                continue
            
            # Use BLAST for longer sequences, or if explicitly requested
            # For very short ones, we might skip or use a local fallback if we had one
            if len(query_seq) > 20:
                matches = self._run_blast(query_seq)
            else:
                matches = [] # Too short for meaningful BLAST

            results.append({
                "orf_id": f"ORF_{orf.get('start')}_{orf.get('end')}",
                "matches": matches
            })
        return results

    def _run_blast(self, sequence: str, program: str = "blastn", database: str = "nt", hitlist_size: int = 3) -> List[Dict[str, Any]]:
        """
        Runs NCBI BLAST over the internet.
        """
        logger.info(f"Running NCBI BLAST ({program}) for sequence length {len(sequence)}...")
        try:
            # Call NCBI BLAST API
            result_handle = NCBIWWW.qblast(program, database, sequence, hitlist_size=hitlist_size)
            
            # Parse XML results
            blast_record = NCBIXML.read(result_handle)
            
            matches = []
            for alignment in blast_record.alignments:
                for hsp in alignment.hsps:
                    matches.append({
                        "header": alignment.title,
                        "similarity": round(hsp.identities / hsp.align_length, 2),
                        "e_value": hsp.expect,
                        "alignment": f"Query: {hsp.query[:50]}... | Match: {hsp.match[:50]}..."
                    })
                    # Only take the best HSP per alignment
                    break
            
            return matches

        except Exception as e:
            logger.error(f"BLAST failed: {e}")
            return []

if __name__ == "__main__":
    agent = ComparisonAgent()
    # Test with a snippet of Insulin (short enough to be fast, long enough to hit)
    query = "ATGGCCCTGTGGATGCGCCTCCTGCCCCTGCTGGCGCTGCTGGCCCTCTGGGGACCTGACCCAGCCGCAGCCTTTGTGAACCAACACCTGTGCGGCTCACACCTGGTGGAAGCTCTCTACCTAGTGTGCGGGGAACGAGGCTTCTTCTACACACCCAAGACCCGCCGGGAGGCAGAGGACCTGCAGGTGGGGCAGGTGGAGCTGGGCGGGGGCCCTGGTGCAGGCAGCCTGCAGCCCTTGGCCCTGGAGGGGTCCCTGCAGAAGCGTGGCATTGTGGAACAATGCTGTACCAGCATCTGCTCCCTCTACCAGCTGGAGAACTACTGCAACTAG"
    print(agent.compare([{"sequence": query, "start": 1, "end": len(query)}]))
