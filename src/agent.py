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

    def analyze_situation(self, verified_cluster, whale_data, historical_context):
        """
        Analyzes a SINGLE VERIFIED CLUSTER.
        The clustering logic in IngestionModule has already grouped similar stories
        and calculated the verification score (count of distinct sources).
        """
        if not self.client:
             return self._fallback_response("Missing API Key or Client Initialization Failed")

        loc = LOCALIZATION.get(self.language, LOCALIZATION["en"])
        headers = loc["headers"]
        prompt_instruction = loc["prompt_instruction"]

        # Format Cluster Info
        topic = verified_cluster.get('topic', 'Unknown Topic')
        score = verified_cluster.get('score', 1)
        sources = verified_cluster.get('sources', [])

        articles_text = ""
        for i, item in enumerate(verified_cluster.get('items', [])):
            title = item.get('title', 'Unknown Title')
            summary = item.get('summary', item.get('text', ''))
            src = item.get('source', 'Unknown')
            articles_text += f"- Article {i+1} [{src}]: {title} - {summary}\n"

        prompt = f"""
        You are 'Sentix', an elite crypto sentiment analyst AI.
        
        TASK: Analyze this PRE-VERIFIED news cluster to generate a trusted trading signal.
        
        **VERIFIED EVENT CLUSTER:**
        Topic: {topic}
        Verification Score: {score} Sources (Sources: {', '.join(sources)})
        
        **ARTICLES:**
        {articles_text}
        
        **ADDITIONAL CONTEXT:**
        Whale Data: "{whale_data}"
        Historical RAG Context: "{historical_context}"
        
        INSTRUCTIONS:
        1. **Fact Checking & Citations:**
           - You are analyzing a cluster of articles about the SAME event.
           - Synthesize the details into a coherent narrative.
           - **CRITICAL:** You MUST append a short citation for your main claims, e.g. "Bitcoin hits $100k [Source: CoinDesk]".
           - If the articles conflict, mention the discrepancy.

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
            "tweet": fallback_tweet,
            "hallucination_check": []
        })

if __name__ == "__main__":
    # Test
    agent = AnalysisAgent()
    print(f"Loaded Language: {agent.language}")
    
    mock_cluster = {
        "topic": "Bitcoin hits $100k",
        "score": 3,
        "sources": ["CoinDesk", "WatcherGuru", "TheBlock"],
        "items": [
            {"title": "Bitcoin hits $100k", "source": "WatcherGuru", "summary": "Price up."},
            {"title": "BTC crosses $100k", "source": "CoinDesk", "summary": "Historic moment."}
        ]
    }
    
    print("Testing Agent Analysis (Verified Cluster)...")
    result = agent.analyze_situation(mock_cluster, "Whale: Quiet", "History: None")
    print(result)
