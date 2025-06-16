import colorlog
import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from db.db import run_db
from tortoise import Tortoise

# Импортируем роутеры
from handlers import start

from dotenv import load_dotenv

load_dotenv()

def setup_logger():
    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )
    handler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    if logger.handlers:
        logger.handlers = []
    
    logger.addHandler(handler)
    return logger


bot = Bot(token=os.getenv('BOT_TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))


async def on_startup():

    logging.info('🚀 Бот запущен!')
    logging.info('Название: AniSearch — бот для поиска аниме')
    logging.info('Версия: 0.0.1')

    logging.info('Планировщик запущен')


async def on_shutdown(bot: Bot, dp: Dispatcher):

    logging.info('Выключение бота...')

    await Tortoise.close_connections()
    await bot.session.close()
    
    logging.info('✅ Бот успешно выключен!')


async def main():

    setup_logger()
    
    storage = MemoryStorage()
    
    dp = Dispatcher(storage=storage)
    
    try:

        await run_db()

        await on_startup()
        
        dp.include_router(start.router)

        await dp.start_polling(bot)

    except KeyboardInterrupt:
        logging.info('Выключение бота...')
    
    except Exception as e:
        logging.exception(f'Произошла ошибка: {e}')
    
    finally:
        await on_shutdown(bot, dp)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Выключение бота...")
        sys.exit(0)