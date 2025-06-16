import logging
import os
from tortoise import Tortoise
from dotenv import load_dotenv

from datetime import datetime, date
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

load_dotenv()

async def run_db():
    logger.info('Инициализация базы данных...')

    database_url = os.getenv('DATABASE_URL')

    await Tortoise.init(
        db_url=database_url,
        modules={
            'models': [
                'db.models.users'
            ]
        },
        timezone='Europe/Moscow'
    )

    await Tortoise.generate_schemas()

    logger.info('Инициализация базы данных завершено успешно')
