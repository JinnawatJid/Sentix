from sqlalchemy.orm import Session
from src.database import SessionLocal, engine, Base
from src.models import ProcessedNews, BotLog, TweetEngagement
from datetime import datetime, timedelta
import random

def seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear existing data for a clean mock
    db.query(ProcessedNews).delete()
    db.query(TweetEngagement).delete()
    db.query(BotLog).delete()

    print("Seeding data...")

    # 1. Mock News & Sentiment
    sentiments = ["BULLISH", "BEARISH", "NEUTRAL"]
    start_date = datetime.utcnow() - timedelta(days=7)

    for i in range(50):
        date = start_date + timedelta(hours=i*3 + random.randint(0, 2))
        sentiment = random.choices(sentiments, weights=[0.4, 0.3, 0.3])[0]

        news_id = f"news_{i}"
        tweet_id = f"tweet_{i}"

        news = ProcessedNews(
            id=news_id,
            title=f"Crypto Market Update #{i}: {sentiment} signals detected",
            source="CoinDesk",
            published_at=date,
            sentiment=sentiment,
            processed_at=date
        )
        db.add(news)

        # 2. Mock Engagement (Correlated with sentiment for fun)
        base_likes = random.randint(10, 50)
        if sentiment == "BULLISH": base_likes *= 2

        engagement = TweetEngagement(
            tweet_id=tweet_id,
            news_id=news_id,
            posted_at=date,
            likes=base_likes + random.randint(0, 20),
            retweets=int(base_likes * 0.3) + random.randint(0, 5),
            replies=random.randint(0, 10),
            quotes=random.randint(0, 5),
            impressions=base_likes * 50
        )
        db.add(engagement)

    # 3. Mock Logs - UPDATED with detailed format
    print("Generating logs with new format...")
    base_time = datetime.utcnow() - timedelta(hours=1)

    # Simulate a full cycle
    logs = [
        ("INFO", "Manual/Scheduled Run Started"),
        ("INFO", "Ingestion: Attempting to fetch tweets from @WatcherGuru via X API..."),
        ("INFO", "Ingestion: Fetched Tweet ID 12345 from @WatcherGuru: Bitcoin is breaking out! #BTC..."),
        ("INFO", "Ingestion: Successfully fetched 1 tweets from X API."),
        ("INFO", "Ingestion: Attempting to fetch tweets from @whale_alert via X API..."),
        ("WARNING", "Ingestion: X API Rate Limit Hit (429). Too Many Requests"),
        ("INFO", "Ingestion: X API failed or returned no data. Switching to RSS Fallback."),
        ("INFO", "Ingestion: Fetching CoinDesk RSS feed..."),
        ("INFO", "Ingestion: Successfully fetched 5 items from CoinDesk RSS."),
        ("INFO", "WebDashboard: Published tweet 99999 for link_abc", {"context": {"sentiment": "BULLISH", "tweet_id": "99999"}})
    ]

    for idx, (level, msg, *rest) in enumerate(logs):
        ctx = rest[0] if rest else None
        log = BotLog(
            timestamp=base_time + timedelta(seconds=idx*5),
            level=level,
            message=msg,
            context=ctx
        )
        db.add(log)

    db.commit()
    db.close()
    print("Seeding complete!")

if __name__ == "__main__":
    seed_data()
