import unittest
from unittest.mock import MagicMock, patch
import json
import os

# Set dummy API key
os.environ["GEMINI_API_KEY"] = "test_key"

from src.ingestion import IngestionModule
from src.agent import AnalysisAgent

class TestPipeline(unittest.TestCase):

    def setUp(self):
        self.ingestion = IngestionModule()
        # Mock client during init to avoid real network calls
        with patch('src.agent.genai.Client') as MockClient:
            self.agent = AnalysisAgent()
            self.agent.client = MockClient.return_value

    @patch('src.ingestion.feedparser.parse')
    @patch('src.ingestion.resolve_events')
    @patch('src.ingestion.extract_facts')
    def test_pipeline_flow(self, mock_extract, mock_resolve, mock_feed):
        # 1. Mock RSS Data
        mock_feed.return_value = MagicMock(entries=[
            MagicMock(title="BTC hits 100k", link="link1", summary="Bitcoin is up.", published="now"),
            MagicMock(title="Bitcoin passes $100,000", link="link2", summary="Price surge.", published="now")
        ])

        # 2. Mock Event Resolution
        mock_resolve.return_value = [{
            "event_id": "evt1",
            "title": "Bitcoin Hits $100k",
            "articles": ["link1", "link2"]
        }]

        # 3. Mock Fact Extraction
        mock_extract.return_value = {
            "facts": [{"fact": "Price > 100k", "sources": ["WatcherGuru", "CoinDesk"]}],
            "confidence": 1.0
        }

        # Run Pipeline
        news_items = [
            {"title": "BTC hits 100k", "source": "WatcherGuru", "id": "link1", "link": "link1"},
            {"title": "Bitcoin passes $100,000", "source": "CoinDesk", "id": "link2", "link": "link2"}
        ]

        verified_events = self.ingestion.process_pipeline(news_items)

        # Assertions
        self.assertEqual(len(verified_events), 1)
        self.assertEqual(verified_events[0]['source_count'], 2)
        self.assertEqual(verified_events[0]['confidence'], 1.0)
        self.assertIn("Price > 100k", [f['fact'] for f in verified_events[0]['facts']])

    def test_agent_critic_loop(self):
        # Mock Gemini Response
        mock_response_draft = MagicMock()
        mock_response_draft.text = json.dumps({
            "tweet": "Bitcoin hits $100k! #BTC",
            "sentiment": "BULLISH",
            "reasoning": "Price up.",
            "knowledge_base_entry": "BTC > 100k",
            "hallucination_check": []
        })

        mock_response_critic = MagicMock()
        mock_response_critic.text = "PASS"

        # Mock the client attached to self.agent
        self.agent.client.models.generate_content.side_effect = [
            mock_response_draft,
            mock_response_critic
        ]

        # Mock Input
        verified_event = {
            "title": "Bitcoin Hits $100k",
            "source_count": 2,
            "sources": ["A", "B"],
            "facts": [{"fact": "Price > 100k", "sources": ["A", "B"]}],
            "items": []
        }

        # Run Agent
        result_json = self.agent.analyze_situation(verified_event, "Whale: Quiet", "History: None")
        result = json.loads(result_json)

        self.assertEqual(result['tweet'], "Bitcoin hits $100k! #BTC")
        self.assertEqual(self.agent.client.models.generate_content.call_count, 2)

if __name__ == '__main__':
    unittest.main()
