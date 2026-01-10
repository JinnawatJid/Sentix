from sqlalchemy.orm import Session
from src.database import SessionLocal, engine, Base
from src.models import ProcessedNews, BotLog, TweetEngagement, DecisionTrace
from datetime import datetime, timedelta
import random
import json

def seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear existing data for a clean mock
    db.query(ProcessedNews).delete()
    db.query(TweetEngagement).delete()
    db.query(BotLog).delete()
    db.query(DecisionTrace).delete()

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

    # 3. Mock Logs
    print("Generating logs...")
    base_time = datetime.utcnow() - timedelta(hours=1)
    logs = [
        ("INFO", "Manual/Scheduled Run Started"),
        ("INFO", "Ingestion: Fetching CoinDesk RSS feed..."),
        ("INFO", "Ingestion: [CoinDesk] Found: Bitcoin ETF Approved"),
        ("INFO", "Ingestion: Clustering 5 new items..."),
        ("INFO", "WebDashboard: Selected Cluster: Bitcoin ETF (Score: 3)"),
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

    # 4. Mock Decision Traces (The new feature!)
    print("Generating Decision Traces (Audit Log)...")

    # Trace 1: Verified
    trace_verified = DecisionTrace(
        timestamp=datetime.utcnow() - timedelta(minutes=30),
        topic="Bitcoin ETF Approval",
        verification_score=3,
        sources_list=json.dumps(["CoinDesk", "WatcherGuru", "TheBlock"]),
        verification_status="VERIFIED",
        ai_reasoning="Consensus found across 3 major sources. Sentiment is clearly BULLISH. No contradictions found.",
        generated_tweet="📰 Consensus: Bitcoin ETF Approved (Confidence: HIGH)\n\n🧠 Impact: Institutional floodgates open.\n\n🚀 Outlook: BULLISH [Source: CoinDesk] #BTC",
        clusters_found=json.dumps([
            {"topic": "Bitcoin ETF Approval", "score": 3, "sources": ["CoinDesk", "WatcherGuru", "TheBlock"]},
            {"topic": "Solana Downtime", "score": 1, "sources": ["Twitter"]}
        ])
    )
    db.add(trace_verified)

    # Trace 2: Unverified/Skipped
    trace_skipped = DecisionTrace(
        timestamp=datetime.utcnow() - timedelta(hours=4),
        topic="Random Meme Coin Pump",
        verification_score=1,
        sources_list=json.dumps(["TwitterUser123"]),
        verification_status="SKIPPED",
        ai_reasoning="No cluster met verification threshold (Score < 2).",
        generated_tweet="",
        clusters_found=json.dumps([
            {"topic": "Random Meme Coin Pump", "score": 1, "sources": ["TwitterUser123"]}
        ])
    )
    db.add(trace_skipped)

    db.commit()
    db.close()
    print("Seeding complete! You can now check the Audit Log in the Dashboard.")

if __name__ == "__main__":
    seed_data()
