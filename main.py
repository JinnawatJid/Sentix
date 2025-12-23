import time
import json
import logging
from src.ingestion import IngestionModule, TwitterScraper, WhaleMonitor, MarketData
from src.memory import MemoryModule
from src.agent import AnalysisAgent
from src.visualizer import Visualizer
from datetime import datetime
import time

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SentixBot")

class SentixBot:
    def __init__(self):
        self.ingestion = IngestionModule()
        self.twitter_source = TwitterScraper()
        self.whale_monitor = WhaleMonitor()
        self.market_data = MarketData()
        self.memory = MemoryModule()
        self.agent = AnalysisAgent(model_name="gemma3")
        self.visualizer = Visualizer()
        self.processed_ids = {} # Dictionary mapping ID -> processing timestamp

    def run_cycle(self):
        logger.info("Starting execution cycle...")

        # Cleanup old processed IDs (> 60 mins) to keep memory low and allow re-processing if needed (though IDs are unique usually)
        current_time = time.time()
        self.processed_ids = {k: v for k, v in self.processed_ids.items() if current_time - v < 3600}

        # 1. Fetch Data
        news_items = self.ingestion.fetch_coindesk_news()
        tweets = self.twitter_source.fetch_tweets()
        
        # Combine sources
        all_inputs = news_items + tweets
        
        for item in all_inputs:
            # unique ID generation
            item_id = item.get('id', item.get('link'))
            
            # Deduplication: Check if ID processed in last 60 mins
            if item_id in self.processed_ids:
                continue
            
            logger.info(f"Processing new item: {item.get('title', item.get('text'))[:50]}...")
            
            # 2. Extract Key Entity (Simple heuristic: look for BTC/ETH mentioned)
            text_content = f"{item.get('title', '')} {item.get('summary', '')} {item.get('text', '')}"
            symbol = "BTC" if "BTC" in text_content or "Bitcoin" in text_content else "ETH"
            
            # 3. Get Verification Data (Whale + Market)
            whale_data = self.whale_monitor.get_whale_movements(symbol)
            market_info = self.market_data.get_market_status(symbol)
            
            logger.info(f"Whale Data: {whale_data}")
            logger.info(f"Market Data: {market_info}")
            
            verification_context = f"Whale Alerts: {whale_data}\nLive Market Price: ${market_info['price']} ({market_info['change_24h']}%)"
            
            # 4. RAG: Retrieve History
            history = self.memory.retrieve_context(text_content)
            logger.info(f"Retrieved {len(history.splitlines())} historical context items.")
            
            # 5. AI Analysis
            logger.info("Sending to AI Agent...")
            analysis_json = self.agent.analyze_situation(item, verification_context, history)
            
            # Parse AI response
            try:
                # Basic cleanup if the LLM adds markdown blocks
                clean_json = analysis_json.replace("```json", "").replace("```", "").strip()
                result = json.loads(clean_json)
                
                logger.info(f"AI Sentiment: {result.get('sentiment')}")
                logger.info(f"Generated Tweet: {result.get('tweet')}")
                
                # 6. Generate Chart
                chart_path = self.visualizer.capture_chart(symbol)
                logger.info(f"Chart generated at: {chart_path}")
                
                # 7. "Publish" (Mock)
                self.publish(result, chart_path)
                
                # 8. Store in Memory for future cycles
                self.memory.store_news_event(
                    text_content,
                    {
                        "source": item.get('source', item.get('user', 'Unknown')),
                        "timestamp": datetime.now().isoformat(),
                        "sentiment": result.get('sentiment', 'NEUTRAL')
                    }
                )
                
                self.processed_ids[item_id] = time.time()
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse AI response: {analysis_json}")
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")

    def publish(self, result, image_path):
        """Simulates publishing to Twitter."""
        print("\n" + "="*50)
        print("📢 MOCK PUBLISHING TO X (TWITTER)")
        print(f"TEXT: {result.get('tweet')}")
        print(f"IMAGE ATTACHMENT: {image_path}")
        print("="*50 + "\n")

if __name__ == "__main__":
    bot = SentixBot()
    # Run one cycle immediately
    bot.run_cycle()
    
    # In a real deployment, you might loop:
    # while True:
    #     bot.run_cycle()
    #     time.sleep(300)
