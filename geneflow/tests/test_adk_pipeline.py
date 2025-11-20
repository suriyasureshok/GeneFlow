import unittest
import os
from geneflow.agents.coordinator import ADKCoordinator

class TestADKPipeline(unittest.TestCase):
    def setUp(self):
        if "GOOGLE_API_KEY" not in os.environ:
            os.environ["GOOGLE_API_KEY"] = "TEST_KEY"

    def test_agent_initialization(self):
        """
        Verifies that the ADK agent can be initialized with tools.
        """
        try:
            coordinator = ADKCoordinator()
            self.assertIsNotNone(coordinator)
            self.assertIsNotNone(coordinator.agent)
            self.assertEqual(coordinator.agent.name, "geneflow_coordinator")
            self.assertTrue(len(coordinator.agent.tools) > 0)
        except Exception as e:
            self.fail(f"Agent initialization failed: {e}")

if __name__ == '__main__':
    unittest.main()
