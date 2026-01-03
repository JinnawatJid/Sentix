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
        self.rss_url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
        self.twitter_client = TwitterClient()

    def fetch_news(self):
        """
        Main entry point. Tries X API first, then falls back to RSS.
        """
        all_news = []

        # 1. Try X API
        # We try to get news from WatcherGuru and CoinDesk
        wg_news = self.twitter_client.fetch_tweets("WatcherGuru", count=2)
        if wg_news:
            all_news.extend(wg_news)

        cd_news = self.twitter_client.fetch_tweets("CoinDesk", count=2)
        if cd_news:
            all_news.extend(cd_news)

        if all_news:
            logger.info(f"Successfully fetched {len(all_news)} tweets from X API.")
        else:
            logger.info("X API failed or returned no data from any source. Switching to RSS Fallback.")
            # 2. Fallback to RSS
            rss_news = self.fetch_coindesk_news()
            all_news.extend(rss_news)

        return all_news

    def fetch_coindesk_news(self):
        """Fetches the latest news from CoinDesk RSS feed."""
        logger.info("Fetching CoinDesk RSS feed...")
        try:
            feed = feedparser.parse(self.rss_url)
            news_items = []
            for entry in feed.entries[:5]: # Get top 5
                news_items.append({
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.published,
                    "summary": entry.summary,
                    "source": "CoinDesk",
                    "id": entry.link
                })

            if news_items:
                logger.info(f"Successfully fetched {len(news_items)} items from CoinDesk RSS.")
            return news_items
        except Exception as e:
            logger.error(f"RSS Fetch Error: {e}")
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
        print(f"Sample: {items[0]['title']}")
    
    whale = WhaleMonitor()
    print("\n--- Testing Whale Monitor ---")
    print(f"Whale Status: {whale.get_whale_movements('BTC')}")
