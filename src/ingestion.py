import feedparser
from datetime import datetime
import time
import requests
import logging
import os
import difflib
from dotenv import load_dotenv
from src.events import resolve_events
from src.facts import extract_facts

load_dotenv()
logger = logging.getLogger("Ingestion")

class IngestionModule:
    def __init__(self):
        # Extended RSS Sources
        self.rss_feeds = {
            "WatcherGuru": "https://watcher.guru/news/feed",
            "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "CoinTelegraph": "https://cointelegraph.com/rss",
            "TheBlock": "https://www.theblock.co/rss",
            "Decrypt": "https://decrypt.co/feed"
        }

    def fetch_news(self):
        """
        Fetches news from RSS sources.
        """
        all_news = []

        # Fetch from RSS Sources
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
            # Updated to fetch 5 items per source as requested
            for entry in feed.entries[:5]:
                # Handle inconsistent field names
                summary = getattr(entry, 'summary', '')
                if not summary and hasattr(entry, 'description'):
                    summary = entry.description

                # Explicit logging for dashboard visibility
                logger.info(f"[{source_name}] Found: {entry.title}")

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

    def process_pipeline(self, news_items):
        """
        Orchestrates the Verification Pipeline:
        1. Anonymize Sources
        2. Resolve Events (Event Detection)
        3. Extract Facts (Fact Validation) with Source Confidence
        """
        logger.info("Starting Event Resolution Pipeline...")

        # 1. Anonymize for unbiased event detection
        anonymized_items = []
        item_map = {} # Map ID/Link back to full object

        for item in news_items:
            # Use link as ID if id is missing
            item_id = item.get('id', item.get('link'))
            item['id'] = item_id # Ensure ID exists

            item_map[item_id] = item

            # Create anon copy
            anon_item = item.copy()
            if 'source' in anon_item:
                del anon_item['source']
            anonymized_items.append(anon_item)

        # 2. Resolve Events
        # Returns list of { event_id, title, articles: [id1, id2...] }
        events = resolve_events(anonymized_items)
        if not events:
            logger.info("No events resolved from news items.")
            return []

        verified_events = []

        # 3. Process Each Event
        for event in events:
            article_ids = event.get('articles', [])

            # Retrieve full articles with sources
            full_articles = [item_map[aid] for aid in article_ids if aid in item_map]

            if not full_articles:
                continue

            # Check strictly for distinct sources before expensive LLM call
            unique_sources = set(a['source'] for a in full_articles)

            # Extract Facts (Verification)
            # This returns { facts: [], confidence: 0.0-1.0 }
            fact_data = extract_facts(event, full_articles)

            # Enrich Event Object
            event['facts'] = fact_data.get('facts', [])
            event['confidence'] = fact_data.get('confidence', 0)
            event['sources'] = list(unique_sources)
            event['source_count'] = len(unique_sources)
            event['items'] = full_articles # Replace IDs with full objects for the Agent

            # Filter Logic:
            # User mentioned: "stories with a Verification Score of less than 2 are marked as UNVERIFIED"
            if event['source_count'] >= 2:
                 verified_events.append(event)
            else:
                 logger.info(f"Event '{event['title']}' rejected. Only {event['source_count']} source(s).")

        # Sort by confidence/source count
        verified_events.sort(key=lambda x: x['source_count'], reverse=True)

        return verified_events

class WhaleMonitor:
    def __init__(self):
        pass

    def get_whale_movements(self, symbol="BTC"):
        """
        Checks Blockchain.info for large unconfirmed transactions.
        """
        logger.info("Checking Blockchain.info for large transactions (Whale Monitor)...")
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
