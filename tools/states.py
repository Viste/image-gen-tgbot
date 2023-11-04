from aiogram.fsm.state import State, StatesGroup


class Text(StatesGroup):
    get = State()


class DAImage(StatesGroup):
    get = State()
    result = State()


class SDImage(StatesGroup):
    get = State()
    result = State()


class MJImage(StatesGroup):
    get = State()
    result = State()


class Voice(StatesGroup):
    get = State()
    result = State()


class Payment(StatesGroup):
    start = State()
    process = State()
