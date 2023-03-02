from aiogram.fsm.state import State, StatesGroup


class Text(StatesGroup):
    get = State()
    result = State()


class Ai21Text(StatesGroup):
    get = State()
    result = State()


class DAImage(StatesGroup):
    get = State()
    result = State()


class SDImage(StatesGroup):
    get = State()
    result = State()


class Voice(StatesGroup):
    get = State()
    result = State()

