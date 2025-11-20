import unittest
from geneflow.agents.hypothesis import HypothesisAgent

class TestHypothesisAgent(unittest.TestCase):
    def setUp(self):
        self.agent = HypothesisAgent()

    def test_generate_hypothesis(self):
        data = {
            "sequence_analysis": {"motifs": [{"motif": "TATA_box"}]},
            "protein_predictions": [{"signal_peptide": True}],
            "comparison": [{"matches": [{"header": "Insulin"}]}]
        }
        hypotheses = self.agent.generate(data)
        
        self.assertTrue(len(hypotheses) >= 3)
        self.assertTrue(any("promoter" in h['hypothesis'] for h in hypotheses))
        self.assertTrue(any("secreted" in h['hypothesis'] for h in hypotheses))
        self.assertTrue(any("Insulin" in h['hypothesis'] for h in hypotheses))

    def test_no_hypothesis(self):
        data = {}
        hypotheses = self.agent.generate(data)
        self.assertEqual(len(hypotheses), 1)
        self.assertIn("unclear", hypotheses[0]['hypothesis'])

if __name__ == '__main__':
    unittest.main()
