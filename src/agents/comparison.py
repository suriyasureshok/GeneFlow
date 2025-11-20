"""
Comparison Agent: Sequence Comparison and BLAST

Compares DNA sequences against NCBI databases using BLAST to find homologous sequences.

Features:
    - NCBI BLAST integration (blastn, blastp, blastx)
    - Homology search and alignment
    - Match scoring and identity calculation

Usage:
    from src.agents.comparison import ComparisonAgent
    agent = ComparisonAgent()
    results = agent.compare(orf_list)

Note: Requires internet connection for NCBI BLAST API
"""

import logging
import os
from typing import List, Dict, Any
from Bio.Blast import NCBIWWW, NCBIXML

logger = logging.getLogger(__name__)

class ComparisonAgent:
    """
    NCBI BLAST sequence homology search engine.
    
    Compares DNA sequences against NCBI databases to identify homologous sequences,
    evolutionary relationships, and functional annotations. Uses QBLAST web API
    for unrestricted access to current databases.
    
    Methods:
        compare: Main entry point for multiple ORF comparison
        _run_blast: Executes NCBI BLAST web query
    
    Note:
        Requires internet connection for NCBI API access.
        Large sequences may take 1-2 minutes for analysis.
    
    Example:
        >>> agent = ComparisonAgent()
        >>> orfs = [{"sequence": "ATGCGTACG...", "start": 1, "end": 100}]
        >>> results = agent.compare(orfs)
    """

    def __init__(self):
        pass

    def compare(self, orfs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compares multiple ORFs against NCBI database.
        
        Skips sequences shorter than 20bp as they yield poor BLAST results.
        
        Args:
            orfs: List of ORF dictionaries with 'sequence', 'start', 'end' keys
        
        Returns:
            List of result dictionaries containing:
                - orf_id (str): ORF identifier
                - matches (List[Dict]): BLAST hits with similarity scores
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
        Executes NCBI BLAST search via QBLAST web API.
        
        Args:
            sequence: Query DNA sequence
            program: BLAST program (blastn, blastp, blastx, etc.)
            database: NCBI database to search (nt, nr, etc.)
            hitlist_size: Maximum number of hits to return
        
        Returns:
            List of match dictionaries containing:
                - header (str): Hit description
                - similarity (float): Identity percentage (0-1)
                - e_value (float): Expect value
                - alignment (str): Alignment preview
            
            Returns empty list on error or no hits
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
