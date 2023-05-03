from datetime import datetime

import aiocron
from aiogram.types import InputMediaPhoto
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Dates, Woman
from main import nasty
from tools.ai_tools import OpenAI, StableDiffAI
from tools.utils import config

openai = OpenAI()
stable_diff_ai = StableDiffAI()


async def delete_nearest_date(session: AsyncSession):
    now = datetime.now()
    nearest_date = await session.query(Dates).order_by(func.abs(Dates.date - now)).first()
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


async def post_images(session):
    random_prompts = await get_random_prompts(session)

    url_list = []
    for prompt in random_prompts:
        url = await stable_diff_ai.gen_ned_img(prompt)
        url_list.append(url)

    if len(url_list) == 10:
        media = [InputMediaPhoto(image_url) for image_url in url_list]
        await nasty.send_media_group(chat_id=config.p_channel, media=media)


@aiocron.crontab('*/5 * * * *')
async def cron_task(session: AsyncSession):
    scheduled_date, scheduled_theme = await delete_nearest_date(session)
    # TODO: use theme returned from delete_nearest_date

    if scheduled_date <= datetime.now():
        await post_images(session)
