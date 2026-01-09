# Sentix: Autonomous AI-Driven Crypto Intelligence
## Progress Update & Technical Deep Dive

---

## 1. Presentation Outline

### Slide 1: Title & Vision
*   **Visual:** Split screen: "Noisy Twitter Feed" vs. "Verified Sentix Signal".
*   **Title:** Sentix: From "News Bot" to "Autonomous Intelligence".
*   **Subtitle:** Real-time Verification, RAG Memory, and Multi-Modal Analysis.
*   **Presenter:** [Your Name]

### Slide 2: The Evolution (System State)
*   **Visual:** A "Before vs. After" comparison.
    *   *v1:* Simple Python script, Linear execution, Text-only.
    *   *Current (v2):* Event-driven Architecture, Web Dashboard, Dockerized, Multi-Language, Vector Memory.
*   **Key Updates:**
    *   **Web Dashboard:** Full UI for monitoring and control.
    *   **Localization:** Native support for global markets (e.g., Thai/English).
    *   **Resilience:** Advanced fallback systems (Twitter -> RSS -> Blockchain).

### Slide 3: High-Level Architecture
*   **Visual:** Architecture Diagram.
    *   *Inputs:* X API, RSS Feeds, On-Chain APIs.
    *   *Core:* **BotController** (Orchestrator).
    *   *Brain:* **Gemini 1.5 Pro** (Reasoning) + **ChromaDB** (Long-term Memory).
    *   *Output:* X (Twitter) + Web Dashboard + Logs.
*   **Key Concept:** The system doesn't just "repost"; it "investigates" using a multi-agent approach.

### Slide 4: Deep Dive - Ingestion & Verification (The "Fetch")
*   **Visual:** "The Funnel"
    *   Top: Raw Tweets, RSS Feeds (Noise).
    *   Middle: Cross-Verification Logic (Filter).
    *   Bottom: Verified Candidates (Signal).
*   **Technical Highlight:**
    *   **Hybrid Ingestion:** If Twitter Rate Limits (429) hit, system seamlessly switches to CoinDesk/Decrypt RSS.
    *   **Truth Verification:** We don't trust text. We verify with **Numbers** (CoinGecko Price) and **Chain Data** (Whale transactions via Blockchain.info).

### Slide 5: Deep Dive - Analysis & RAG Memory (The "Brain")
*   **Visual:** A circular loop: `News Event` -> `Search Memory` -> `Analyze` -> `Store Outcome`.
*   **Technical Highlight:**
    *   **RAG (Retrieval-Augmented Generation):** Before writing a tweet, the AI pulls similar *past* events from **ChromaDB**.
    *   *Example:* "Last time inflation was 5%, BTC dropped." -> AI uses this context to predict today's move.
    *   **Cross-Verification Prompting:** The LLM is explicitly instructed to REJECT stories that appear in only one source.

### Slide 6: New Feature - Web Dashboard & Monitoring
*   **Visual:** Screenshot of the new Dashboard (Traffic light status, Logs, Engagement Charts).
*   **Technical Highlight:**
    *   **Tech Stack:** FastAPI (Backend) + Jinja2/Tailwind (Frontend) + Chart.js.
    *   **Real-time Control:** Manual trigger overrides, live log streaming, and sentiment distribution stats.

### Slide 7: New Feature - Localization & Scalability
*   **Visual:** Two tweets side-by-side: One in English, one in Thai.
*   **Technical Highlight:**
    *   **Configurable Persona:** The AI adapts its tone ("Crypto Native") and language based on `config.json`.
    *   **Scalability:** Stateless Docker containers allow running multiple instances for different languages or coins simultaneously.

### Slide 8: Live Demo
*   (Placeholder for live interaction - see "Demo Walkthrough" section below)

### Slide 9: Roadmap & Conclusion
*   **Future:**
    *   **Agentic Trading:** Moving from "Analysis" to "Execution" (Paper trading wallet).
    *   **Multi-Platform:** Telegram/Discord integration.
*   **Closing:** Sentix is now a robust, verifiable, and scalable intelligence platform.

---

## 2. Speaker Script & Talking Points

**Slide 1: Intro**
"Good morning. Today I'm presenting the latest evolution of Sentix. We've moved beyond a simple news bot. Sentix is now an autonomous intelligence agent that verifies, remembers, and visualizes market data in real-time."

**Slide 2: Evolution**
"Since our last update, we've matured the engineering significantly. We moved from a fragile script to a robust platform. We added a **Web Dashboard** for visibility, **Localization** to reach global audiences, and a **Memory Module** so the AI learns from its past predictions."

**Slide 3: Architecture**
"Here is the high-level view. The core differentiator is the **Analysis Agent**. It doesn't just summarize; it acts as a detective. It ingests data, queries its long-term memory (ChromaDB), checks on-chain stats, and only then formulates a conclusion."

**Slide 4: Ingestion (Technical)**
"Technically, this is where we solved the 'Reliability' problem. Reliance on a single API (like Twitter) is dangerous. We implemented a 'Waterfall' ingestion system. If Twitter blocks us (Rate Limits), we instantly fall back to RSS feeds. If the 'Whale Alert' bot is down, we query the Bitcoin blockchain directly. The system always finds a way to get the truth."

**Slide 5: The Brain (RAG)**
"This is the most exciting CS element: **Retrieval-Augmented Generation (RAG)**. Most bots are amnesiac—they treat every event as new. Sentix remembers. When 'CPI Data' is released, it checks its vector database: *'How did the market react last time?'* It includes that historical context in its analysis. This reduces hallucination and improves signal quality."

**Slide 6: Dashboard**
"We also realized that 'Black Box' AI is hard to trust. So we built a full FastAPI Dashboard. We can see exactly what the bot is thinking, view the raw logs, and manually trigger runs. It gives us full observability."

**Slide 7: Localization**
"Finally, we made the system global. With a simple config change, the AI changes its entire persona and language—for example, switching to a 'Thai Crypto Native' persona—while maintaining the same rigorous verification logic."

---

## 3. Technical Implementation Guide (For Q&A)

*Use this reference to point to specific code during the "Deep Dive" slides.*

### **A. Ingestion & Fallbacks (The "Fetch")**
*   **File:** `src/ingestion.py`
*   **Class:** `IngestionModule` & `WhaleMonitor`
*   **Logic:**
    *   `fetch_news()`: Orchestrates the "Twitter first, RSS second" priority.
    *   `TwitterClient.fetch_tweets()`: Contains the `try/except` block for `tweepy.errors.TooManyRequests` (429).
    *   `WhaleMonitor.get_whale_movements()`: Shows the fallback from `@whale_alert` (Twitter) to `blockchain.info` (Raw API).

### **B. The Brain & RAG (The "Process" & "Learn")**
*   **File:** `src/agent.py` & `src/memory.py`
*   **Class:** `AnalysisAgent` & `MemoryModule`
*   **Logic:**
    *   `analyze_situation()` (`src/agent.py`): The prompt explicitly asks the LLM to verify "Candidate Stories" against "Context Stories".
    *   `MemoryModule.retrieve_context()`: Queries **ChromaDB** for similar past events.
    *   `store_news_event()`: Called *after* a successful tweet to save the "Knowledge Base Entry" (closing the learning loop).

### **C. Orchestration & State (The "Controller")**
*   **File:** `src/web/app.py`
*   **Class:** `BotController`
*   **Logic:**
    *   `run_cycle()`: The main loop. It fetches -> checks DB for duplicates -> verifies -> analyzes -> tweets -> saves to memory.
    *   **Database:** Uses `SQLAlchemy` (in `src/database.py`) to persist `ProcessedNews` and `BotLog`.

### **D. Visualization & Dashboard**
*   **File:** `src/web/app.py` (Backend) & `src/web/templates/index.html` (Frontend)
*   **Tech:** FastAPI, Jinja2, Chart.js.
*   **Logic:**
    *   `/api/logs`: Streams live logs from the `BotLog` database table.
    *   `/api/control/run`: Allows the user to trigger `bot_controller.run_cycle()` via a background task.

---

## 4. Live Demo Walkthrough

**Setup:**
1.  Open the **Web Dashboard** (`http://localhost:8000`) in a browser.
2.  Have the terminal open showing the docker logs (optional, for "Matrix" effect).

**Steps:**
1.  **Show the Status:** "As you can see, the bot is currently 'Idle' and waiting for its next scheduled run."
2.  **Review Logs:** Scroll through the 'System Logs' panel. "Here we can see previous decisions. Notice how it skipped this story because it couldn't cross-verify it."
3.  **Manual Trigger:** Click the **"Run Now"** button.
4.  **Watch it Work:**
    *   Observe the Status change to **"Running..."**.
    *   Refresh the logs to see: `Fetching news...`, `Analyzing...`, `Generating Chart...`.
5.  **The Result:** "Once finished, we see the new Tweet ID and the updated Sentiment Distribution chart reflecting the latest market mood."
