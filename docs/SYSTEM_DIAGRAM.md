# System Overview Diagram

This document contains the high-level architecture diagram for the Sentix system (v2.1).
It is written in **Mermaid.js**, which renders automatically in GitHub.

```mermaid
flowchart TD
    %% Global Styles
    classDef source fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef process fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;
    classDef storage fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef ai fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef output fill:#ffebee,stroke:#c62828,stroke-width:2px;

    %% ---------------------------------------------------------
    %% 1. Data Sources Layer
    %% ---------------------------------------------------------
    subgraph Sources ["Data Sources (External)"]
        direction TB
        RSS["RSS Feeds<br/>(WatcherGuru, CoinDesk, etc.)"]:::source
        Whale["Whale Monitor<br/>(Blockchain.info)"]:::source
        Market["Market Data<br/>(CoinGecko)"]:::source
    end

    %% ---------------------------------------------------------
    %% 2. Ingestion & Verification Layer
    %% ---------------------------------------------------------
    subgraph Ingestion ["Ingestion & Verification Layer"]
        direction TB
        Ingest["IngestionModule<br/>(Fetch & Normalize)"]:::process
        Cluster["Event Resolution<br/>(Clustering & Anonymization)"]:::process
        Verify["Fact Extraction<br/>(Batch Verification)"]:::process

        %% Logic Connections
        RSS --> Ingest
        Whale --> Ingest
        Market --> Ingest
        Ingest --> Cluster
        Cluster -->|"Group Similar Articles"| Verify
    end

    %% ---------------------------------------------------------
    %% 3. Intelligence Core (AI & Memory)
    %% ---------------------------------------------------------
    subgraph Core ["Intelligence Core"]
        direction TB
        RAG[("ChromaDB<br/>RAG Memory")]:::storage
        Agent["AnalysisAgent<br/>(Orchestrator)"]:::ai
        Gemini["Gemini 3 Flash<br/>(LLM Inference)"]:::ai
        Critic["Critic Loop<br/>(Self-Correction)"]:::ai

        %% Logic Connections
        Verify -->|"Verified Events"| Agent
        Agent <-->|"Retrieve Context"| RAG
        Agent -->|"Prompt"| Gemini
        Gemini -->|"Draft Tweet"| Agent
        Agent -->|"Review Draft"| Critic
        Critic -->|"Approved / Rewritten"| Agent
    end

    %% ---------------------------------------------------------
    %% 4. Output Layer
    %% ---------------------------------------------------------
    subgraph Outputs ["Presentation & Output"]
        direction TB
        Twitter["Twitter / X API<br/>(Post Only)"]:::output
        Dashboard["Audit Dashboard<br/>(/audit & /config)"]:::output
        Logs[("Decision Trace<br/>(Audit Logs)")]:::storage

        %% Logic Connections
        Agent -->|"Publish"| Twitter
        Agent -->|"Log Decision"| Logs
        Logs --> Dashboard
    end

    %% Key Relationships
    Verify -.->|"Filter Unverified"| Agent
```

## Diagram Explanation

1.  **Data Sources**: The system pulls raw data from RSS feeds, on-chain whale alerts, and market price APIs.
2.  **Ingestion & Verification**:
    *   **Event Resolution**: Groups related articles to identify unique real-world events.
    *   **Fact Extraction**: Verifies facts by ensuring multiple sources report the same information.
3.  **Intelligence Core**:
    *   **Gemini 3 Flash**: The primary LLM used for analyzing sentiment and generating content.
    *   **RAG Memory**: Retrieves historical context (e.g., "How did BTC react to similar CPI data last time?").
    *   **Critic Loop**: A secondary AI check to prevent hallucinations before posting.
4.  **Output**:
    *   **Twitter**: Final posts are sent to X.
    *   **Audit Dashboard**: Every step is logged for transparency, allowing users to trace the AI's decision-making process.
