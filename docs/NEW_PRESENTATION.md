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
    *   *v2 (Last Update):* Event-driven, RAG Memory, Dashboard.
    *   *v2.1 (Current):* **Transparency & Trust**. Added Audit Logs, Deterministic Verification, and Traceability.
*   **Key Updates:**
    *   **Audit Log:** Full "Forensics" view to inspect AI decisions.
    *   **Deterministic Verification:** Code-based clustering (not just AI "vibes") to confirm news.
    *   **Decision Trace:** Every tweet is linked to the specific articles that triggered it.

### Slide 3: High-Level Architecture
*   **Visual:** Architecture Diagram.
    *   *Inputs:* X API, RSS Feeds, On-Chain APIs.
    *   *Filter:* **Clustering Algorithm** (Input Verification).
    *   *Core:* **BotController** (Orchestrator).
    *   *Brain:* **Gemini 1.5 Pro** (Reasoning) + **ChromaDB** (Long-term Memory).
    *   *Output:* X (Twitter) + **Audit Dashboard**.
*   **Key Concept:** The system doesn't just "repost"; it "investigates" using a multi-agent approach.

### Slide 4: Deep Dive - Ingestion & Verification (The "Fetch")
*   **Visual:** "The Funnel"
    *   Top: RSS Feeds (WatcherGuru, CoinDesk, Decrypt, TheBlock).
    *   Middle: **Deterministic Clustering** (Python `difflib`).
    *   Bottom: Verified Candidates (Score >= 2 Sources).
*   **Technical Highlight:**
    *   **Trust by Numbers:** We don't blindly trust the AI to pick a story. We implemented a **Clustering Algorithm** in Python that groups articles by similarity.
    *   **Consensus Rule:** A story is *only* eligible for analysis if it appears in at least **2 distinct sources**. This filters out rumors and single-source FUD (Fear, Uncertainty, Doubt).

### Slide 5: Deep Dive - Analysis & RAG Memory (The "Brain")
*   **Visual:** A circular loop: `News Event` -> `Search Memory` -> `Analyze` -> `Store Outcome`.
*   **Technical Highlight:**
    *   **RAG (Retrieval-Augmented Generation):** Before writing a tweet, the AI pulls similar *past* events from **ChromaDB**.
    *   *Example:* "Last time inflation was 5%, BTC dropped." -> AI uses this context to predict today's move.
    *   **Hallucination Check:** The AI is prompted to output a "Hallucination Check" list and must append **Citations** (e.g., `[Source: CoinDesk]`) to every claim.

### Slide 6: New Feature - Audit Log & Transparency (v2.1)
*   **Visual:** Screenshot of the new **/audit** page.
*   **Technical Highlight:**
    *   **The "Black Box" Problem:** Solved. We now store a `DecisionTrace` for every run.
    *   **What You See:** The exact input clusters, the calculated verification score, the AI's reasoning text, and the final output.
    *   **Accountability:** If the bot makes a mistake, we can trace it back to the specific logic step that failed.

### Slide 7: Localization & Scalability
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

**Slide 2: Evolution (v2.1 Update)**
"The biggest concern with AI bots is 'Trust'. How do we know it's not hallucinating? In this update (v2.1), we focused entirely on **Verification and Transparency**. We built an 'Audit Log' so we can see exactly *why* the AI made a decision."

**Slide 3: Architecture**
"Here is the high-level view. The core differentiator is the **Verification Layer**. Before the AI even sees the news, a deterministic algorithm groups stories and filters out unverified rumors. It's a 'Code-First, AI-Second' approach."

**Slide 4: Ingestion (Technical)**
"Technically, this is where we solved the 'Reliability' problem. Reliance on a single API (like Twitter) is dangerous. We implemented a 'Waterfall' ingestion system. If Twitter blocks us (Rate Limits), we instantly fall back to RSS feeds.
**NEW:** We implemented `IngestionModule.cluster_news()`. It uses text similarity to count how many sources are reporting the same story. Only stories with a 'Confidence Score' of 2 or higher pass to the next stage."

**Slide 5: The Brain (RAG)**
"This is the most exciting CS element: **Retrieval-Augmented Generation (RAG)**. Most bots are amnesiac—they treat every event as new. Sentix remembers. When 'CPI Data' is released, it checks its vector database: *'How did the market react last time?'* It includes that historical context in its analysis. This reduces hallucination and improves signal quality."

**Slide 6: Audit Log (New)**
"We also realized that 'Black Box' AI is hard to trust. So we built a full **Audit Dashboard**. We can see the exact 'Decision Trace': Inputs -> Logic -> Output. If the bot decides *not* to tweet, we see why (e.g., 'Verification Score too low')."

---

## 3. Technical Implementation Guide (For Q&A)

*Use this reference to point to specific code during the "Deep Dive" slides.*

### **A. Ingestion & Verification (The "Fetch")**
*   **File:** `src/ingestion.py`
*   **Class:** `IngestionModule`
*   **New Logic (v2.1):**
    *   `cluster_news(news_items)`: Uses `difflib.SequenceMatcher` to group similar titles. Calculates a `score` (count of unique sources).
    *   **Consensus:** The `fetch_news` function aggregates data, but `cluster_news` is the gatekeeper that validates it.

### **B. The Brain & RAG (The "Process" & "Learn")**
*   **File:** `src/agent.py` & `src/memory.py`
*   **Class:** `AnalysisAgent` & `MemoryModule`
*   **Logic:**
    *   `analyze_situation()`: Now accepts a **Verified Cluster** object. The prompt forces the AI to check facts against the provided text and append citations (`[Source: X]`).
    *   `MemoryModule.retrieve_context()`: Queries **ChromaDB** for similar past events.

### **C. Audit & Traceability (The "Log")**
*   **File:** `src/models.py` & `src/web/app.py`
*   **Class:** `DecisionTrace` (SQLAlchemy Model)
*   **Logic:**
    *   Every execution cycle creates a `DecisionTrace` record.
    *   Stores: `clusters_found` (Input), `verification_score` (Validation), `ai_reasoning` (Process), and `generated_tweet` (Output).
    *   **Frontend:** `src/web/templates/audit.html` visualizes this data.

---

## 4. Live Demo Walkthrough

**Setup:**
1.  Open the **Web Dashboard** (`http://localhost:8000`) in a browser.
2.  Click the new **"Audit Log"** link in the header.

**Steps:**
1.  **Show the Audit Log:** "Here is the new Audit View. You can see a history of every decision the bot has made."
2.  **Highlight Verification:** "Notice this entry marked 'VERIFIED'. It had a score of 3, meaning CoinDesk, WatcherGuru, and TheBlock all reported it."
3.  **Highlight Rejection:** "Now look at this 'SKIPPED' entry. The bot found a story about a Meme Coin, but it only appeared on Twitter. The Verification Score was 1, so the system blocked it automatically."
4.  **View Logic:** Click 'View Logic'. "We can inspect the internal reasoning of the AI to confirm it understood the context correctly."
