"""
Unit Tests for Agentic Workflow

Tests the complete agentic workflow including agent coordination and pipeline execution.
"""

import unittest
from src.agents.coordinator import ADKCoordinator
import os

class TestAgenticWorkflow(unittest.TestCase):
    def setUp(self):
        # Ensure we have a mock API key if not present, to avoid crash during init
        if "GOOGLE_API_KEY" not in os.environ:
            os.environ["GOOGLE_API_KEY"] = "TEST_KEY"
            
        self.coordinator = CoordinatorAgent()
        # Short sequence for speed
        self.sequence = "ATG" + "AAA" * 10 + "TATAAA" + "CCCTAA"

    def test_pipeline_structure(self):
        """
        Verifies that the pipeline runs through the steps without crashing,
        even if the LLM calls fail (due to invalid key).
        """
        results = self.coordinator.run_pipeline(self.sequence)
        
        self.assertEqual(results["status"], "Completed")
        data = results["results"]
        
        # Check that memory was populated
        self.assertIn("sequence_analysis", data)
        self.assertIn("protein_predictions", data)
        self.assertIn("literature", data)
        self.assertIn("comparison", data)
        self.assertIn("hypotheses", data)

if __name__ == '__main__':
    unittest.main()
