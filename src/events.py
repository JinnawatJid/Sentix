import json
from src.core.llm import call_llm
from src.core.jsonutil import parse_or_fix

def resolve_events(articles):
    prompt = f"""
You are a JSON API.

Return ONLY valid JSON.
No explanation. No markdown.

Your job is to group news articles into REAL-WORLD EVENTS.

Definition of SAME EVENT:
Articles must describe the SAME concrete real-world occurrence:
- same organization(s)
- same specific action
- same object (ETF, lawsuit, hack, listing, regulation, etc)
- same timeframe (within 24 hours)

They must NOT be grouped if they are only:
- about the same topic
- about the same company but different actions
- an analysis, opinion, or market reaction to another event

IMPORTANT SOURCE RULES:
- Articles from DIFFERENT news outlets reporting the same occurrence SHOULD be grouped together.
- Multiple versions, rewrites, or updates from the SAME outlet about the same occurrence should still be included, but they do NOT count as independent confirmation.
- Do NOT group articles just because they come from the same source. Group ONLY if they describe the same real-world event.

You must think in terms of: "Did these articles report the same thing actually happening?"

Articles:
{json.dumps(articles, indent=2)}

Return a JSON array in this exact format:
[
  {{
    "event_id": "short stable identifier based on organization + action + date",
    "title": "clear factual description of what happened",
    "articles": ["id1", "id2", "id3"]
  }}
]
"""
    raw = call_llm(prompt)
    return parse_or_fix(raw, prompt)

