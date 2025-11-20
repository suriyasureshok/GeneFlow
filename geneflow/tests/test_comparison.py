import unittest
import os
from geneflow.agents.comparison import ComparisonAgent

class TestComparisonAgent(unittest.TestCase):
    def setUp(self):
        # Ensure we use the correct path relative to where test is run
        # Assuming running from root
        self.db_path = "geneflow/data/known_sequences.fasta"
        self.agent = ComparisonAgent(db_path=self.db_path)

    def test_load_db(self):
        self.assertTrue(len(self.agent.db) > 0)
        self.assertIn("Insulin", self.agent.db[1]['header'])

    def test_jaccard(self):
        s1 = "ATGCGT"
        s2 = "ATGCGT"
        self.assertEqual(self.agent._jaccard_similarity(s1, s2, k=3), 1.0)
        
        s3 = "AAAAAA"
        self.assertEqual(self.agent._jaccard_similarity(s1, s3, k=3), 0.0)

    def test_compare(self):
        # Use Insulin sequence
        insulin_seq = self.agent.db[1]['sequence']
        res = self.agent.compare([{"sequence": insulin_seq, "start": 1, "end": 100}])
        
        self.assertTrue(len(res) > 0)
        top_match = res[0]['matches'][0]
        self.assertIn("Insulin", top_match['header'])
        self.assertAlmostEqual(top_match['similarity'], 1.0)

if __name__ == '__main__':
    unittest.main()
