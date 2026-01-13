# Data Sources & Integration Strategy

This document outlines the external data sources used by Sentix to fetch news, verify facts, and visualize market data. The system employs a "Multi-Source" verification strategy to ensure high signal fidelity and reduce false positives.

---

## 1. Primary News & Signal Sources
*Purpose: To detect breaking news and market events in real-time.*

### A. RSS Feeds (Primary)
*   **Role:** The exclusive source of news ingestion.
*   **Method:** `src/ingestion.py` -> `IngestionModule` -> `fetch_rss_feed`
*   **Sources:**
    *   **WatcherGuru:** `https://watcher.guru/news/feed` (High-speed breaking news)
    *   **CoinDesk:** `https://www.coindesk.com/arc/outboundfeeds/rss/`
    *   **CoinTelegraph:** `https://cointelegraph.com/rss`
    *   **The Block:** `https://www.theblock.co/rss`
    *   **Decrypt:** `https://decrypt.co/feed`
*   **Update:** We now fetch **5 items** per source (increased from 3) to improve event clustering coverage.

### B. X (Twitter) API
*   **Role:** Posting Only.
*   **Method:** `src/publisher.py` -> `TwitterPublisher`
*   **Status:** **Ingestion from Twitter has been removed** to eliminate dependency on unstable Free Tier limits and to ensure all data comes from verifiable, long-form editorial sources (RSS).

---

## 2. Verification & Truth Sources
*Purpose: To validate if the news is "real" or just "noise" (FUD) by checking hard numbers.*

### A. The Verification Pipeline (New in v2.1)
Instead of simple text clustering, we now employ a rigorous multi-step verification process:

1.  **Event Resolution (`src/events.py`):**
    *   Input: Anonymized news items (Source labels removed to prevent bias).
    *   Logic: AI groups articles describing the *exact same real-world occurrence* into an Event.
2.  **Fact Extraction (`src/facts.py`):**
    *   Input: The Resolved Event + Original Articles (Sources re-attached).
    *   Logic: AI extracts *atomic facts* that are confirmed by at least **2 Independent Sources**.
    *   **Confidence Score:** Calculated as `(Agreeing Sources) / (Total Independent Sources)`.
3.  **Critic Loop (`src/agent.py`):**
    *   Input: Draft Tweet + Verified Facts.
    *   Logic: A secondary "Critic" AI reviews the draft against the facts to detect hallucinations before publishing.

### B. CoinGecko API
*   **Role:** Market Price Verification.
*   **Endpoint:** `api.coingecko.com/api/v3/simple/price`
*   **Method:** `src/ingestion.py` -> `MarketData`
*   **Data Points:** Real-time Price (USD) and 24h Change %.
*   **Usage:** Checks if the market price is actually reacting to the news event (e.g., if news is "BTC Crashes" but price is flat, it might be FUD).

### C. Blockchain.info API (Whale Monitor)
*   **Role:** Primary Whale Monitoring (On-Chain Truth).
*   **Endpoint:** `blockchain.info/unconfirmed-transactions`
*   **Method:** `src/ingestion.py` -> `WhaleMonitor`
*   **Data Points:** Unconfirmed mempool transactions > 10 BTC.
*   **Usage:** Directly checks the Bitcoin mempool for large movements.

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

---

## 5. Selection Rationale: Why These Sources?

The crypto news landscape is vast. We selected this specific portfolio based on three pillars: **Speed, Veracity, and Independence.**

### A. Speed vs. Accuracy Portfolio
*   **WatcherGuru (Speed):** They are arguably the fastest "breaking news" outlet in crypto. They often tweet headlines seconds after an event. We use them as the "Trigger".
*   **CoinDesk & The Block (Accuracy):** Speed is dangerous without verification. These outlets adhere to traditional journalistic standards. If WatcherGuru reports it, we check CoinDesk to see if it's confirmed or if it's a rumor.
*   **Decrypt (Accessibility):** Provides excellent context and "explainer" style content, helping the AI understand the *implications* of technical news.

### B. The "Ground Truth" Layer
*   **CoinGecko (Independence):** Unlike CoinMarketCap (owned by Binance), CoinGecko is an independent data aggregator. This removes potential conflict-of-interest bias when reporting exchange-related news or token prices.
*   **Blockchain.info (Raw Truth):** Social media can lie. The blockchain cannot. By querying the mempool directly, we bypass editorialized "Whale Alert" tweets (which can be delayed or filtered) and get a raw, unbiased view of capital flow.
