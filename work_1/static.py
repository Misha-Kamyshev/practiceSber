import os
from pyexpat.errors import messages
from typing import Optional

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage

from langchain_gigachat.chat_models import GigaChat
from aiogram import Bot, Dispatcher
from langgraph.graph import MessagesState

load_dotenv()

AUTHORIZATION_KEY = os.getenv("AUTHORIZATION_KEY")
DATA_SOURCE = os.getenv("DATA_SOURCE")
BOT_TOKEN = os.getenv("BOT_TOKEN")

DB_SCHEMA = '''Ты помощник-аналитик и работаешь с оценками студентов. Также работаешь с базой данных PostgreSQL. В ней есть следующие таблицы:
                
                1. Таблица `students`:
                   - `student_id` (integer, PRIMARY KEY)
                   - `first_name` (varchar(50)) — имя студента
                   - `last_name` (varchar(50)) — фамилия студента
                   - `group_name` (varchar(20)) — название группы
                
                2. Таблица `subjects`:
                   - `subject_id` (integer, PRIMARY KEY)
                   - `subject_name` (varchar(100)) — название предмета
                   - `min_score_subject` (real) — минимальный средний балл группы по предмету
                
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
                !!!!!!КАЖДЫЙ ЗАПРОС БУДЕТ СОДЕРЖАТЬ ШАБЛОН КАК НЕОБХОДИМО ОТВЕТИТ, СТРОГО СОБЛЮДАЙ ЕГО!!!!!!.
                '''

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

giga = GigaChat(
    credentials=AUTHORIZATION_KEY,
    verify_ssl_certs=False,
    model="GigaChat"
)


class State(MessagesState, total=False):
    start: Optional[bool]  # на старте True все остальное время False для записи на старте системного промпта
    user_input: Optional[str]  # начальное сообщение от пользователя
    check_sql: Optional[str]  # промежуточный SQL-запрос

    error_sql: Optional[str]  # ошибка, которая возникает при ошибочном выполнении sql
    error_empty_sql: Optional[bool]  # ошибка, если вывод sql пуст
    count_error_sql: Optional[int]  # счетчик ошибок

    student_id: Optional[list[int]]
    grade: Optional[list[int]]
    min_avg_grade: Optional[int]

    result: Optional[str]  # конечный ответ от ИИ для вывода пользователю
