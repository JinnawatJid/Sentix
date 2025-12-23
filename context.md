# 🚀 Project Summary: Sentix (AI-Driven Crypto News Bot) v1.0

> **Use this file to restore context in future AI sessions.**

## **Overview**
Sentix is a RAG-based automated bot that fetches real-time crypto news, verifies it with live on-chain/market data, analyzes sentiment using a local LLM (Google Gemma 3), and generates visual trading charts for X (Twitter).

## **Key Features Implemented**
1.  **Real-Time Ingestion (with Fallbacks):**
    *   **News:** CoinDesk RSS Feed.
    *   **Social:** Twitter Scraper (`ntscraper`) for @WatcherGuru & @whale_alert.
    *   **On-Chain Fallback:** If Twitter is down, it automatically queries **Blockchain.info API** for live large Bitcoin transactions (> 10 BTC).
    *   **Market Data:** Uses **CoinGecko API** to verify price impacts (e.g., "Is BTC actually down?").

2.  **RAG Memory:**
    *   Uses **ChromaDB** to store news events and retrieve historical context for the AI.

3.  **AI Analysis:**
    *   Integrated with **Ollama** to run **Google Gemma 3**.
    *   **Robustness:** Includes a fallback mode to keep running even if the local LLM server is offline (returns "Neutral" sentiment with a warning).

4.  **Visualization:**
    *   Uses **Playwright** to capture live screenshots of TradingView charts (e.g., `BTCUSD`) to attach to tweets.

5.  **Infrastructure:**
    *   Full **Docker & Docker Compose** setup.

## **Technical Stack**
*   **Language:** Python 3.11
*   **Core Libs:** `chromadb`, `ollama`, `playwright`, `ntscraper`, `feedparser`, `requests`.
*   **Deployment:** Docker Compose (Service: `app` + connection to host Ollama).

## **File Structure**
*   `src/ingestion.py`: Handles RSS, Twitter scraping, Blockchain API, and CoinGecko.
*   `src/agent.py`: Interface to Ollama (Gemma 3) with error handling.
*   `src/memory.py`: Vector database logic (ChromaDB).
*   `src/visualizer.py`: Chart generation (Playwright).
*   `main.py`: Main orchestration loop.

## **How to Run**
1.  **Start Ollama:** `ollama serve` (Ensure `gemma3` model is pulled).
2.  **Run Bot (Docker):** `docker-compose up --build`
3.  **Run Bot (Manual):** `pip install -r requirements.txt && python main.py`
