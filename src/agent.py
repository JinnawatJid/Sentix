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
            "summary": "📝 Summary",
            "fund_flow": "💸 Fund Flow",
            "sentiment": "🚀 Sentiment"
        },
        "fallback": "📝 Summary: Market movement detected.\n\n💸 Fund Flow: Analyzing on-chain data.\n\n🚀 Sentiment: NEUTRAL 🤖\n\n#Bitcoin #Crypto #Sentix",
        "prompt_instruction": "Ensure the tweet is in English."
    },
    "th": {
        "headers": {
            "summary": "📝 สรุป",
            "fund_flow": "💸 กระแสเงินทุน",
            "sentiment": "🚀 ความรู้สึก"
        },
        "fallback": "📝 สรุป: ตรวจพบความเคลื่อนไหวของตลาด\n\n💸 กระแสเงินทุน: กำลังวิเคราะห์ข้อมูล On-chain\n\n🚀 ความรู้สึก: เป็นกลาง (NEUTRAL) 🤖\n\n#Bitcoin #Crypto #Sentix",
        "prompt_instruction": "Translate the tweet content to Thai. Translate the headers as specified below. Keep hashtags in English (e.g. #Bitcoin #Crypto)."
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

    def analyze_situation(self, news_items, whale_data, historical_context):
        """
        Analyzes a list of news items + whale data + history to determine sentiment and generate a tweet.
        Prioritizes cross-verified stories.
        """
        if not self.client:
             return self._fallback_response("Missing API Key or Client Initialization Failed")

        loc = LOCALIZATION.get(self.language, LOCALIZATION["en"])
        headers = loc["headers"]
        prompt_instruction = loc["prompt_instruction"]

        # Format news list for the prompt
        news_text = ""
        if isinstance(news_items, list):
            for i, item in enumerate(news_items):
                title = item.get('title', item.get('text', 'Unknown Content'))
                source = item.get('source', 'Unknown Source')
                news_text += f"- Item {i+1}: [{source}] {title}\n"
        else:
             # Handle single item legacy case just in case
             title = news_items.get('title', news_items.get('text', 'Unknown Content'))
             source = news_items.get('source', 'Unknown Source')
             news_text = f"- Item 1: [{source}] {title}\n"

        prompt = f"""
        You are 'Sentix', an elite crypto sentiment analyst AI.
        
        TASK: Analyze the following aggregated news data to generate a SINGLE high-quality trading signal and viral tweet.
        
        1. LIVE AGGREGATED NEWS (from multiple sources):
        {news_text}
        
        2. WHALE ALERT DATA (On-Chain Verification):
        "{whale_data}"
        
        3. HISTORICAL CONTEXT (RAG Memory):
        "{historical_context}"
        
        INSTRUCTIONS:
        1. **Cross-Verification (CRITICAL):**
           - Scan the news items. Group stories that report the same event.
           - Identify the MOST significant story that is reported by **at least 2 distinct sources**.
           - If no story is confirmed by at least 2 distinct sources, you MUST return a NEUTRAL sentiment and set the tweet text to "Market monitoring in progress. No cross-verified significant events detected at this time. #Sentix". Do not generate a fake or unverified tweet.
           - Ignore low-impact noise or spam.

        2. **Synthesis:**
           - Combine details from all matching sources to create a comprehensive summary.

        3. **Analysis:**
           - Determine the sentiment (BULLISH, BEARISH, or NEUTRAL).
           - Cross-reference with Whale Data.
           - Use Historical Context for pattern matching.
           - {prompt_instruction}
        
        TWEET FORMAT:
        The tweet MUST strictly follow this format with these exact emojis and headers:

        {headers['summary']}: [Synthesized summary of the confirmed story]

        {headers['fund_flow']}: [Mention the whale data/on-chain flows]

        {headers['sentiment']}: [BULLISH/BEARISH/NEUTRAL] [Optional: Diamond/Rocket emoji if bullish]

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
    
    mock_news = [
        {"title": "Bitcoin drops below $60k", "source": "CoinDesk", "summary": "Market fears rise."},
        {"title": "BTC hits $59k amid sell-off", "source": "WatcherGuru", "summary": "Panic selling."},
        {"title": "Random irrelevant coin launch", "source": "Unknown", "summary": "Spam."}
    ]
    mock_whale = "🚨 2,000 BTC transferred from Binance to Unknown Wallet (Accumulation?)"
    mock_history = "Date: 2023-08-01, Event: BTC dipped on inflation news but rebounded 5% next day."
    
    print("Testing Agent Analysis (Multi-Source)...")
    result = agent.analyze_situation(mock_news, mock_whale, mock_history)
    print(result)
