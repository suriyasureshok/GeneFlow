import unittest
from geneflow.agents.literature import LiteratureAgent

class TestLiteratureAgent(unittest.TestCase):
    def setUp(self):
        self.agent = LiteratureAgent(offline_mode=True)

    def test_search_offline(self):
        results = self.agent.search(["TATA"])
        self.assertTrue(len(results) > 0)
        self.assertIn("TATA", results[0]['title'])
        self.assertIn("summary", results[0])

    def test_search_no_match(self):
        results = self.agent.search(["Xylophone"])
        self.assertEqual(len(results), 0)

if __name__ == '__main__':
    unittest.main()
