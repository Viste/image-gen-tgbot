from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Dates, Woman
from tools.ai_tools import OpenAI, StableDiffAI

openai = OpenAI()
stable_diff_ai = StableDiffAI()


async def delete_nearest_date(session: AsyncSession):
    now = datetime.now()
    stmt = select(Dates).order_by(func.abs(Dates.date - now))
    result = await session.execute(stmt)
    nearest_date = result.scalars().first()
    theme = nearest_date.theme
    await session.delete(nearest_date)
    await session.commit()
    return {'date': nearest_date.date, 'theme': theme}


async def get_nearest_date(session: AsyncSession):
    now = datetime.now()
    nearest_date = await session.query(Dates).order_by(func.abs(Dates.date - now)).first()
    return nearest_date if nearest_date else None


async def get_random_prompts(session: AsyncSession):
    random_prompts = await session.execute(
        session.query(Woman.prompt).order_by(func.rand()).limit(10)
    )
    return random_prompts.scalars().all()
