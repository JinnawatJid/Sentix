from google import genai
from google.genai import types
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("AnalysisAgent")

# Localization Configuration
LOCALIZATION = {
    "en": {
        "headers": {
            "summary": "📰 Consensus",
            "impact": "🧠 Impact",
            "sentiment": "🚀 Outlook"
        },
        "fallback": "📰 Consensus: Market movement detected.\n\n🧠 Impact: Analyzing on-chain data.\n\n🚀 Outlook: NEUTRAL 🤖\n\n#Bitcoin #Crypto #Sentix",
        "prompt_instruction": "Ensure the tweet is in English. Use a professional but engaging crypto-native persona."
    },
    "th": {
        "headers": {
            "summary": "📢 ข่าวกรอง",
            "impact": "🧠 วิเคราะห์ผลกระทบ",
            "sentiment": "🚀 แนวโน้ม"
        },
        "fallback": "📢 ข่าวกรอง: ตรวจพบความเคลื่อนไหวของตลาด\n\n🧠 วิเคราะห์ผลกระทบ: กำลังวิเคราะห์ข้อมูล On-chain\n\n🚀 แนวโน้ม: เป็นกลาง (NEUTRAL) 🤖\n\n#Bitcoin #Crypto #Sentix",
        "prompt_instruction": "Translate the tweet content to Thai. Use a 'Crypto-Native' persona (engaging, insightful, slang allowed but professional). Explicitly state the Confidence Score (level of cross-verification) in the first section. Focus on the impact."
    }
}

class AnalysisAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        self.language = "en"  # Default
        self.critic_enabled = True # Default

        # Load Configuration
        self._load_config()

        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables. AI analysis will fail.")
        else:
            try:
                # Use v1alpha for experimental models
                self.client = genai.Client(
                    api_key=self.api_key,
                    http_options=types.HttpOptions(api_version='v1alpha')
                )
            except Exception as e:
                 logger.error(f"Failed to initialize Gemini Client: {e}")

    def _load_config(self):
        """Loads configuration from config.json"""
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.language = config.get("language", "en")
                    self.critic_enabled = config.get("critic_enabled", True)

                    if self.language not in LOCALIZATION:
                        logger.warning(f"Language '{self.language}' not supported. Defaulting to 'en'.")
                        self.language = "en"
            else:
                logger.info("config.json not found. Defaulting to defaults.")
        except Exception as e:
            logger.error(f"Error loading config.json: {e}. Using defaults.")

    def analyze_situation(self, verified_event, whale_data, historical_context):
        """
        Analyzes a SINGLE VERIFIED EVENT.
        Input `verified_event` is a dict from IngestionModule.process_pipeline containing:
        - title, facts, confidence, sources, items, etc.
        """
        if not self.client:
             return self._fallback_response("Missing API Key or Client Initialization Failed")

        loc = LOCALIZATION.get(self.language, LOCALIZATION["en"])
        headers = loc["headers"]
        prompt_instruction = loc["prompt_instruction"]

        # 1. Format Event Data from Input
        topic = verified_event.get('title', 'Unknown Topic')
        score = verified_event.get('source_count', 0)
        sources = verified_event.get('sources', [])
        facts = verified_event.get('facts', [])

        # Prepare Facts Text for Prompt
        facts_text = ""
        for f in facts:
            facts_text += f"- {f['fact']} (Verified by {', '.join(f['sources'])})\n"

        # Fallback if no facts (shouldn't happen if pipeline worked, but safe to keep items)
        if not facts_text:
            for i, item in enumerate(verified_event.get('items', [])):
                facts_text += f"- Article {i+1}: {item.get('title')} - {item.get('summary')}\n"

        # 2. Construct Main Prompt
        prompt = f"""
        You are 'Sentix', an elite crypto sentiment analyst AI.
        
        TASK: Analyze this VERIFIED EVENT to generate a trusted trading signal.
        
        **EVENT:**
        Topic: {topic}
        Consensus Score: {score} Sources (Sources: {', '.join(sources)})
        
        **VERIFIED FACTS:**
        {facts_text}
        
        **ADDITIONAL CONTEXT:**
        Whale Data: "{whale_data}"
        Historical RAG Context: "{historical_context}"
        
        INSTRUCTIONS:
        1. **Fact Checking & Citations:**
           - Base your analysis STRICTLY on the "Verified Facts".
           - **CRITICAL:** You MUST append a short citation for your main claims, e.g. "Bitcoin hits $100k [Source: CoinDesk]".

        2. **Synthesis & Persona:**
           - Adopt a **Crypto-Native Persona**: Be sharp, insightful, and engaging. Avoid robotic language.
           - Explicitly state the "Consensus Level" based on the Verification Score ({score} sources).

        3. **Analysis:**
           - Determine the sentiment (BULLISH, BEARISH, or NEUTRAL).
           - Focus on the **IMPACT** (Why this matters for price/market).
           - Generate a "Knowledge Base Entry" (RAG Context).
           - {prompt_instruction}
        
        TWEET FORMAT:
        {headers['summary']}: [Synthesized Event] (Verified by {score} sources)

        {headers['impact']}: [Deep analysis of impact + Citations]

        {headers['sentiment']}: [BULLISH/BEARISH/NEUTRAL] [Engaging closing line]

        (Ensure total length < 280 chars. Use hashtags like #BTC #Crypto #Sentix at the end.)

        OUTPUT FORMAT (JSON):
        {{
            "sentiment": "BULLISH/BEARISH/NEUTRAL",
            "reasoning": "Explain your synthesis of the cluster.",
            "tweet": "The formatted tweet string.",
            "knowledge_base_entry": "The long RAG memory sentence.",
            "hallucination_check": ["List", "of", "key", "facts", "claimed"]
        }}
        
        Respond ONLY with the JSON string.
        """
        
        try:
            # Generate Initial Draft
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt
            )
            initial_json = response.text

            # 3. Critic Loop (Self-Correction)
            if self.critic_enabled:
                final_json = self._critic_loop(initial_json, facts_text, prompt)
                return final_json

            return initial_json

        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            return self._fallback_response(str(e))

    def _critic_loop(self, draft_json_str, facts_text, original_prompt):
        """
        Critic Option B: Validates the generated tweet against verified facts.
        """
        logger.info("Running Critic Loop...")
        try:
            # Parse Draft
            clean_json = draft_json_str.replace("```json", "").replace("```", "").strip()
            draft = json.loads(clean_json)
            tweet = draft.get("tweet", "")
        except Exception as e:
            logger.warning(f"Critic failed to parse draft: {e}")
            return draft_json_str

        critic_prompt = f"""
        You are a STRICT FACT-CHECKING CRITIC.

        VERIFIED FACTS (The Truth):
        {facts_text}

        DRAFT TWEET (To Check):
        {tweet}

        TASK:
        1. Compare the tweet against the Verified Facts.
        2. Check for HALLUCINATIONS (claims not in facts) or Exaggerations.
        3. If the tweet is 100% supported by facts, return ONLY the string "PASS".
        4. If there are errors, REWRITE the tweet to be accurate and engaging.

        OUTPUT:
        If PASS: "PASS"
        If FAIL: Return ONLY the rewritten tweet text.
        """

        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=critic_prompt
            )
            critique = response.text.strip()

            if "PASS" in critique:
                logger.info("Critic passed the tweet.")
                return draft_json_str
            else:
                logger.warning("Critic rewrote the tweet.")
                # Update the tweet in the draft JSON
                draft['tweet'] = critique
                # Update reasoning note
                draft['reasoning'] += " (Refined by Critic)"
                return json.dumps(draft)

        except Exception as e:
            logger.error(f"Critic Loop Error: {e}")
            return draft_json_str

    def _fallback_response(self, error_msg):
        loc = LOCALIZATION.get(self.language, LOCALIZATION["en"])
        fallback_tweet = loc["fallback"]

        return json.dumps({
            "sentiment": "NEUTRAL",
            "reasoning": f"AI Model unavailable ({error_msg}). Defaulting to neutral.",
            "tweet": fallback_tweet,
            "hallucination_check": []
        })

if __name__ == "__main__":
    # Test
    agent = AnalysisAgent()
    print(f"Loaded Language: {agent.language}")
    
    # Mock Event Data
    mock_event = {
        "title": "Bitcoin hits $100k",
        "source_count": 3,
        "sources": ["CoinDesk", "WatcherGuru", "TheBlock"],
        "facts": [
            {"fact": "Bitcoin price exceeded $100,000", "sources": ["CoinDesk", "WatcherGuru"]},
            {"fact": "Trading volume spiked 200%", "sources": ["TheBlock", "CoinDesk"]}
        ],
        "items": []
    }
    
    print("Testing Agent Analysis (Verified Event)...")
    result = agent.analyze_situation(mock_event, "Whale: Quiet", "History: None")
    print(result)
