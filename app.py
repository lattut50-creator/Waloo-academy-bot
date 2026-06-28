import asyncio
import os
from flask import Flask
from threading import Thread

# Import your bot's main components
from bot import dp, bot

app = Flask(__name__)

@app.route('/')
def home():
    return "Waloo Academy Bot is running! 🚀"

@app.route('/health')
def health():
    return "OK"

def run_bot():
    """Run the bot with proper error handling"""
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Start polling without signal handlers
        loop.run_until_complete(dp.start_polling(bot, skip_updates=True))
        loop.run_forever()
    except Exception as e:
        print(f"❌ Bot error: {e}")

if __name__ == "__main__":
    # Start the bot in a separate thread
    bot_thread = Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Run the Flask server
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
