from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from langchain_core.messages import HumanMessage, SystemMessage

from work_1.nodes.node import app
from work_1.static import DB_SCHEMA

router = Router()
start = True


@router.message(Command('start'))
async def handle_start(message: Message):
    await message.answer(text='Задай мне вопрос связанный с моей базой данных')


@router.message()
async def handle_message(message: Message):
    pass
