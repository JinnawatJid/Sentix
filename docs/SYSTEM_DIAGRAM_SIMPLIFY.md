# Simplified System Architecture

This document provides a high-level developer overview of the Sentix system (v2.1).
For the detailed component interaction view, see [SYSTEM_DIAGRAM.md](./SYSTEM_DIAGRAM.md).

```mermaid
flowchart LR
    %% Global Styles
    classDef source fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef process fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;
    classDef storage fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef ai fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef output fill:#ffebee,stroke:#c62828,stroke-width:2px;

    %% ---------------------------------------------------------
    %% 1. Data Sources
    %% ---------------------------------------------------------
    subgraph Sources ["External Sources"]
        direction TB
        RSS["RSS Feeds"]:::source
        Whale["Whale Monitor"]:::source
        Market["Market Data"]:::source
    end

    %% ---------------------------------------------------------
    %% 2. Ingestion Service
    %% ---------------------------------------------------------
    subgraph Ingestion ["Ingestion Service"]
        direction TB
        Pipe["Pipeline Orchestrator<br/>(Fetch &rarr; Cluster &rarr; Verify)"]:::process
    end

    %% ---------------------------------------------------------
    %% 3. Intelligence Core
    %% ---------------------------------------------------------
    subgraph Core ["Analysis Core"]
        direction TB
        Agent("Analysis Agent<br/>(Central Logic)"):::ai

        %% Satellites
        Gemini["Gemini 3 Flash<br/>(LLM)"]:::ai
        RAG[("ChromaDB<br/>(Context)")]:::storage
        Critic["Critic Loop<br/>(Safety)"]:::ai
    end

    %% ---------------------------------------------------------
    %% 4. Outputs
    %% ---------------------------------------------------------
    subgraph Outputs ["Endpoints"]
        direction TB
        X["Twitter / X API"]:::output
        Audit["Audit Dashboard<br/>(Decision Traces)"]:::output
    end

    %% Flow Connections
    RSS & Whale & Market --> Pipe
    Pipe -->|"Verified Events"| Agent

    %% Core Internal Connections
    Agent <--> RAG
    Agent <--> Gemini
    Agent <--> Critic

    %% Output Connections
    Agent -->|"Publish"| X
    Agent -->|"Log"| Audit
```

## Diagram Explanation

*   **Ingestion Service**: Consolidates raw data fetching, event resolution (clustering), and fact verification into a single automated pipeline. Only verified, high-confidence events are passed downstream.
*   **Analysis Core**: The **Analysis Agent** acts as the central brain. It queries **ChromaDB** for historical context, sends prompts to **Gemini** for reasoning, and runs a **Critic Loop** to self-correct before finalizing content.
*   **Endpoints**: The system has two distinct outputs:
    1.  **Public**: Posts to Twitter/X.
    2.  **Internal**: Logs comprehensive decision traces to the Audit Dashboard for transparency.
