import unittest
from geneflow.agents.protein_prediction import ProteinPredictionAgent

class TestProteinPrediction(unittest.TestCase):
    def setUp(self):
        self.agent = ProteinPredictionAgent()

    def test_translate(self):
        # ATG (M) AAA (K) TAA (Stop)
        dna = "ATGAAATAA"
        aa = self.agent._translate(dna)
        self.assertEqual(aa, "MK")

    def test_properties(self):
        aa = "MK"
        props = self.agent._compute_properties(aa)
        # M (1.9) + K (-3.9) = -2.0 / 2 = -1.0
        self.assertEqual(props['hydrophobicity'], -1.0)
        self.assertEqual(props['molecular_weight'], 220.0)

    def test_signal_peptide(self):
        # Hydrophobic stretch: LLLLL
        aa_pos = "M" + "L"*10 + "K"
        self.assertTrue(self.agent._detect_signal_peptide(aa_pos))
        
        aa_neg = "M" + "K"*10
        self.assertFalse(self.agent._detect_signal_peptide(aa_neg))

if __name__ == '__main__':
    unittest.main()
