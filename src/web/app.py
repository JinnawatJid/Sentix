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

from src.database import get_db, engine, Base
from src.models import ProcessedNews, BotLog, TweetEngagement
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

            # Check DB for duplicates
            target_item = None
            for item in items:
                item_id = item.get('id', item.get('link'))
                if not db.query(ProcessedNews).filter(ProcessedNews.id == item_id).first():
                    target_item = item
                    break

            if not target_item:
                logger.info("No new unprocessed items.")
                self.last_run_status = "Finished (No New Items)"
                return

            # 2. Process
            text_content = f"{target_item.get('title', '')} {target_item.get('summary', '')}"
            symbol = "BTC" if "BTC" in text_content or "Bitcoin" in text_content else "ETH"

            whale_data = self.whale_monitor.get_whale_movements(symbol)
            market_info = self.market_data.get_market_status(symbol)
            history = self.memory.retrieve_context(text_content)

            verification = f"Whale: {whale_data}\nPrice: {market_info['price']}"

            # 3. Analyze
            analysis_json = self.agent.analyze_situation(target_item, verification, history)
            try:
                clean_json = analysis_json.replace("```json", "").replace("```", "").strip()
                result = json.loads(clean_json)
                tweet_text = result.get('tweet')
                sentiment = result.get('sentiment')

                # 4. Visualize
                chart_path = self.visualizer.capture_chart(symbol)

                # 5. Publish
                tweet_id = self.publisher.post_tweet(tweet_text, chart_path)

                if tweet_id:
                    # Save to DB
                    item_id = target_item.get('id', target_item.get('link'))

                    # Store News
                    news_entry = ProcessedNews(
                        id=item_id,
                        title=target_item.get('title'),
                        source=target_item.get('source', 'Unknown'),
                        sentiment=sentiment
                    )

                    # Prevent integrity error if item already exists (rare due to check above, but safe)
                    existing = db.query(ProcessedNews).filter(ProcessedNews.id == item_id).first()
                    if not existing:
                        db.add(news_entry)

                    # Track Engagement
                    engagement = TweetEngagement(
                        tweet_id=str(tweet_id),
                        news_id=item_id,
                        posted_at=datetime.utcnow()
                    )
                    db.add(engagement)

                    logger.info(f"Published tweet {tweet_id} for {item_id}", extra={"context": {"sentiment": sentiment, "tweet_id": tweet_id}})
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

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    # Trigger metric update if needed (could be async, but quick enough here for small batches)
    # For now, let's trust the background job to update it, or add an explicit update endpoint.
    # To keep stats fresh, we'll try a quick update if it's been a while?
    # Better: just return what we have.

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
        db = next(get_db())
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
