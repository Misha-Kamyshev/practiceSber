from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from work_1.nodes.graph import app

router = Router()
start = True


@router.message(Command('start'))
async def handle_start(message: Message):
    await message.answer(text='Задай мне вопрос связанный с моей базой данных')


@router.message()
async def handle_message(message: Message):
    global start
    config = {"configurable": {"thread_id": 'asd1'}}

    response = app.invoke({
        'user_input': message.text,
        'start': start,

        'error_sql': '',
        'error_empty_sql': False,
        'check_sql': '',
        'count_error_sql': 0,
        'student_id': [],
        'grade': [],
        'result': ''
    }, config=config)

    result = response.get('result')
    await message.answer(text=result)
    start = False
