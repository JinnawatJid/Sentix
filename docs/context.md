# 🚀 Project Summary: Sentix (AI-Driven Crypto News Bot) v2.1

> **Use this file to restore context in future AI sessions.**

## **Overview**
Sentix is a RAG-based automated bot that fetches real-time crypto news, verifies it with live on-chain/market data, analyzes sentiment using the **Google Gemini API**, and generates visual trading charts for X (Twitter).

## **Key Features Implemented**
1.  **Strict Verification Pipeline (v2.1):**
    *   **Ingestion:** Fetches news exclusively from 5 high-quality RSS feeds (WatcherGuru, CoinDesk, etc.), fetching 5 items per feed.
    *   **Event Resolution:** Uses AI to group articles describing the same real-world event, *anonymizing sources first* to prevent bias.
    *   **Fact Extraction:** Extracts atomic facts only if verified by at least **2 Independent Sources**.
    *   **Critic Loop:** A secondary AI step that fact-checks the generated tweet against verified facts to prevent hallucinations.

2.  **RAG Memory:**
    *   Uses **ChromaDB** to store news events and retrieve historical context for the AI.

3.  **AI Analysis:**
    *   Integrated with **Google Gemini API** (`gemini-2.0-flash-exp`) for fast, cost-effective sentiment analysis and tweet generation.
    *   **Robustness:** Includes error handling for API failures and a "Critic" self-correction loop.

4.  **Visualization:**
    *   Uses **Playwright** to capture live screenshots of TradingView charts (e.g., `BTCUSD`) to attach to tweets.

5.  **Dashboard & Audit:**
    *   **FastAPI** dashboard (`src/web/app.py`) for monitoring bot status.
    *   **Audit Log:** Tracks every decision trace, including source verification scores, AI reasoning, and original input clusters.

6.  **Infrastructure:**
    *   Full **Docker & Docker Compose** setup.

## **Technical Stack**
*   **Language:** Python 3.12+
*   **Core Libs:** `google-genai`, `tweepy`, `chromadb`, `playwright`, `feedparser`, `requests`, `schedule`, `fastapi`, `sqlalchemy`.
*   **Deployment:** Docker Compose.

## **File Structure**
*   `src/ingestion.py`: Orchestrates the Pipeline (Fetch -> Resolve -> Verify).
*   `src/events.py`: AI logic for resolving raw news into events.
*   `src/facts.py`: AI logic for extracting verified facts from events.
*   `src/agent.py`: Interface to Google Gemini API (Analysis + Critic Loop).
*   `src/memory.py`: Vector database logic (ChromaDB).
*   `src/visualizer.py`: Chart generation (Playwright).
*   `src/web/app.py`: Main orchestration loop and Web Dashboard.
*   `tests/`: Contains test scripts (Pipeline Flow, Agent Logic).

## **How to Run**
1.  **Setup Environment:**
    *   Follow instructions in `SETUP.md` to obtain API keys (`GEMINI_API_KEY`, `TWITTER_*`).
    *   Create a `.env` file.
2.  **Run Tests:**
    *   **Pipeline Test:** `python tests/test_pipeline.py`
3.  **Start Bot:**
    *   **Docker:** `docker-compose up --build`
    *   **Manual:** `run_dashboard.bat` (Windows) or `./run_dashboard.sh` (Mac/Linux).
