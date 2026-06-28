import asyncio
import os
from flask import Flask
from threading import Thread

# Import your bot's main components
from bot import dp, bot, main

app = Flask(__name__)

@app.route('/')
def home():
    return "Waloo Academy Bot is running! 🚀"

@app.route('/health')
def health():
    return "OK"

def run_bot():
    asyncio.run(main())

if __name__ == "__main__":
    # Start the bot in a separate thread
    bot_thread = Thread(target=run_bot)
    bot_thread.start()
    
    # Run the Flask server
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)