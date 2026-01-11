import os
import sys
import logging
import json
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock external dependencies BEFORE importing modules that use them
sys.modules['tweepy'] = MagicMock()
# sys.modules['google.genai'] = MagicMock() # We don't mock the whole module to allow imports
sys.modules['chromadb'] = MagicMock()
sys.modules['playwright.sync_api'] = MagicMock()

# Now import the modules
from src.ingestion import IngestionModule
from src.agent import AnalysisAgent

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DryRunTest")

def run_dry_run():
    logger.info("🚀 Starting Dry Run (Mocked) Test...")

    # 1. Mock Ingestion
    logger.info("--- Step 1: Mock Ingestion ---")

    # Patch the methods inside the classes
    with patch('src.ingestion.TwitterClient.fetch_tweets') as mock_fetch:
        mock_fetch.return_value = [{
            "title": "Mock Tweet",
            "text": "Bitcoin is pumping! #BTC",
            "summary": "Bitcoin is pumping! #BTC",
            "source": "@WatcherGuru",
            "id": "12345",
            "link": "http://twitter.com/12345"
        }]

        ingestor = IngestionModule()
        items = ingestor.fetch_news()

        if items:
            logger.info(f"✅ Fetched Mock Item: {items[0]['title']}")
        else:
            logger.error("❌ Failed to fetch mock items.")

    # 2. Mock AI Analysis
    logger.info("--- Step 2: Mock AI Analysis ---")

    # Mock the Client class in src.agent.genai
    with patch('src.agent.genai.Client') as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "sentiment": "BULLISH",
            "reasoning": "Mock reasoning.",
            "tweet": "Bitcoin to the moon! 🚀 #BTC"
        })

        # Mock client.models.generate_content
        mock_client.models.generate_content.return_value = mock_response

        agent = AnalysisAgent()
        # Ensure client is set (AnalysisAgent sets it in __init__ if env var exists, but we want to force our mock)
        agent.client = mock_client

        result = agent.analyze_situation(
            {"title": "Mock News"},
            "Whale Data: None",
            "History: None"
        )

        logger.info(f"✅ Mock AI Response: {result}")

    logger.info("\n✅ DRY RUN TEST COMPLETE (Logic Verified).")

if __name__ == "__main__":
    run_dry_run()
