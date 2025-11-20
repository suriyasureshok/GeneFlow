import unittest
from geneflow.agents.coordinator import ADKCoordinator

class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        self.coordinator = ADKCoordinator()
        # Sample sequence with TATA box and Start/Stop codons
        self.sequence = "ATG" + "AAA" * 30 + "TATAAA" + "CCCTAA"

    def test_pipeline_run(self):
        results = self.coordinator.run_pipeline(self.sequence)
        
        self.assertEqual(results["status"], "Completed")
        self.assertIsNone(results["error"])
        
        data = results["results"]
        
        # Check Sequence Analysis
        self.assertTrue(data["sequence_analysis"]["valid"])
        self.assertGreater(len(data["sequence_analysis"]["orfs"]), 0)
        self.assertTrue(any(m['motif'] == 'TATA_box' for m in data["sequence_analysis"]["motifs"]))
        
        # Check Protein Prediction
        self.assertGreater(len(data["protein_predictions"]), 0)
        self.assertIn("molecular_weight", data["protein_predictions"][0]["properties"])
        
        # Check Literature
        self.assertIsInstance(data["literature"], list)
        
        # Check Comparison
        self.assertIsInstance(data["comparison"], list)
        
        # Check Hypotheses
        self.assertIsInstance(data["hypotheses"], list)
        self.assertGreater(len(data["hypotheses"]), 0)

if __name__ == '__main__':
    unittest.main()
