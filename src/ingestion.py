import feedparser
from datetime import datetime
import time
import requests
import logging
import tweepy
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("Ingestion")

class TwitterClient:
    def __init__(self):
        # We need Bearer Token for reading (if available) or OAuth1/2 for writing
        # For Free Tier reading (user timeline) is usually restricted, but we try anyway.
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.client = None
        if self.bearer_token:
            try:
                self.client = tweepy.Client(bearer_token=self.bearer_token)
            except Exception as e:
                logger.error(f"Failed to initialize Twitter Client: {e}")

    def fetch_tweets(self, username, count=2):
        """
        Attempts to fetch tweets from a user's timeline.
        This often fails on Free Tier (403 Forbidden).
        """
        if not self.client:
            return []

        logger.info(f"Attempting to fetch tweets from @{username} via X API...")
        try:
            # 1. Get User ID
            user = self.client.get_user(username=username)
            if not user.data:
                logger.warning(f"User @{username} not found.")
                return []

            user_id = user.data.id

            # 2. Get Tweets
            # exclude=['retweets', 'replies'] is good practice
            response = self.client.get_users_tweets(user_id, max_results=5, exclude=['retweets', 'replies'])

            tweets = []
            if response.data:
                for t in response.data[:count]:
                    logger.info(f"Fetched Tweet ID {t.id} from @{username}: {t.text[:50]}...")
                    tweets.append({
                        "title": f"Tweet from @{username}",
                        "text": t.text,
                        "summary": t.text, # Use text as summary
                        "source": f"@{username}",
                        "timestamp": datetime.now().isoformat(), # API v2 doesn't give date easily without fields expansion
                        "id": str(t.id),
                        "link": f"https://twitter.com/{username}/status/{t.id}"
                    })
            return tweets

        except tweepy.errors.Forbidden as e:
            logger.warning(f"X API Access Denied (403): Free Tier likely restricts reading tweets. {e}")
            return None # Signal to trigger fallback
        except tweepy.errors.TooManyRequests as e:
            logger.warning(f"X API Rate Limit Hit (429). {e}")
            return None
        except Exception as e:
            logger.error(f"X API General Error: {e}")
            return None

class IngestionModule:
    def __init__(self):
        # Extended RSS Sources
        self.rss_feeds = {
            "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "CoinTelegraph": "https://cointelegraph.com/rss",
            "TheBlock": "https://www.theblock.co/rss",
            "Decrypt": "https://decrypt.co/feed"
        }
        self.twitter_client = TwitterClient()

    def fetch_news(self):
        """
        Fetches news from ALL available sources (Twitter + RSS) to allow for cross-verification.
        """
        all_news = []

        # 1. Fetch from Twitter Sources (if available/limit not hit)
        twitter_sources = ["WatcherGuru", "CoinDesk"] # Could add others but kept simple for now
        for handle in twitter_sources:
            try:
                tweets = self.twitter_client.fetch_tweets(handle, count=2)
                if tweets:
                    all_news.extend(tweets)
                # Polite delay between calls
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error fetching tweets for {handle}: {e}")

        # 2. Fetch from RSS Sources (Reliable Backbone)
        for source_name, url in self.rss_feeds.items():
            rss_items = self.fetch_rss_feed(source_name, url)
            if rss_items:
                all_news.extend(rss_items)

        logger.info(f"Total aggregated news items: {len(all_news)}")
        return all_news

    def fetch_rss_feed(self, source_name, url):
        """Fetches and parses a generic RSS feed."""
        logger.info(f"Fetching {source_name} RSS feed...")
        try:
            feed = feedparser.parse(url)
            news_items = []
            for entry in feed.entries[:3]: # Get top 3 from each to avoid noise
                # Handle inconsistent field names
                summary = getattr(entry, 'summary', '')
                if not summary and hasattr(entry, 'description'):
                    summary = entry.description

                news_items.append({
                    "title": entry.title,
                    "link": entry.link,
                    "published": getattr(entry, 'published', datetime.now().isoformat()),
                    "summary": summary,
                    "source": source_name,
                    "id": entry.link
                })
            return news_items
        except Exception as e:
            logger.error(f"RSS Fetch Error ({source_name}): {e}")
            return []

class WhaleMonitor:
    def __init__(self):
        self.twitter_client = TwitterClient()

    def get_whale_movements(self, symbol="BTC"):
        """
        Tries to get data from @whale_alert. 
        Fallback: Uses blockchain.info to find large unconfirmed transactions.
        """
        # 1. Try Twitter (X API)
        tweets = self.twitter_client.fetch_tweets("whale_alert", count=3)
        if tweets:
            relevant = [t['text'] for t in tweets if symbol in t['text']]
            if relevant:
                return f"Recent Whale Alerts (Verified via X): {'; '.join(relevant)}"
        
        # 2. Fallback: Real On-Chain Data (Blockchain.info)
        logger.info("Fallback: Checking Blockchain.info for large transactions...")
        try:
            # Fetch unconfirmed transactions
            url = "https://blockchain.info/unconfirmed-transactions?format=json"
            r = requests.get(url, timeout=10)
            data = r.json()
            
            large_txs = []
            for tx in data.get('txs', [])[:50]: # Check first 50
                total_out = sum([out.get('value', 0) for out in tx.get('out', [])])
                # Convert satoshis to BTC
                btc_value = total_out / 100_000_000
                if btc_value > 10: # Only care about > 10 BTC
                    large_txs.append(f"{btc_value:.2f} BTC")
            
            if large_txs:
                top_tx = sorted(large_txs, key=lambda x: float(x.split()[0]), reverse=True)[:3]
                return f"Live On-Chain Data: Detected large unconfirmed transactions: {', '.join(top_tx)}."
            
            return "No significant large transactions detected in mempool."
            
        except Exception as e:
            logger.error(f"Blockchain API Error: {e}")
            return "Unable to verify on-chain data."

class MarketData:
    def get_market_status(self, symbol="BTC"):
        """
        Fetches real-time price using CoinGecko API (No key needed).
        """
        try:
            # Map symbol to CoinGecko ID
            ids = {"BTC": "bitcoin", "ETH": "ethereum"}
            cg_id = ids.get(symbol, "bitcoin")
            
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd&include_24hr_change=true"
            r = requests.get(url, timeout=10)
            data = r.json()
            
            price = data[cg_id]['usd']
            change = data[cg_id]['usd_24h_change']
            
            return {
                "symbol": symbol,
                "price": price,
                "change_24h": round(change, 2),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Market Data Error: {e}")
            return {"symbol": symbol, "price": "N/A", "change_24h": "N/A"}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test
    ingestor = IngestionModule()
    print("--- Testing Ingestion ---")
    items = ingestor.fetch_news()
    print(f"Fetched {len(items)} items.")
    if items:
        print(f"Sample: {items[0]['title']} ({items[0]['source']})")
    
    whale = WhaleMonitor()
    print("\n--- Testing Whale Monitor ---")
    print(f"Whale Status: {whale.get_whale_movements('BTC')}")
