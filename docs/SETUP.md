# Setup Guide: How to "Achieve" the Environment

This guide helps you obtain the necessary API keys and configure the environment to run Sentix in "Live Integration" mode.

## 1. Google Gemini API Key
Sentix uses Google's Gemini models for AI sentiment analysis.

1.  Go to [Google AI Studio](https://aistudio.google.com/).
2.  Click **"Get API key"** (top left).
3.  Click **"Create API key"**.
4.  Copy the key string.
5.  Save this for your `.env` file as `GEMINI_API_KEY`.

## 2. Twitter (X) API Keys
To fetch tweets and post updates, you need a Twitter Developer account.

1.  Go to the [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard).
2.  Sign up for a **Free** (or Basic) account.
3.  Create a **Project** and an **App**.
4.  In your App settings, navigate to **"Keys and tokens"**.
5.  Generate and copy the following:
    *   **Consumer Key** (API Key) -> `TWITTER_CONSUMER_KEY`
    *   **Consumer Secret** (API Key Secret) -> `TWITTER_CONSUMER_SECRET`
    *   **Access Token** -> `TWITTER_ACCESS_TOKEN`
    *   **Access Token Secret** -> `TWITTER_ACCESS_TOKEN_SECRET`
    *   **Bearer Token** -> `TWITTER_BEARER_TOKEN`

> **Note:** The "Free" tier has very strict limits (posting only, usually). Reading tweets might return 403 Forbidden. Sentix handles this by falling back to RSS feeds automatically.

## 3. Create the `.env` File
Create a file named `.env` in the root directory of the project and paste your keys:

```bash
# .env

# Google AI
GEMINI_API_KEY=your_gemini_key_here

# Twitter / X API
TWITTER_BEARER_TOKEN=your_bearer_token_here
TWITTER_CONSUMER_KEY=your_consumer_key_here
TWITTER_CONSUMER_SECRET=your_consumer_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
```

## 4. Run the Tests
Once your `.env` is ready, verify everything:

```bash
# Test the live connection (requires keys)
python tests/test_live_integration.py
```
