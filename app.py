import asyncio
import os
import sys
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

def run_web_server():
    """Run Flask web server in a separate thread"""
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Starting web server on port {port}...")
    sys.stdout.flush()
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

async def run_bot():
    """Run the bot in the main thread"""
    print("🚀 Starting bot...")
    sys.stdout.flush()
    try:
        print("📱 Bot polling started...")
        sys.stdout.flush()
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        print(f"❌ Bot error: {e}")
        sys.stdout.flush()

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Starting Waloo Academy Bot...")
    print("=" * 50)
    sys.stdout.flush()
    
    # Start web server in a separate thread
    web_thread = Thread(target=run_web_server, daemon=True)
    web_thread.start()
    print("✅ Web server thread started")
    sys.stdout.flush()
    
    # Run bot in the main thread
    asyncio.run(run_bot())
