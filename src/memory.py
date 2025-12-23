import chromadb
from chromadb.config import Settings
import hashlib
import json

class MemoryModule:
    def __init__(self, db_path="chroma_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name="crypto_news_history")

    def _generate_id(self, content):
        return hashlib.md5(content.encode()).hexdigest()

    def store_news_event(self, text, metadata):
        """Stores a news event with its metadata (source, sentiment, timestamp)."""
        doc_id = self._generate_id(text)
        
        # Check if already exists to avoid dupes (basic check)
        existing = self.collection.get(ids=[doc_id])
        if existing['ids']:
            return False # Already exists

        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        return True

    def retrieve_context(self, query_text, n_results=3):
        """Retrieves similar past news events to provide context."""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        context_items = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                context_items.append(f"Date: {meta.get('timestamp', 'N/A')}, Event: {doc}, Source: {meta.get('source', 'Unknown')}")
        
        return "\n".join(context_items)

if __name__ == "__main__":
    # Test memory module
    memory = MemoryModule()
    
    # Store some dummy history
    memory.store_news_event(
        "Bitcoin crashes 10% after SEC announcement.",
        {"source": "CoinDesk", "timestamp": "2023-01-01", "sentiment": "negative"}
    )
    memory.store_news_event(
        "Whales buy the dip as BTC hits $20k.",
        {"source": "WatcherGuru", "timestamp": "2023-01-02", "sentiment": "positive"}
    )
    
    # Retrieve
    print("Retrieving context for 'SEC regulation update'...")
    context = memory.retrieve_context("SEC regulation update")
    print(context)
