import ollama
import os

class AnalysisAgent:
    def __init__(self, model_name="gemma3"):
        self.model_name = model_name
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        # In a real environment, you might need to configure the ollama client with the host
        # The ollama python library checks OLLAMA_HOST env var automatically.

    def analyze_situation(self, news_item, whale_data, historical_context):
        """
        Analyzes the current news + whale data + history to determine sentiment and generate a tweet.
        """
        
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
        
        Respond ONLY with the JSON.
        """
        
        try:
            response = ollama.chat(model=self.model_name, messages=[
                {
                    'role': 'user',
                    'content': prompt,
                },
            ])
            return response['message']['content']
        except Exception as e:
            # Fallback for when Ollama is not running (e.g. CI/CD or demo env)
            print(f"Warning: AI Agent failed ({e}). Using fallback response.")
            return """
            {
                "sentiment": "NEUTRAL",
                "reasoning": "AI Model unavailable. Defaulting to neutral based on market data availability.",
                "tweet": "🤖 #Sentix AI Offline. Market data shows active movement. Check the charts! #Bitcoin #Crypto"
            }
            """

if __name__ == "__main__":
    # Test the agent (Note: This requires Ollama running with the gemma3 model)
    # If not running, it will print a connection error, which is expected in this env if the server isn't up.
    agent = AnalysisAgent(model_name="gemma3")
    
    mock_news = {"title": "Bitcoin drops below $60k", "summary": "Market fears rise as inflation data disappoints."}
    mock_whale = "🚨 2,000 BTC transferred from Binance to Unknown Wallet (Accumulation?)"
    mock_history = "Date: 2023-08-01, Event: BTC dipped on inflation news but rebounded 5% next day."
    
    print("Testing Agent Analysis...")
    result = agent.analyze_situation(mock_news, mock_whale, mock_history)
    print(result)
