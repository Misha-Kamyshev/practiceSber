import os
from typing import Optional

from dotenv import load_dotenv

from langchain_gigachat.chat_models import GigaChat
from aiogram import Bot, Dispatcher
from langgraph.graph import MessagesState

load_dotenv()

AUTHORIZATION_KEY = os.getenv("AUTHORIZATION_KEY")
DATA_SOURCE = os.getenv("DATA_SOURCE")
BOT_TOKEN = os.getenv("BOT_TOKEN")

DB_SCHEMA = '''Ты работаешь с базой данных PostgreSQL. В ней есть следующие таблицы:
                
                1. Таблица `students`:
                   - `student_id` (integer, PRIMARY KEY)
                   - `first_name` (varchar(50)) — имя студента
                   - `last_name` (varchar(50)) — фамилия студента
                   - `group_name` (varchar(20)) — название группы
                
                2. Таблица `subjects`:
                   - `subject_id` (integer, PRIMARY KEY)
                   - `subject_name` (varchar(100)) — название предмета
                
                3. Таблица `grades`:
                   - `grade_id` (integer, PRIMARY KEY)
                   - `student_id` (integer, FOREIGN KEY → students.student_id)
                   - `subject_id` (integer, FOREIGN KEY → subjects.subject_id)
                   - `grade` (integer) — оценка
                
                Связи между таблицами:
                - `grades.student_id` связан с `students.student_id`
                - `grades.subject_id` связан с `subjects.subject_id`
                
                Используй только существующие поля. При необходимости делай JOIN между таблицами.
                Все имена, фамилии и названия предметов начинаются с заглавной буквы (пример: Алексей Андреев; Теория вероятностей), не забудь поменять регистр.
                !!!!!!ВОЗВРАЩАЙ ТОЛЬКО SQL-ЗАПРОСЫ **НИКОГДА НЕ ОТВЕЧАЙ СЛОВАМИ**!!!!!!.
                '''

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

giga = GigaChat(
    credentials=AUTHORIZATION_KEY,
    verify_ssl_certs=False,
    model="GigaChat"
)


class MyState(MessagesState, total=False):
    pass
