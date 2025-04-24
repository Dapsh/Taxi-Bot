import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

# Import local modules
from config import BOT_TOKEN
from db import Database
from registration import router as reg_router
from passenger import router as passenger_router
from driver import router as driver_router
from common import router as common_router

# Configure logging
logging.basicConfig(level=logging.INFO)


# Define bot commands for menu
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить/перезапустить бота"),
        BotCommand(command="help", description="Показать справку")
    ]
    await bot.set_my_commands(commands)


async def main():
    # Initialize bot and dispatcher
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Initialize database
    db = Database()
    await db.init()

    # Register routers
    dp.include_router(common_router)
    dp.include_router(reg_router)
    dp.include_router(passenger_router)
    dp.include_router(driver_router)

    # Set bot commands
    await set_commands(bot)

    # Start polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Error occurred: {e}")