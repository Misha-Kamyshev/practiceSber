import time
import random

from work_1.databases.query import get_subject, get_group, get_grades_db, get_avg_group, get_avg_grade_on_subject, \
    write_new_grade
from work_1.logger import write_logs
from work_1.nodes.graph import app


async def agent_orders(bot):
    config = {"configurable": {"thread_id": 'asd1'}}

    while True:
        result_subject_id = list(map(lambda x: x[0], get_subject()))
        result_group = list(map(lambda x: x[0], get_group()))
        result_api: list[tuple[int, int, float, int]] = []

        for subject_id in result_subject_id:
            for group in result_group:
                result_avg_group = get_avg_group(group, subject_id)
                result_min_avg_grade = get_avg_grade_on_subject(subject_id)
                result_grades = get_grades_db(group, subject_id)

                if result_avg_group >= result_min_avg_grade:
                    continue

                response = app.invoke({
                    'error': None,
                    'warning': False,
                    'count_warning': 0,

                    'min_avg_grade': result_min_avg_grade,
                    'current_avg_group': result_avg_group,
                    'grade': result_grades,
                    'select_next': False,
                    'selected_students': [],

                    'result': []
                }, config=config)

                result: list[tuple[int, int, float]] = (response.get('result'))

                for row in result:
                    result_api.append((row[0], row[1], row[2], subject_id))

        write_logs(file='agent.log', returns=f'{result_api}', question_human='Все студенты, которые должны исправить оценки')

        coefficient = 0.5
        for row in result_api:
            if row[2] * coefficient > random.random():
                try:
                    write_new_grade(row[0], row[3], 5)
                    await bot.send_message(text=f'Студент ID={row[0]} исправил оценку по предмету ID={row[3]}', chat_id=1423680752)
                except Exception as e:
                    write_logs(file='agent_error.log', returns=f'{e}', question_human='Ошибка при записи новой оценки в бд')
            time.sleep(5)

        time.sleep(86400)
