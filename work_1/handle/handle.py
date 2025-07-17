from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from work_1.nodes.agent import agent

router = Router()


@router.message(Command('start'))
async def handle_start(message: Message):
    await message.answer(text='Задай мне вопрос связанный с моей базой данных')


@router.message()
async def handle_message(message: Message):
    response = agent.invoke(
        "Подходит ли средний балл у группы ИТ-101 по предмету алгоритмы к минимальному по этому предмету")

    await message.answer(text=response)
