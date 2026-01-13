import json
from src.core.llm import call_llm
from src.core.jsonutil import parse_or_fix

def extract_facts(event, articles):
    prompt = f"""
You are a cross-source fact validation engine.

Your task is to extract ONLY verifiable facts that are confirmed by
AT LEAST TWO INDEPENDENT NEWS OUTLETS.

Each article contains a "source" field indicating the publisher.

Do NOT treat multiple articles from the same source as independent confirmation.

Event:
{json.dumps(event, indent=2)}

Articles:
{json.dumps(articles, indent=2)}

Rules:
- A fact must be stated (explicitly or implicitly) by at least two DIFFERENT sources.
- If only one source reports a claim, EXCLUDE it.
- If sources disagree, EXCLUDE the claim.
- Exclude opinions, analysis, speculation, and predictions.
- Extract only objective real-world facts.

Return ONLY valid JSON in this format:
{{
  "facts": [
    {{
      "fact": "clear, concise factual statement",
      "sources": ["sourceA", "sourceB"]
    }}
  ],
  "confidence": 0.0-1.0
}}

Where confidence is:
(number of independent sources that agree on the core event) 
divided by 
(total number of independent sources that reported on this event)
"""
    raw = call_llm(prompt)
    data = parse_or_fix(raw, prompt)

    # unwrap if list
    if isinstance(data, list):
        data = data[0]

    # enforce schema
    if not isinstance(data, dict):
        return {"facts": [], "confidence": 0}

    if "facts" not in data:
        data["facts"] = []

    if "confidence" not in data:
        data["confidence"] = 0

    return data

