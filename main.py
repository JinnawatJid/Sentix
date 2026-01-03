from src.web.app import app, bot_controller
import uvicorn
import logging

if __name__ == "__main__":
    # When running main.py directly, we start the web server.
    # The web server app.py handles starting the background scheduler thread on startup.
    logging.info("Starting Sentix Bot Web Server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
