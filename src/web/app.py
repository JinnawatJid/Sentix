from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging
import threading
import time
import schedule
import uvicorn
import os
import json
import re

from src.database import get_db, engine, Base
from src.models import ProcessedNews, BotLog, TweetEngagement, DecisionTrace
# Import the main bot logic (We will refactor main.py to be importable or import classes directly)
from src.ingestion import IngestionModule, WhaleMonitor, MarketData
from src.memory import MemoryModule
from src.agent import AnalysisAgent
from src.visualizer import Visualizer
from src.publisher import TwitterPublisher
from src.logging_handlers import DBHandler # Import custom handler
from datetime import datetime

# Initialize DB
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sentix Bot Dashboard")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates = Jinja2Templates(directory="src/web/templates")

# Configure Root Logger to use DBHandler
logging.basicConfig(level=logging.INFO)
root_logger = logging.getLogger()
# Avoid adding duplicates if reloaded
if not any(isinstance(h, DBHandler) for h in root_logger.handlers):
    root_logger.addHandler(DBHandler())

logger = logging.getLogger("WebDashboard")

# --- BOT INSTANCE ---
class BotController:
    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        self.last_run_status = "Idle"
        self.next_run = None

        # Bot Components
        self.ingestion = IngestionModule()
        self.whale_monitor = WhaleMonitor()
        self.market_data = MarketData()
        self.memory = MemoryModule()
        self.agent = AnalysisAgent()
        self.visualizer = Visualizer()
        self.publisher = TwitterPublisher()

    def _extract_symbol(self, text):
        """
        Extracts crypto symbol from text using a mapping list.
        Defaults to BTC if no known symbol is found.
        """
        text = text.lower()

        # Priority mapping (Title Keywords -> Ticker)
        # Order matters: longer phrases first to avoid partial matches (e.g. "classic" vs "ethereum classic")
        mapping = {
            "bitcoin cash": "BCH",
            "bitcoin": "BTC",
            "btc": "BTC",
            "ethereum classic": "ETC",
            "ethereum": "ETH",
            "ether": "ETH",
            "eth": "ETH",
            "solana": "SOL",
            "sol": "SOL",
            "ripple": "XRP",
            "xrp": "XRP",
            "cardano": "ADA",
            "ada": "ADA",
            "dogecoin": "DOGE",
            "doge": "DOGE",
            "polkadot": "DOT",
            "dot": "DOT",
            "matic": "MATIC",
            "polygon": "MATIC",
            "litecoin": "LTC",
            "ltc": "LTC",
            "tron": "TRX",
            "avalanche": "AVAX",
            "avax": "AVAX",
            "shiba inu": "SHIB",
            "shib": "SHIB",
            "uniswap": "UNI",
            "uni": "UNI",
            "wrapped bitcoin": "WBTC",
            "chainlink": "LINK",
            "link": "LINK",
            "cosmos": "ATOM",
            "atom": "ATOM",
            "monero": "XMR",
            "filecoin": "FIL",
            "aptos": "APT",
            "lido": "LDO",
            "arbitrum": "ARB",
            "near protocol": "NEAR",
            "near": "NEAR",
            "quant": "QNT",
            "vechain": "VET",
            "sui": "SUI"
        }

        # Find the earliest match in the text
        best_match_ticker = None
        min_index = len(text)

        for key, ticker in mapping.items():
            # Check for word boundaries to avoid matching "eth" in "something"
            pattern = r'(^|\s|\W)' + re.escape(key) + r'($|\s|\W)'
            match = re.search(pattern, text)
            if match:
                # We found a match. Is it earlier than the current best?
                start_index = match.start()
                if start_index < min_index:
                    min_index = start_index
                    best_match_ticker = ticker

        if best_match_ticker:
            return best_match_ticker

        return "BTC" # Default to Bitcoin

    def run_cycle(self, db: Session):
        self.last_run_status = "Running..."
        logger.info("Manual/Scheduled Run Started")

        try:
            # 1. Fetch
            items = self.ingestion.fetch_news()
            if not items:
                logger.info("No news items found.")
                self.last_run_status = "Finished (No News)"
                return

            # Check DB for processed items to avoid reprocessing old news
            # For cross-verification, we want to look at NEW items (candidates)
            new_items = []
            for item in items:
                item_id = item.get('id', item.get('link'))
                if not db.query(ProcessedNews).filter(ProcessedNews.id == item_id).first():
                    new_items.append(item)

            if not new_items:
                logger.info("No new unprocessed items.")
                self.last_run_status = "Finished (No New Items)"
                return

            # 2. Verify (PIPELINE)
            # Replaced cluster_news with process_pipeline
            logger.info(f"Processing Pipeline for {len(new_items)} new items...")
            verified_events = self.ingestion.process_pipeline(new_items)

            # Updated Logic: Allow single-source events (verified_events will contain them now)
            if not verified_events:
                logger.info("No events found in pipeline.")

                # Record trace
                trace = DecisionTrace(
                    clusters_found=json.dumps([]),
                    topic="None Selected",
                    verification_score=0,
                    sources_list=json.dumps([]),
                    verification_status="SKIPPED",
                    ai_reasoning="No events passed verification pipeline.",
                    generated_tweet=""
                )
                db.add(trace)
                db.commit()

                self.last_run_status = "Finished (Skipped - No Events)"
                return

            # Select the top verified event
            # process_pipeline already sorts by confidence
            selected_event = verified_events[0]

            logger.info(f"Selected Event: {selected_event['title']} (Score: {selected_event['source_count']})")

            # 3. Analyze
            # Gather auxiliary data
            topic_title = selected_event['title']
            symbol = self._extract_symbol(topic_title)
            logger.info(f"Extracted Symbol: {symbol}")

            whale_data = self.whale_monitor.get_whale_movements(symbol)
            market_info = self.market_data.get_market_status(symbol)
            history = self.memory.retrieve_context(topic_title)

            verification_context = f"Whale: {whale_data}\nPrice: {market_info['price']}"

            # Pass the Verified Event object to Agent
            analysis_json = self.agent.analyze_situation(selected_event, verification_context, history)

            try:
                clean_json = analysis_json.replace("```json", "").replace("```", "").strip()
                result = json.loads(clean_json)

                tweet_text = result.get('tweet')
                sentiment = result.get('sentiment')
                knowledge_base_entry = result.get('knowledge_base_entry')
                reasoning = result.get('reasoning')

                # 4. Visualize
                chart_path = self.visualizer.capture_chart(symbol)

                # 5. Publish
                tweet_id = self.publisher.post_tweet(tweet_text, chart_path)

                # 6. Save Trace (Audit Log)
                trace = DecisionTrace(
                    # Store summary of all verified events found this cycle
                    clusters_found=json.dumps([{
                        'topic': e['title'],
                        'score': e['source_count'],
                        'sources': e['sources']
                    } for e in verified_events]),

                    topic=topic_title,
                    verification_score=selected_event['source_count'],
                    sources_list=json.dumps(selected_event['sources']),
                    verification_status="VERIFIED",
                    ai_reasoning=reasoning,
                    generated_tweet=tweet_text
                )
                db.add(trace)

                if tweet_id:
                    # Save items to DB
                    # The event has 'items' which are the full article objects
                    for item in selected_event['items']:
                        item_id = item.get('id', item.get('link'))
                        if not db.query(ProcessedNews).filter(ProcessedNews.id == item_id).first():
                             news_entry = ProcessedNews(
                                id=item_id,
                                title=item.get('title'),
                                source=item.get('source', 'Unknown'),
                                sentiment=sentiment
                            )
                             db.add(news_entry)

                    # Track Engagement
                    if selected_event['items']:
                        primary_item = selected_event['items'][0]
                        primary_id = primary_item.get('id', primary_item.get('link'))
                        engagement = TweetEngagement(
                            tweet_id=str(tweet_id),
                            news_id=primary_id,
                            posted_at=datetime.utcnow()
                        )
                        db.add(engagement)

                    # Save RAG Memory
                    if knowledge_base_entry:
                        self.memory.store_news_event(
                            text=knowledge_base_entry,
                            metadata={
                                "source": "Aggregated",
                                "timestamp": datetime.utcnow().isoformat(),
                                "sentiment": sentiment,
                                "raw_title": topic_title
                            }
                        )

                    logger.info(f"Published tweet {tweet_id}", extra={"context": {"sentiment": sentiment, "tweet_id": tweet_id}})
                    self.last_run_status = "Success"
                else:
                    logger.error("Failed to publish tweet")
                    self.last_run_status = "Failed (Publish Error)"

                db.commit()

            except Exception as e:
                logger.error(f"Analysis/Publishing Error: {e}")
                self.last_run_status = "Failed (Error)"

        except Exception as e:
            logger.error(f"Cycle Error: {e}")
            self.last_run_status = "Failed (Exception)"

    def update_metrics(self, db: Session):
        """Fetch latest metrics for recent tweets"""
        try:
            # Fetch tweets from last 7 days
            recent_tweets = db.query(TweetEngagement).order_by(TweetEngagement.posted_at.desc()).limit(50).all()
            if not recent_tweets:
                return

            tweet_ids = [t.tweet_id for t in recent_tweets]
            metrics_map = self.publisher.fetch_tweet_metrics(tweet_ids)

            for tweet in recent_tweets:
                if tweet.tweet_id in metrics_map:
                    m = metrics_map[tweet.tweet_id]
                    tweet.likes = m['likes']
                    tweet.retweets = m['retweets']
                    tweet.replies = m['replies']
                    tweet.quotes = m['quotes']
                    tweet.impressions = m['impressions']
                    tweet.last_updated = datetime.utcnow()

            db.commit()
            logger.info(f"Updated metrics for {len(tweet_ids)} tweets.")
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")

bot_controller = BotController()

# --- ROUTES ---

@app.get("/api/status")
def get_status():
    return {
        "status": "Running" if bot_controller.is_running else "Idle",
        "last_run_status": bot_controller.last_run_status
    }

@app.post("/api/control/run")
def run_bot(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(bot_controller.run_cycle, db)
    return {"message": "Bot cycle started in background"}

@app.get("/api/logs")
def get_logs(limit: int = 20, db: Session = Depends(get_db)):
    logs = db.query(BotLog).order_by(BotLog.timestamp.desc()).limit(limit).all()
    return logs

@app.get("/api/audit")
def get_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    traces = db.query(DecisionTrace).order_by(DecisionTrace.timestamp.desc()).limit(limit).all()
    return traces

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    # Sentiment Distribution
    bullish = db.query(ProcessedNews).filter(ProcessedNews.sentiment == "BULLISH").count()
    bearish = db.query(ProcessedNews).filter(ProcessedNews.sentiment == "BEARISH").count()
    neutral = db.query(ProcessedNews).filter(ProcessedNews.sentiment == "NEUTRAL").count()

    # Engagement Over Time (for Charts)
    # Return list of {date, likes, retweets}
    engagement_data = db.query(TweetEngagement).order_by(TweetEngagement.posted_at.asc()).limit(30).all()
    engagement_list = [
        {
            "id": e.tweet_id,
            "date": e.posted_at.strftime("%Y-%m-%d %H:%M"),
            "likes": e.likes,
            "retweets": e.retweets
        }
        for e in engagement_data
    ]

    return {
        "sentiment": {"bullish": bullish, "bearish": bearish, "neutral": neutral},
        "engagement": engagement_list
    }

# Render Frontend
from starlette.requests import Request
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/audit", response_class=HTMLResponse)
def audit_page(request: Request):
    return templates.TemplateResponse("audit.html", {"request": request})

@app.get("/config", response_class=HTMLResponse)
def config_page(request: Request):
    return templates.TemplateResponse("config.html", {"request": request})

# Scheduler Logic
def scheduler_loop():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Start Scheduler on Startup
@app.on_event("startup")
def startup_event():
    # Define schedule job
    def job():
        # Create a new DB session for the thread
        from src.database import SessionLocal
        with SessionLocal() as db:
            # Update metrics first
            bot_controller.update_metrics(db)
            # Run cycle
            bot_controller.run_cycle(db)

    schedule.every(4).hours.do(job)

    # Run scheduler in thread
    t = threading.Thread(target=scheduler_loop, daemon=True)
    t.start()
    bot_controller.scheduler_thread = t
    bot_controller.is_running = True

if __name__ == "__main__":
    uvicorn.run("src.web.app:app", host="0.0.0.0", port=8000, reload=True)
