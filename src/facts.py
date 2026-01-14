import json
from src.core.llm import call_llm
from src.core.jsonutil import parse_or_fix

def extract_facts(event, articles):
    # Wrapper for legacy single calls, redirects to batch
    # We wrap the single event in a list structure for the batch function
    batch_input = [{
        "event_id": event.get("event_id", "single_event"),
        "title": event.get("title"),
        "articles": articles
    }]

    batch_result = extract_facts_batch(batch_input)

    # Return result for this specific event or default
    return batch_result.get(event.get("event_id", "single_event"), {"facts": [], "confidence": 0})

def extract_facts_batch(events_data):
    """
    Batch processes multiple events for fact extraction.
    events_data: List of dicts, each containing:
      - event_id
      - title
      - articles (list of full article objects)
    """
    if not events_data:
        return {}

    # Minimize token usage by sending only necessary fields
    minimized_data = []
    for item in events_data:
        minimized_data.append({
            "id": item.get("event_id"),
            "event": item.get("title"),
            "articles": [
                {"s": a.get("source"), "t": a.get("title"), "d": a.get("summary", "")[:200]}
                for a in item.get("articles", [])
            ]
        })

    prompt = f"""
You are a cross-source fact validation engine.

Your task is to extract verifiable facts for MULTIPLE events.

For each event provided in the list:
1. Identify the core facts reported in the articles.
2. If multiple sources report the same fact, list them.
3. If only one source reports a fact, include it (Single Source is allowed).
4. Calculate a "confidence" score (0.0 - 1.0) based on source diversity.

Rules:
- Fact Format: "clear, concise factual statement"
- Exclude opinions and pure speculation.
- Return a JSON object where KEYS are the 'id' of the event.

Input Data:
{json.dumps(minimized_data, indent=2)}

Return ONLY valid JSON in this format:
{{
  "event_id_1": {{
    "facts": [
      {{
        "fact": "Statement here",
        "sources": ["SourceA", "SourceB"]
      }}
    ],
    "confidence": 1.0
  }},
  "event_id_2": {{
    "facts": [],
    "confidence": 0.5
  }}
}}
"""
    raw = call_llm(prompt)
    data = parse_or_fix(raw, prompt)

    if not isinstance(data, dict):
        return {}

    return data
