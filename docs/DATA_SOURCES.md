# Data Sources & Integration Strategy

This document outlines the external data sources used by Sentix to fetch news, verify facts, and visualize market data. The system employs a "Multi-Source" verification strategy to ensure high signal fidelity and reduce false positives.

---

## 1. Primary News & Signal Sources
*Purpose: To detect breaking news and market events in real-time.*

### A. X (Twitter) API
*   **Role:** The primary "fast" signal.
*   **Method:** `src/ingestion.py` -> `TwitterClient`
*   **Key Accounts:**
    *   `@WatcherGuru`: High-speed breaking news.
    *   `@CoinDesk`: Institutional-grade reporting.
*   **Logic:** The system attempts to fetch the latest tweets from these user timelines.

### B. RSS Feeds (Fallback & Context)
*   **Role:** Robust fallback if Twitter Rate Limits (429) are hit, and provides broader context for cross-verification.
*   **Method:** `src/ingestion.py` -> `IngestionModule` -> `fetch_rss_feed`
*   **Sources:**
    *   **CoinDesk:** `https://www.coindesk.com/arc/outboundfeeds/rss/`
    *   **CoinTelegraph:** `https://cointelegraph.com/rss`
    *   **The Block:** `https://www.theblock.co/rss`
    *   **Decrypt:** `https://decrypt.co/feed`

---

## 2. Verification & Truth Sources
*Purpose: To validate if the news is "real" or just "noise" (FUD) by checking hard numbers.*

### A. CoinGecko API
*   **Role:** Market Price Verification.
*   **Endpoint:** `api.coingecko.com/api/v3/simple/price`
*   **Method:** `src/ingestion.py` -> `MarketData`
*   **Data Points:** Real-time Price (USD) and 24h Change %.
*   **Usage:** Checks if the market price is actually reacting to the news event (e.g., if news is "BTC Crashes" but price is flat, it might be FUD).

### B. Blockchain.info API
*   **Role:** On-Chain "Truth" Fallback.
*   **Endpoint:** `blockchain.info/unconfirmed-transactions`
*   **Method:** `src/ingestion.py` -> `WhaleMonitor`
*   **Data Points:** Unconfirmed mempool transactions > 10 BTC.
*   **Usage:** Used when the Twitter-based "Whale Alert" is unreachable. It allows the bot to directly verify if large funds are moving on-chain.

### C. X (Twitter) - Whale Alert
*   **Role:** Primary Whale Monitoring.
*   **Account:** `@whale_alert`
*   **Method:** `src/ingestion.py` -> `WhaleMonitor`
*   **Usage:** Scans for tweets mentioning the target symbol (e.g., "BTC") to see if whales are moving funds to/from exchanges.

---

## 3. Visualization Sources
*Purpose: To generate the visual "proof" attached to the tweet.*

### A. TradingView
*   **Role:** Chart Generation.
*   **URL:** `https://www.tradingview.com/chart/?symbol={SYMBOL}USD`
*   **Method:** `src/visualizer.py` -> `Visualizer`
*   **Tech:** Uses **Playwright** (Headless Chromium) to visit the URL and capture a screenshot.
*   **Usage:** Provides a visual confirmation of the price action described in the text.

---

## 4. Intelligence & Memory (Internal)
*Purpose: To process raw data into actionable insights.*

*   **Google Gemini API:** The "Processor" that analyzes the text sentiment and generates the tweet.
*   **ChromaDB:** The "Long-term Memory" where the bot queries its own past experiences to find historical parallels (RAG).
