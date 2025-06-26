from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from langchain_core.messages import HumanMessage, SystemMessage

from app.nodes.node import app
from app.static import DB_SCHEMA

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
        'start': start
    }, config=config)
    result = response.get('final_result')

    start = False
    answer = []
    for row in result:
        line = " | ".join(str(item) for item in row)
        answer.append(line)

    await message.answer(text="\n".join(answer))
