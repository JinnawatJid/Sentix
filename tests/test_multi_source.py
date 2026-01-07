import unittest
from unittest.mock import MagicMock, patch
import logging

# Import the modules to test
from src.ingestion import IngestionModule, TwitterClient
from src.agent import AnalysisAgent

class TestMultiSourceIngestion(unittest.TestCase):

    @patch('src.ingestion.feedparser.parse')
    @patch('src.ingestion.TwitterClient.fetch_tweets')
    def test_fetch_news_aggregation(self, mock_fetch_tweets, mock_feedparser):
        """
        Verifies that fetch_news calls all sources and combines the results.
        """
        # Mock Twitter Response
        mock_fetch_tweets.side_effect = [
            [{"title": "Tweet 1", "source": "WatcherGuru", "summary": "T1"}], # WatcherGuru
            [] # CoinDesk Twitter (empty)
        ]

        # Mock RSS Response
        mock_feed = MagicMock()
        mock_entry = MagicMock()
        mock_entry.title = "RSS News 1"
        mock_entry.link = "http://rss.link"
        mock_entry.published = "2023-01-01"
        mock_entry.summary = "RSS Summary"
        mock_feed.entries = [mock_entry]
        mock_feedparser.return_value = mock_feed

        ingestor = IngestionModule()
        # Reduce sleep time for test speed
        with patch('time.sleep', return_value=None):
            all_news = ingestor.fetch_news()

        # Assertions
        print(f"\nFetched {len(all_news)} items.")
        for item in all_news:
            print(f"- {item['source']}: {item['title']}")

        # We expect:
        # 1 item from WatcherGuru
        # 1 item from EACH of the 4 RSS feeds (CoinDesk, CoinTelegraph, TheBlock, Decrypt)
        # Total = 1 + 4 = 5
        self.assertTrue(len(all_news) >= 5, f"Expected at least 5 items, got {len(all_news)}")

        sources = [item['source'] for item in all_news]
        self.assertIn("WatcherGuru", sources)
        self.assertIn("CoinDesk", sources) # From RSS
        self.assertIn("CoinTelegraph", sources)

    def test_agent_prompt_structure(self):
        """
        Verifies that the agent constructs the prompt correctly with separate candidate and context lists.
        """
        agent = AnalysisAgent()
        # Mock client to avoid API call
        agent.client = MagicMock()
        agent.client.models.generate_content.return_value.text = '{"sentiment": "NEUTRAL", "reasoning": "Test", "tweet": "Test Tweet"}'

        mock_candidates = [
            {"title": "New Event A", "source": "Source A", "summary": "Sum A"}
        ]
        mock_context = [
             {"title": "Old Event B", "source": "Source B", "summary": "Sum B"}
        ]

        # We intercept the call to generate_content to inspect the prompt
        agent.analyze_situation(mock_candidates, mock_context, "Whale Data", "History")

        call_args = agent.client.models.generate_content.call_args
        prompt_sent = call_args[1]['contents']

        print("\n--- Generated Prompt Snippet ---")
        print(prompt_sent[:500] + "...")

        self.assertIn("NEW CANDIDATE STORIES", prompt_sent)
        self.assertIn("OLDER CONTEXT STORIES", prompt_sent)
        self.assertIn("New Event A", prompt_sent)
        self.assertIn("Old Event B", prompt_sent)
        self.assertIn("Crypto-Native Persona", prompt_sent)

if __name__ == '__main__':
    unittest.main()
