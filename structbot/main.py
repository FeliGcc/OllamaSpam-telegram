import asyncio
from aiogram import Bot, Dispatcher
from config.conf import TOKEN, API_Ollama
from commands import start, risk

async def main():
    bot = Bot(TOKEN)
    dp = Dispatcher()
    
    dp.include_router(start.router)
    dp.include_router(risk.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())