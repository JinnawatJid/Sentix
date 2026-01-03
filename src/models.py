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
