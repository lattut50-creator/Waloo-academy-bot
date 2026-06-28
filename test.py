import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Put your token here!
BOT_TOKEN = "8601191492:AAE4XuyPG8AV74fcwTyz-nKKdBDu0ar2Udg"

# Create bot
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("✅ Your bot is working! Great job, Waloo Academy is online!")

@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer("🆘 Just type /start to test the bot!")

async def main():
    print("🚀 Testing bot...")
    print("📱 Send /start to your bot on Telegram")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())