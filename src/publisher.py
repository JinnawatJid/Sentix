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
            return response.data['id']
        except Exception as e:
            logger.error(f"Failed to post tweet via V2 Client: {e}")

            # Fallback to V1.1 API if V2 fails (Common for Free Tier / Media issues)
            if self.api_v1:
                logger.info("Attempting V1.1 API Fallback...")
                try:
                    if media_id:
                        status = self.api_v1.update_status(status=text, media_ids=[media_id])
                    else:
                        status = self.api_v1.update_status(status=text)
                    logger.info(f"Tweet posted successfully via V1.1 Fallback! ID: {status.id}")
                    return str(status.id)
                except Exception as v1_e:
                    logger.error(f"V1.1 Fallback also failed: {v1_e}")

            return None

    def fetch_tweet_metrics(self, tweet_ids):
        """
        Fetches public metrics (likes, retweets, replies, quotes) for a list of tweet IDs.
        Returns a dictionary mapping tweet_id -> metrics object.
        """
        if not self.client:
            logger.warning("Twitter Client not initialized. Skipping metrics fetch.")
            return {}

        metrics_map = {}

        # Batch requests up to 100 IDs (API limit)
        chunk_size = 100
        for i in range(0, len(tweet_ids), chunk_size):
            chunk = tweet_ids[i:i + chunk_size]
            try:
                response = self.client.get_tweets(
                    ids=chunk,
                    tweet_fields=["public_metrics", "created_at"]
                )

                if response.data:
                    for tweet in response.data:
                        metrics_map[str(tweet.id)] = {
                            "likes": tweet.public_metrics.get("like_count", 0),
                            "retweets": tweet.public_metrics.get("retweet_count", 0),
                            "replies": tweet.public_metrics.get("reply_count", 0),
                            "quotes": tweet.public_metrics.get("quote_count", 0),
                            "impressions": tweet.public_metrics.get("impression_count", 0), # Often 0/unavailable on Basic Tier
                            "created_at": tweet.created_at
                        }
            except Exception as e:
                logger.error(f"Failed to fetch metrics for chunk {chunk}: {e}")

        return metrics_map

if __name__ == "__main__":
    # Test
    pub = TwitterPublisher()
    # pub.post_tweet("🤖 Hello World! This is a test from Sentix Bot.")
