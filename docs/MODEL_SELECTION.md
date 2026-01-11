# Architecture Decision Record: LLM Selection for Sentix

## 1. Context and Problem Statement
The **Sentix** system requires a Large Language Model (LLM) to perform real-time sentiment analysis, summarization, and verification of cryptocurrency news clusters. The system operates on a scheduled interval (every 4 hours) and must process multiple potential news clusters rapidly.

The key constraints for the project are:
1.  **Cost Efficiency:** As an academic/student project, minimizing operational costs (OpEx) is critical.
2.  **Latency:** The "time-to-tweet" must be minimized to maintain relevance in the fast-moving crypto market.
3.  **Context Window:** The model must handle Retrieval Augmented Generation (RAG) contexts, including historical logs and multiple news articles.
4.  **Availability:** The API must have a reliable uptime and generous rate limits for development.

**Candidate Models Evaluated:**
*   **Google Gemini 2.0 Flash (via Gemini 1.5/3 Preview APIs):** Google's high-efficiency, multimodal model.
*   **OpenAI GPT-4o:** The industry standard for reasoning capabilities.
*   **DeepSeek V3:** A rising competitor known for strong reasoning at a lower cost than OpenAI.

## 2. Comparative Analysis

The following table compares the models based on public benchmarks and API specifications (as of Late 2024/Early 2025):

| Feature | **Google Gemini Flash** (Selected) | OpenAI GPT-4o | DeepSeek V3 |
| :--- | :--- | :--- | :--- |
| **Cost (Dev/Free Tier)** | **Free of Charge** (via Google AI Studio) | Paid (Tokens) | Paid (Tokens) |
| **Avg. Latency** | **~600-800ms** | ~2000-3000ms | ~1500-2500ms |
| **Context Window** | **1 Million Tokens** | 128k Tokens | 64k - 128k Tokens |
| **Rate Limits** | High (15 RPM free tier) | Variable (Tier-based) | Variable |
| **Reasoning Capability** | High (Sufficient for Sentiment) | Very High | High |

## 3. Decision Justification

### Why Gemini was selected:

1.  **Speed (Latency):**
    For a trading-adjacent news bot, speed is paramount. Gemini Flash is architected specifically for high-throughput, low-latency tasks. In our internal tests, it consistently outperforms GPT-4o in simple summarization and classification tasks by a factor of 2-3x.

2.  **Cost (The "Student" Factor):**
    Google AI Studio provides a generous free tier that allows for extensive testing, debugging, and continuous operation without incurring credit card charges. OpenAI and DeepSeek require prepaid credits, which introduces friction and budget risk for an academic project.

3.  **Long Context Window:**
    Gemini's 1M token window allows us to pass massive amounts of "context" (historical price data, previous decisions, full article text) without complex chunking strategies. This simplifies the codebase significantly.

## 4. Architectural Flexibility

While Gemini is the current driver, the system architecture is designed to be **Model Agnostic**. The `AnalysisAgent` is decoupled from the core application logic.

We have implemented a `Provider` pattern (demonstrated in `research/llm_benchmark.py`) that allows the system to switch to OpenAI or DeepSeek by simply changing an environment variable and the adapter class, should the need verify higher-order reasoning capabilities in the future.

## 5. Conclusion
Gemini offers the best intersection of **Performance**, **Cost**, and **Ease of Implementation** for the Sentix use case. Switching to a heavier model like GPT-4o would increase costs and latency with diminishing returns on sentiment accuracy.
