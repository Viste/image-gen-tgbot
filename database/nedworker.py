import logging
from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from tools.ai.conversation import OpenAI
from tools.ai.stadif import StableDiffAI
from database.models import Dates, Woman

logger = logging.getLogger(__name__)
openai = OpenAI()
stable_diff_ai = StableDiffAI()


async def delete_nearest_date(session: AsyncSession, date_id: int):
    stmt = select(Dates).where(Dates.id == date_id)
    result = await session.execute(stmt)
    nearest_date = result.scalars().first()

    if nearest_date:
        await session.delete(nearest_date)
        await session.commit()
        logger.info(f"Deleted date: {nearest_date.date}, type: {type(nearest_date.date)}")
    else:
        logger.info("No date found with the given id")


async def get_nearest_date(session: AsyncSession):
    logger.info("Executing get_nearest_date...")
    now = datetime.now()
    stmt = select(Dates).order_by(func.abs(func.timestampdiff(text('SECOND'), Dates.date, now)))
    result = await session.execute(stmt)
    nearest_date = result.scalars().first()
    if nearest_date:
        logger.info(f"Nearest date found: {nearest_date.date}")
        return {'id': nearest_date.id, 'date': nearest_date.date, 'theme': nearest_date.theme}
    else:
        logger.info("No nearest date found.")
        return None


async def get_random_prompts(session: AsyncSession):
    stmt = select(Woman.prompt).order_by(func.rand()).limit(10)
    random_prompts = await session.execute(stmt)
    return random_prompts.scalars().all()
