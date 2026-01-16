import requests
import logging
from src.database import SessionLocal
from src.models import BotLog
from datetime import datetime

def inject_log():
    db = SessionLocal()

    log_entry = BotLog(
        timestamp=datetime.utcnow(),
        level="WARNING",
        message="Critic rewrote the tweet (Verification Test)",
        context={
            "original": "Bitcoin is going to the moon! 🚀 Buy now! [No Source]",
            "rewritten": "Market analysis suggests positive momentum for Bitcoin. [Source: CoinGecko]"
        }
    )

    db.add(log_entry)
    db.commit()
    db.close()
    print("Injected mock log entry.")

if __name__ == "__main__":
    inject_log()
