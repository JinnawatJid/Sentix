import json
import re
import logging

logger = logging.getLogger("JsonUtil")

def parse_or_fix(raw_text, original_prompt=None):
    if not raw_text:
        return {}

    # Strip code fences
    clean_text = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(clean_text)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON Decode Error: {e}. Raw: {raw_text[:50]}...")
        return {}
