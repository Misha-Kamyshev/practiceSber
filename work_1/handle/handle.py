from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from work_1.nodes.graph import app

router = Router()


@router.message(Command('start'))
async def handle_start(message: Message):
    await message.answer(text='Задай мне вопрос связанный с моей базой данных')


@router.message()
async def handle_message(message: Message):
    config = {"configurable": {"thread_id": 'asd1'}}

    response = app.invoke({
        'user_input': message.text,

        'error': None,
        'warning': False,
        'count_warning': 0,

        'min_avg_grade': 0,
        'current_avg_group': 0,
        'grade': [],
        'select_next': False,
        'selected_students': [],


        'result': ''
    }, config=config)

    result = response.get('result')
    await message.answer(text=result)
