import os
import sys
import logging
import json
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ingestion import IngestionModule, WhaleMonitor, MarketData
from src.agent import AnalysisAgent
from src.visualizer import Visualizer

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LiveTest")

def check_env():
    load_dotenv()
    keys = [
        "GEMINI_API_KEY",
        "TWITTER_BEARER_TOKEN",
        "TWITTER_CONSUMER_KEY",
        "TWITTER_CONSUMER_SECRET",
        "TWITTER_ACCESS_TOKEN",
        "TWITTER_ACCESS_TOKEN_SECRET"
    ]
    missing = [k for k in keys if not os.getenv(k)]

    if missing:
        logger.error("❌ MISSING ENVIRONMENT VARIABLES:")
        for k in missing:
            print(f"   - {k}")
        print("\nPlease follow the instructions in SETUP.md to obtain these keys.")
        return False

    logger.info("✅ All environment variables found.")
    return True

def run_integration_test():
    if not check_env():
        return

    logger.info("🚀 Starting Live Integration Test...")

    # 1. Ingestion
    logger.info("--- Step 1: Ingestion ---")
    ingestor = IngestionModule()
    items = ingestor.fetch_news()

    if not items:
        logger.warning("⚠️ No news items fetched (Twitter might be rate limited and RSS empty?).")
        return

    target_item = items[0]
    logger.info(f"✅ Fetched Item: {target_item.get('title')}")
    logger.info(f"   Source: {target_item.get('source')}")

    # 2. Verification Data
    logger.info("--- Step 2: Verification Data ---")
    whale = WhaleMonitor()
    market = MarketData()

    symbol = "BTC" # Default for test
    whale_data = whale.get_whale_movements(symbol)
    market_info = market.get_market_status(symbol)

    logger.info(f"✅ Whale Data: {whale_data}")
    logger.info(f"✅ Market Data: {market_info}")

    # 3. AI Analysis
    logger.info("--- Step 3: AI Analysis (Gemini) ---")
    agent = AnalysisAgent()
    verification_context = f"Whale Alerts: {whale_data}\nLive Market Price: ${market_info['price']}"

    # Using dummy history for test
    history = "Date: 2023-01-01, Event: Bitcoin is volatile."

    analysis_json = agent.analyze_situation(target_item, verification_context, history)
    logger.info(f"✅ AI Response:\n{analysis_json}")

    # 4. Visualization
    logger.info("--- Step 4: Visualization (Playwright) ---")
    viz = Visualizer()
    chart_path = viz.capture_chart(symbol)

    if chart_path and os.path.exists(chart_path):
        logger.info(f"✅ Chart captured: {chart_path}")
    else:
        logger.error("❌ Failed to capture chart.")

    # 5. Publishing (Dry Run)
    logger.info("--- Step 5: Publishing (Dry Run) ---")
    logger.info("ℹ️ Skipping actual tweet posting to prevent spam during test.")
    logger.info("   To test posting, run src/publisher.py directly.")

    logger.info("\n✅ LIVE INTEGRATION TEST COMPLETE.")

if __name__ == "__main__":
    run_integration_test()
