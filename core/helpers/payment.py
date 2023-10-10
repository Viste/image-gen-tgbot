import logging
from datetime import datetime, timedelta

from aiogram import types, Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import LabeledPrice
from sqlalchemy.ext.asyncio import AsyncSession

from database.manager import UserManager as user_manager
from database.models import User
from tools.states import Payment
from tools.utils import config

router = Router()
logger = logging.getLogger(__name__)


@router.message(Payment.process, F.content_type.in_({'text'}), F.chat.type == "private")
async def pay_sub(message: types.Message, state: FSMContext, bot: Bot):
    userid = message.from_user.id
    current_state = await state.get_state()
    logging.info("Current state: %r ", current_state)
    #await bot.send_invoice(userid, title='Приобретение подписки помощника "Настя"',
    #                       description='Приобрести Подписку', provider_token=config.payment_token, currency='RUB',
    #                       photo_url='https://i.pinimg.com/originals/73/a1/ec/73a1ecc7f59840a47537c012bc23d685.png',
    #                       photo_height=512, photo_width=512, photo_size=512, is_flexible=False, need_name=True,
    #                       prices=price, start_parameter='create_invoice_subscribe', payload='payload:subscribe')
