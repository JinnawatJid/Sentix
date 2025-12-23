import feedparser
from datetime import datetime
import time
import yfinance as yf
from ntscraper import Nitter
import logging
import requests
import random

logger = logging.getLogger("Ingestion")

class IngestionModule:
    def __init__(self):
        self.rss_url = "https://www.coindesk.com/arc/outboundfeeds/rss/"

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
                    "source": "CoinDesk"
                })
            return news_items
        except Exception as e:
            logger.error(f"RSS Fetch Error: {e}")
            return []

class TwitterScraper:
    def __init__(self):
        # Retry logic for Nitter instances could go here, but Nitter is inherently unstable without a rotating proxy.
        self.scraper = Nitter(log_level=1, skip_instance_check=False)

    def fetch_tweets(self, accounts=["WatcherGuru", "CoinDesk"], count=2):
        tweets = []
        for account in accounts:
            logger.info(f"Scraping tweets from @{account}...")
            try:
                data = self.scraper.get_tweets(account, mode='user', number=count)
                if 'tweets' in data and len(data['tweets']) > 0:
                    for t in data['tweets']:
                        tweets.append({
                            "text": t['text'],
                            "user": account,
                            "timestamp": t['date'],
                            "id": t['link'],
                            "link": t['link']
                        })
                else:
                    logger.warning(f"No tweets found for @{account}")
            except Exception as e:
                logger.error(f"Error scraping @{account}: {e}")
                # No mock fallback here; if we can't get tweets, we just return empty list
        return tweets

class WhaleMonitor:
    def __init__(self):
        self.scraper = TwitterScraper()

    def get_whale_movements(self, symbol="BTC"):
        """
        Tries to get data from @whale_alert. 
        Fallback: Uses blockchain.info to find large unconfirmed transactions.
        """
        # 1. Try Twitter
        tweets = self.scraper.fetch_tweets(["whale_alert"], count=3)
        if tweets:
            # Filter for relevant symbol
            relevant = [t['text'] for t in tweets if symbol in t['text']]
            if relevant:
                return f"Recent Whale Alerts: {'; '.join(relevant)}"
        
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
    print(f"News Items: {len(ingestor.fetch_coindesk_news())}")
    
    whale = WhaleMonitor()
    print(f"Whale Status: {whale.get_whale_movements('BTC')}")
    
    market = MarketData()
    print(f"Market: {market.get_market_status('BTC')}")
