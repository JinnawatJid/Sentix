import time
import json
import logging
import schedule
import os
from src.ingestion import IngestionModule, WhaleMonitor, MarketData
from src.memory import MemoryModule
from src.agent import AnalysisAgent
from src.visualizer import Visualizer
from src.publisher import TwitterPublisher
from datetime import datetime

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SentixBot")

STATE_FILE = "state.json"

class SentixBot:
    def __init__(self):
        self.ingestion = IngestionModule()
        self.whale_monitor = WhaleMonitor()
        self.market_data = MarketData()
        self.memory = MemoryModule()
        self.agent = AnalysisAgent() # Default uses Gemini now
        self.visualizer = Visualizer()
        self.publisher = TwitterPublisher()
        self.processed_ids = self._load_state()

    def _load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_state(self):
        # Cleanup old IDs (> 24h)
        current_time = time.time()
        self.processed_ids = {k: v for k, v in self.processed_ids.items() if current_time - v < 86400}
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(self.processed_ids, f)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def run_cycle(self):
        logger.info("Starting execution cycle...")

        # 1. Fetch Data (Tries X API -> Falls back to RSS)
        items = self.ingestion.fetch_news()

        if not items:
            logger.info("No news items found this cycle.")
            return

        # Process only the freshest item that hasn't been processed
        # For simplicity in this scheduled bot, we pick the TOP 1 new item to avoid spamming.
        target_item = None
        for item in items:
            item_id = item.get('id', item.get('link'))
            if item_id not in self.processed_ids:
                target_item = item
                break

        if not target_item:
            logger.info("No new unprocessed items found.")
            return

        logger.info(f"Processing target item: {target_item.get('title', 'Unknown')[:50]}...")
        
        # 2. Extract Key Entity (Heuristic)
        text_content = f"{target_item.get('title', '')} {target_item.get('summary', '')} {target_item.get('text', '')}"
        symbol = "BTC" if "BTC" in text_content or "Bitcoin" in text_content else "ETH"
        
        # 3. Get Verification Data
        whale_data = self.whale_monitor.get_whale_movements(symbol)
        market_info = self.market_data.get_market_status(symbol)

        verification_context = f"Whale Alerts: {whale_data}\nLive Market Price: ${market_info['price']} ({market_info['change_24h']}%)"

        # 4. RAG
        history = self.memory.retrieve_context(text_content)

        # 5. AI Analysis
        logger.info("Sending to AI Agent (Gemini)...")
        analysis_json = self.agent.analyze_situation(target_item, verification_context, history)

        try:
            # Basic cleanup
            clean_json = analysis_json.replace("```json", "").replace("```", "").strip()
            result = json.loads(clean_json)
            
            logger.info(f"AI Sentiment: {result.get('sentiment')}")
            tweet_text = result.get('tweet')
            
            # 6. Generate Chart
            chart_path = self.visualizer.capture_chart(symbol)
            
            # 7. Publish to X
            success = self.publisher.post_tweet(tweet_text, chart_path)
            
            if success:
                logger.info("Successfully published to X!")
                # 8. Mark as processed
                item_id = target_item.get('id', target_item.get('link'))
                self.processed_ids[item_id] = time.time()
                self._save_state()
                
                # 9. Store in Memory
                self.memory.store_news_event(
                    text_content,
                    {
                        "source": target_item.get('source', 'Unknown'),
                        "timestamp": datetime.now().isoformat(),
                        "sentiment": result.get('sentiment', 'NEUTRAL')
                    }
                )
            else:
                logger.error("Failed to publish to X.")

        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI response: {analysis_json}")
        except Exception as e:
            logger.error(f"Error in processing loop: {e}")

def job():
    bot = SentixBot()
    bot.run_cycle()

if __name__ == "__main__":
    logger.info("Sentix Bot Initialized.")

    # Run once on startup to check systems
    job()

    # Schedule every 4 hours
    schedule.every(4).hours.do(job)

    logger.info("Scheduler started (Every 4 hours). Press Ctrl+C to exit.")
    
    while True:
        schedule.run_pending()
        time.sleep(60)
