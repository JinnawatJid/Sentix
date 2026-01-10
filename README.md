# Sentix - AI-Driven Crypto News Bot (v1.0 Live Prototype)

Sentix is a RAG-based automated bot that fetches **real-time crypto news**, verifies it with **live on-chain data**, and publishes sentiment analysis with visual charts to X (Twitter).

## Features
- **Real-time News Ingestion**: 
    - Fetches latest updates from **CoinDesk RSS**.
    - Scrapes **Twitter (X)** for latest tweets from @WatcherGuru (via Nitter).
- **On-Chain Verification (Whale Alert)**:
    - Scrapes @whale_alert tweets.
    - **Fallback**: Automatically queries **Blockchain.info** for live unconfirmed large transactions (> 10 BTC) if Twitter is down.
- **Market Data Verification**:
    - Validates price movements using **CoinGecko API** (e.g., "Is BTC actually down?").
- **RAG Memory**: Uses **ChromaDB** to store and retrieve historical news context.
- **AI Analysis**: Uses **Google Gemini** (via Google GenAI API) to synthesize all data points and generate viral tweets.
- **Visuals**: Auto-generates **TradingView** chart screenshots using Playwright.

## Prerequisites
1. **Docker & Docker Compose**
2. **Google Gemini API Key** (Get it from [Google AI Studio](https://aistudio.google.com/)).
3. **Twitter (X) API Keys** (Consumer Key/Secret, Access Token/Secret, Bearer Token).

## Setup Instructions

### 1. Configure Environment Variables
Create a `.env` file in the root directory with your API keys:

```bash
# .env

# Google AI
GEMINI_API_KEY=your_gemini_key_here

# Twitter / X API
TWITTER_BEARER_TOKEN=your_bearer_token_here
TWITTER_CONSUMER_KEY=your_consumer_key_here
TWITTER_CONSUMER_SECRET=your_consumer_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
```

### 2. Run Sentix with Docker
The easiest way to run the bot is via Docker Compose.

```bash
# Build and run
docker-compose up --build
```

### 3. Manual Installation (Python)
If you prefer running without Docker:

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run the bot
python main.py
```

## Configuration
- **Twitter Scraping**: Uses `ntscraper` which relies on public Nitter instances. If scraping fails, the bot automatically falls back to RSS and Blockchain APIs.
- **Model**: Edit `src/agent.py` if you wish to change the specific Gemini model version (default: `gemini-3-flash-preview`).

## Project Structure
- `src/ingestion.py`: **Live Data Module** (RSS, Twitter Scraper, Blockchain API, CoinGecko).
- `src/memory.py`: ChromaDB vector store for RAG.
- `src/agent.py`: Interface to Google Gemini (LLM).
- `src/visualizer.py`: Generates chart screenshots.
- `main.py`: Main execution loop.
