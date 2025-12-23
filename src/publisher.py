import tweepy
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("Publisher")

class TwitterPublisher:
    def __init__(self):
        self.consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
        self.consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

        self.client = None
        self.api_v1 = None

        if self.consumer_key and self.access_token:
            try:
                # Client for v2 (Posting text)
                self.client = tweepy.Client(
                    consumer_key=self.consumer_key,
                    consumer_secret=self.consumer_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret
                )

                # API v1.1 for Media Upload (if available/supported by keys)
                auth = tweepy.OAuth1UserHandler(
                    self.consumer_key, self.consumer_secret,
                    self.access_token, self.access_token_secret
                )
                self.api_v1 = tweepy.API(auth)

                logger.info("Twitter Publisher initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize Twitter Publisher: {e}")

    def post_tweet(self, text, media_path=None):
        """
        Posts a tweet. Tries to upload media if provided, otherwise posts text only.
        """
        if not self.client:
            logger.warning("Twitter Client not initialized. Skipping publish.")
            return False

        media_id = None
        if media_path and os.path.exists(media_path) and self.api_v1:
            try:
                logger.info(f"Uploading media: {media_path}")
                media = self.api_v1.media_upload(filename=media_path)
                media_id = media.media_id
            except Exception as e:
                logger.warning(f"Media upload failed (likely API tier restriction): {e}. Proceeding with text only.")

        try:
            logger.info(f"Posting tweet: {text}")
            if media_id:
                response = self.client.create_tweet(text=text, media_ids=[media_id])
            else:
                response = self.client.create_tweet(text=text)

            logger.info(f"Tweet posted successfully! ID: {response.data['id']}")
            return True
        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
            return False

if __name__ == "__main__":
    # Test
    pub = TwitterPublisher()
    pub.post_tweet("🤖 Hello World! This is a test from Sentix Bot.")
