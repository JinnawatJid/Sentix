from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from datetime import datetime
from src.database import Base

class ProcessedNews(Base):
    __tablename__ = "processed_news"

    id = Column(String, primary_key=True, index=True) # URL or Unique ID
    title = Column(String)
    source = Column(String)
    published_at = Column(DateTime, default=datetime.utcnow)
    sentiment = Column(String) # BULLISH, BEARISH, NEUTRAL
    processed_at = Column(DateTime, default=datetime.utcnow)

class BotLog(Base):
    __tablename__ = "bot_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String) # INFO, ERROR, WARNING
    message = Column(Text)
    context = Column(JSON, nullable=True) # Store extra data like tweet_id

class TweetEngagement(Base):
    __tablename__ = "tweet_engagement"

    tweet_id = Column(String, primary_key=True)
    news_id = Column(String) # Foreign key reference logic to ProcessedNews
    posted_at = Column(DateTime)

    # Metrics
    likes = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    quotes = Column(Integer, default=0)
    impressions = Column(Integer, default=0) # If available

    last_updated = Column(DateTime, default=datetime.utcnow)

class DecisionTrace(Base):
    __tablename__ = "decision_traces"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Input Data Snapshot
    clusters_found = Column(JSON) # Summary of all clusters found in this cycle

    # Selected Topic Info
    topic = Column(String) # The representative title of the chosen story
    verification_score = Column(Integer) # How many distinct sources confirmed it
    sources_list = Column(JSON) # List of source names (e.g. ["CoinDesk", "WatcherGuru"])

    # AI Logic
    ai_reasoning = Column(Text) # The 'reasoning' field from Gemini

    # Outcome
    generated_tweet = Column(Text)
    verification_status = Column(String) # "VERIFIED" (>=2 sources) or "UNVERIFIED"
