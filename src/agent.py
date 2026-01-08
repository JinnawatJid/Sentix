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

        # Load Configuration
        self._load_config()

        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables. AI analysis will fail.")
        else:
            try:
                # Preview models often require v1alpha.
                # We explicitly set it here to avoid 404 errors with experimental models.
                self.client = genai.Client(
                    api_key=self.api_key,
                    http_options=types.HttpOptions(api_version='v1alpha')
                )
            except Exception as e:
                 logger.error(f"Failed to initialize Gemini Client: {e}")

    def _load_config(self):
        """Loads language configuration from config.json"""
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.language = config.get("language", "en")
                    if self.language not in LOCALIZATION:
                        logger.warning(f"Language '{self.language}' not supported. Defaulting to 'en'.")
                        self.language = "en"
            else:
                logger.info("config.json not found. Defaulting to 'en'.")
        except Exception as e:
            logger.error(f"Error loading config.json: {e}. Defaulting to 'en'.")

    def analyze_situation(self, candidates, context_news, whale_data, historical_context):
        """
        Analyzes a list of NEW candidates + OLD context news + whale data + history.
        Only generates a tweet if a CANDIDATE story is cross-verified (either by another candidate or context).
        """
        if not self.client:
             return self._fallback_response("Missing API Key or Client Initialization Failed")

        loc = LOCALIZATION.get(self.language, LOCALIZATION["en"])
        headers = loc["headers"]
        prompt_instruction = loc["prompt_instruction"]

        # Format lists
        candidates_text = ""
        for i, item in enumerate(candidates):
            title = item.get('title', item.get('text', 'Unknown Content'))
            source = item.get('source', 'Unknown Source')
            candidates_text += f"- Item {i+1}: [{source}] {title}\n"

        context_text = ""
        if context_news:
            for i, item in enumerate(context_news):
                title = item.get('title', item.get('text', 'Unknown Content'))
                source = item.get('source', 'Unknown Source')
                context_text += f"- Context {i+1}: [{source}] {title}\n"

        prompt = f"""
        You are 'Sentix', an elite crypto sentiment analyst AI.
        
        TASK: Analyze the following news data to generate a SINGLE high-quality trading signal and viral tweet.

        1. **NEW CANDIDATE STORIES** (Potentially breaking news):
        {candidates_text}
        
        2. **OLDER CONTEXT STORIES** (Already processed, use for verification ONLY):
        {context_text}
        
        3. WHALE ALERT DATA (On-Chain Verification):
        "{whale_data}"
        
        4. HISTORICAL CONTEXT (RAG Memory):
        "{historical_context}"
        
        INSTRUCTIONS:
        1. **Selection & Cross-Verification (CRITICAL):**
           - You must select a story **FROM THE CANDIDATE LIST** as the main topic.
           - Verify this story by finding matching reports in either the **CANDIDATE LIST** or the **CONTEXT LIST**.
           - **RULE:** Only generate a tweet if the candidate story is confirmed by **at least 2 distinct sources** (e.g., Candidate Source A + Context Source B, or Candidate Source A + Candidate Source B).
           - **DO NOT** generate a tweet about a story that appears ONLY in the Context list (we have already tweeted about it).
           - If no candidate story meets the verification criteria, return NEUTRAL sentiment with reasoning "No verified new stories".

        2. **Synthesis & Persona:**
           - Adopt a **Crypto-Native Persona**: Be sharp, insightful, and engaging. Avoid robotic language.
           - Calculate a **Confidence Score** (Low/Medium/High) based on the number of verifying sources.

        3. **Analysis:**
           - Determine the sentiment (BULLISH, BEARISH, or NEUTRAL).
           - Focus on the **IMPACT** (Why this matters for price/market), not just a summary.
           - {prompt_instruction}
        
        TWEET FORMAT:
        The tweet MUST strictly follow this format with these exact emojis and headers:

        {headers['summary']}: [Synthesized Event + Confidence Score (e.g., 'Confidence: HIGH')]

        {headers['impact']}: [Deep analysis of the market impact. Why it matters. Fund flow context.]

        {headers['sentiment']}: [BULLISH/BEARISH/NEUTRAL] [Engaging closing line/Call to action]

        (Ensure the total length is under 280 characters. Use hashtags like #BTC #Crypto #Sentix at the very end or integrated if space permits, but prioritize the structure.)

        OUTPUT FORMAT (JSON):
        {{
            "sentiment": "BULLISH/BEARISH/NEUTRAL",
            "reasoning": "Explain which story was chosen and which sources confirmed it.",
            "tweet": "The formatted tweet string as described above."
        }}
        
        Respond ONLY with the JSON string. Do not use Markdown formatting blocks (```json ... ```).
        """
        
        try:
            # Using Gemini 3 Flash Preview as requested
            # Note: Preview models often require v1alpha or v1beta. The SDK defaults to v1beta.
            response = self.client.models.generate_content(
                model='gemini-3-flash-preview',
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            return self._fallback_response(str(e))

    def _fallback_response(self, error_msg):
        loc = LOCALIZATION.get(self.language, LOCALIZATION["en"])
        fallback_tweet = loc["fallback"]

        return json.dumps({
            "sentiment": "NEUTRAL",
            "reasoning": f"AI Model unavailable ({error_msg}). Defaulting to neutral.",
            "tweet": fallback_tweet
        })

if __name__ == "__main__":
    # Test
    agent = AnalysisAgent()
    print(f"Loaded Language: {agent.language}")
    
    candidates = [
        {"title": "Bitcoin hits $60k", "source": "WatcherGuru", "summary": "Price up."}
    ]
    context = [
        {"title": "Bitcoin surges past $59k", "source": "CoinDesk", "summary": "Rally continues."}
    ]
    mock_whale = "Whale Data"
    mock_history = "History"
    
    print("Testing Agent Analysis (Candidates + Context)...")
    result = agent.analyze_situation(candidates, context, mock_whale, mock_history)
    print(result)
