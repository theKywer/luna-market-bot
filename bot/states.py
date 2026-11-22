
from aiogram.fsm.state import State, StatesGroup


class SearchStates(StatesGroup):
    waiting_for_query = State()


class SupportStates(StatesGroup):
    waiting_for_faq_query = State()
