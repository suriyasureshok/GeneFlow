import unittest
from geneflow.agents.sequence_analyzer import SequenceAnalyzerAgent

class TestSequenceAnalyzer(unittest.TestCase):
    def setUp(self):
        self.agent = SequenceAnalyzerAgent()

    def test_clean_sequence(self):
        raw = "  atg cgt \n"
        cleaned = self.agent._clean_sequence(raw)
        self.assertEqual(cleaned, "ATGCGT")

    def test_validate_sequence(self):
        valid, _ = self.agent._validate_sequence("ATGC")
        self.assertTrue(valid)
        
        invalid, msg = self.agent._validate_sequence("XYZ")
        self.assertFalse(invalid)

    def test_gc_content(self):
        # GC = 50%
        seq = "GCAT"
        self.assertEqual(self.agent._calculate_gc(seq), 50.0)

    def test_find_orfs(self):
        # ATG (Start) ... (30 AA = 90 nt) ... TAA (Stop)
        # Let's make a shorter one for testing if we can adjust min_len or just mock
        # For this test, I'll use a sequence that definitely has an ORF if I lower the threshold or make it long enough
        # Construct a 93 nt sequence: ATG + 29 codons + TAA
        # 29 codons = "AAA" * 29
        seq = "ATG" + "AAA" * 29 + "TAA"
        orfs = self.agent._find_orfs(seq, min_len_aa=10) # Lower threshold for test
        self.assertEqual(len(orfs), 1)
        self.assertEqual(orfs[0]['start'], 1)
        self.assertEqual(orfs[0]['length'], 93)

    def test_motifs(self):
        seq = "TATAAA" # TATA box
        motifs = self.agent._scan_motifs(seq)
        self.assertTrue(any(m['motif'] == 'TATA_box' for m in motifs))

if __name__ == '__main__':
    unittest.main()
