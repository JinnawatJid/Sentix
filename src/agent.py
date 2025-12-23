import google.generativeai as genai
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("AnalysisAgent")

class AnalysisAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables. AI analysis will fail.")
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash') # Using Flash for speed/cost efficiency

    def analyze_situation(self, news_item, whale_data, historical_context):
        """
        Analyzes the current news + whale data + history to determine sentiment and generate a tweet.
        """
        if not hasattr(self, 'model'):
             return self._fallback_response("Missing API Key")

        prompt = f"""
        You are 'Sentix', an elite crypto sentiment analyst AI.
        
        TASK: Analyze the following data points to generate a trading signal and a viral tweet.
        
        1. LIVE NEWS:
        "{news_item.get('title', news_item.get('text', 'Unknown Content'))}"
        (Summary: {news_item.get('summary', 'N/A')})
        
        2. WHALE ALERT DATA (On-Chain Verification):
        "{whale_data}"
        
        3. HISTORICAL CONTEXT (RAG Memory):
        "{historical_context}"
        
        INSTRUCTIONS:
        - Determine the sentiment (BULLISH, BEARISH, or NEUTRAL).
        - Cross-reference the news with the whale data. (e.g., Bad news + Whales selling = Verified Panic. Bad news + Whales Buying = Bullish Divergence/Fakeout).
        - Use the historical context to see if this pattern has happened before.
        
        OUTPUT FORMAT (JSON):
        {{
            "sentiment": "BULLISH/BEARISH/NEUTRAL",
            "reasoning": "Brief explanation of why.",
            "tweet": "Write a punchy, engaging tweet for X (Twitter). Use emojis. Mention key levels. Keep it under 280 chars. Add hashtags like #BTC #Crypto #Sentix."
        }}
        
        Respond ONLY with the JSON string. Do not use Markdown formatting blocks (```json ... ```).
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            return self._fallback_response(str(e))

    def _fallback_response(self, error_msg):
        return json.dumps({
            "sentiment": "NEUTRAL",
            "reasoning": f"AI Model unavailable ({error_msg}). Defaulting to neutral.",
            "tweet": "🤖 #Sentix AI Alert: Market movement detected. Check the charts! #Bitcoin #Crypto"
        })

if __name__ == "__main__":
    # Test
    agent = AnalysisAgent()
    
    mock_news = {"title": "Bitcoin drops below $60k", "summary": "Market fears rise as inflation data disappoints."}
    mock_whale = "🚨 2,000 BTC transferred from Binance to Unknown Wallet (Accumulation?)"
    mock_history = "Date: 2023-08-01, Event: BTC dipped on inflation news but rebounded 5% next day."
    
    print("Testing Agent Analysis...")
    result = agent.analyze_situation(mock_news, mock_whale, mock_history)
    print(result)
