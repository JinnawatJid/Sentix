# 🚀 Project Summary: Sentix (AI-Driven Crypto News Bot) v1.1

> **Use this file to restore context in future AI sessions.**

## **Overview**
Sentix is a RAG-based automated bot that fetches real-time crypto news, verifies it with live on-chain/market data, analyzes sentiment using the **Google Gemini API**, and generates visual trading charts for X (Twitter).

## **Key Features Implemented**
1.  **Real-Time Ingestion (with Fallbacks):**
    *   **Primary:** X (Twitter) API via `tweepy`.
    *   **Fallback:** If the X API hits Rate Limits (429) or Access Denied (403), it automatically falls back to the **CoinDesk RSS Feed**.
    *   **On-Chain Fallback:** If Twitter is down, it queries **Blockchain.info API** for live large Bitcoin transactions (> 10 BTC).
    *   **Market Data:** Uses **CoinGecko API** to verify price impacts.

2.  **RAG Memory:**
    *   Uses **ChromaDB** to store news events and retrieve historical context for the AI.

3.  **AI Analysis:**
    *   Integrated with **Google Gemini API** (`gemini-3-flash-preview`) for fast, cost-effective sentiment analysis and tweet generation.
    *   **Robustness:** Includes error handling for API failures.

4.  **Visualization:**
    *   Uses **Playwright** to capture live screenshots of TradingView charts (e.g., `BTCUSD`) to attach to tweets.

5.  **Infrastructure:**
    *   Full **Docker & Docker Compose** setup.

## **Technical Stack**
*   **Language:** Python 3.11
*   **Core Libs:** `google-genai`, `tweepy`, `chromadb`, `playwright`, `feedparser`, `requests`, `schedule`.
*   **Deployment:** Docker Compose.

## **File Structure**
*   `src/ingestion.py`: Handles Twitter API (with RSS fallback), Blockchain API, and CoinGecko.
*   `src/agent.py`: Interface to Google Gemini API.
*   `src/memory.py`: Vector database logic (ChromaDB).
*   `src/visualizer.py`: Chart generation (Playwright).
*   `main.py`: Main orchestration loop.
*   `tests/`: Contains test scripts (Live Integration and Dry Run).

## **How to Run**
1.  **Setup Environment:**
    *   Follow instructions in `SETUP.md` to obtain API keys (`GEMINI_API_KEY`, `TWITTER_*`).
    *   Create a `.env` file.
2.  **Run Tests:**
    *   **Dry Run (No Keys Needed):** `python tests/test_dry_run_v2.py`
    *   **Live Integration:** `python tests/test_live_integration.py`
3.  **Start Bot:**
    *   **Docker:** `docker-compose up --build`
    *   **Manual:** `pip install -r requirements.txt && python main.py`
