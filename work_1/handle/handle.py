from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command('start'))
async def handle_start(message: Message):
    await message.answer(text='Задай мне вопрос связанный с моей базой данных')


@router.message()
async def handle_message(message: Message):
    await message.answer(text=f'Я не отвечаю на сообщения ID {message.chat.id}')

    # await message.answer(text=result)
