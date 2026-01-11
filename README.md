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
- **AI Analysis**: Uses **Google Gemma 3** (via Ollama) to synthesize all data points and generate viral tweets.
- **Visuals**: Auto-generates **TradingView** chart screenshots using Playwright.

## Prerequisites
1. **Docker & Docker Compose**
2. **Ollama** installed locally (or on a remote server).
3. **Google Gemma 3** model pulled in Ollama.

## Setup Instructions

### 1. Install & Configure Ollama
You need to have Ollama running and the `gemma3` model available.

```bash
# Install Ollama (Linux/Mac)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model
ollama pull gemma3

# Start the server (if not running)
ollama serve
```

### 2. Run Sentix with Docker
The easiest way to run the bot is via Docker Compose.

```bash
# Build and run
docker-compose up --build
```

**Note:** The `docker-compose.yml` is configured to talk to Ollama on your host machine via `host.docker.internal:11434`.

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
- **Model**: Edit `src/agent.py` to change `gemma3` to another model.

## Project Structure
- `src/ingestion.py`: **Live Data Module** (RSS, Twitter Scraper, Blockchain API, CoinGecko).
- `src/memory.py`: ChromaDB vector store for RAG.
- `src/agent.py`: Interface to Ollama (LLM).
- `src/visualizer.py`: Generates chart screenshots.
- `main.py`: Main execution loop.
