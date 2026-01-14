
import unittest
from unittest.mock import MagicMock, patch
from src.ingestion import IngestionModule
from src.facts import extract_facts_batch

class TestFactExtraction(unittest.TestCase):
    def test_extract_facts_batch_structure(self):
        """Test that extract_facts_batch handles the structure correctly with mocks."""

        # Mock LLM response
        mock_response = {
            "event_1": {
                "facts": [{"fact": "Test Fact", "sources": ["SourceA"]}],
                "confidence": 0.5
            }
        }

        with patch('src.facts.call_llm', return_value='{"event_1": {"facts": [{"fact": "Test Fact", "sources": ["SourceA"]}], "confidence": 0.5}}'):
             result = extract_facts_batch([
                 {"event_id": "event_1", "title": "Test Event", "articles": [{"source": "SourceA", "title": "T", "summary": "S"}]}
             ])

             self.assertIn("event_1", result)
             self.assertEqual(result["event_1"]["confidence"], 0.5)

class TestIngestionBatching(unittest.TestCase):
    def test_process_pipeline_batching(self):
        """Test that process_pipeline calls extract_facts_batch and processes results."""

        ingestion = IngestionModule()

        # Mock resolve_events to return 2 events
        mock_events = [
            {"event_id": "e1", "title": "Event 1", "articles": ["a1"]},
            {"event_id": "e2", "title": "Event 2", "articles": ["a2"]}
        ]

        mock_items = [
            {"id": "a1", "title": "News 1", "source": "SourceA", "link": "l1"},
            {"id": "a2", "title": "News 2", "source": "SourceB", "link": "l2"}
        ]

        # Mock extract_facts_batch return
        mock_facts = {
            "e1": {"facts": [{"fact": "F1", "sources": ["SourceA"]}], "confidence": 1.0},
            "e2": {"facts": [{"fact": "F2", "sources": ["SourceB"]}], "confidence": 0.5}
        }

        with patch('src.ingestion.resolve_events', return_value=mock_events), \
             patch('src.ingestion.extract_facts_batch', return_value=mock_facts):

            results = ingestion.process_pipeline(mock_items)

            # Should have 2 results now (no filtering)
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]['event_id'], "e1")
            self.assertEqual(results[0]['confidence'], 1.0)

if __name__ == '__main__':
    unittest.main()
