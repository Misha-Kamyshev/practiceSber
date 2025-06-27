from langchain_core.messages import HumanMessage, SystemMessage

from work_1.databases.query import extract_sql, query_to_databases, get_grades_db, get_students_in_group, \
    get_avg_grade_on_subject
from work_1.static import State, DB_SCHEMA, giga
from work_1.logger import write_logs


def check_group_and_subject(state: State) -> State:
    messages = state['messages']
    if state['start']:
        messages.append(SystemMessage(content=DB_SCHEMA))
        state['start'] = False

    prompt = (
                 "Тебе необходимо составить SQL-запрос для проверки существования предмета и группы, которые указаны в запросе. "
                 "Формат вывода: ```sql ... ```.\nЗапрос: ") \
             + state['user_input']

    if state['error_empty_sql']:
        prompt = ('Твой SQL-запрос выполнился успешно, но вернул None. '
                  'Проверь еще раз текст запроса на ошибки в словах и исправь SQL-запрос. '
                  'Формат вывода: ```sql ... ```.\nЗапрос: ') \
                 + state['user_input'] + '\nSQL-запрос: ' + state['check_sql']

    if state['error_sql']:
        prompt = ('Твой SQL-запрос не выполнился. Исправь его и напиши снова. '
                  'Формат вывода: ```sql ... ```.\nЗапрос: ') \
                 + state['check_sql'] + "\nОшибка: " + state['error_sql']

    messages.append(HumanMessage(content=prompt))

    result = giga.invoke(messages)
    messages.append(result)

    state['messages'] = messages
    state['check_sql'] = result.content
    write_logs('step_1.log', question_human=prompt, returns=result.content)

    sql = extract_sql(result.content)
    try:
        result_db = query_to_databases(sql)
        if result_db and all(value is not None for value in result_db[0]):
            state['error_sql'] = None
            state['error_empty_sql'] = False
        else:
            state['error_sql'] = None
            state['error_empty_sql'] = True
    except Exception as e:
        state['error_sql'] = str(e)
        state['error_empty_sql'] = True
        write_logs('step_1.log', question_human='Ошибка при выполнении SQL', returns=str(e))

    return result


def get_grades(state: State) -> State:
    prompt = ('Тебе необходимо найти в запросе про какой предмет и группу там говорится. '
              'Формат вывода: предмет: МАТЕМАТИКА; группа: ИТ-102.\nЗапрос: ') \
             + state['user_input']

    if state['error_empty_sql']:
        prompt = ('SQL-запрос выполнился успешно, но вернул None. '
                  'Проверь ошибки в названиях группы и предмета, и верни исправленный вариант. '
                  'Формат вывода: предмет: МАТЕМАТИКА; группа: ИТ-102.\n'
                  'Запрос пользователя: ') + state['user_input']

    messages = state['messages']
    messages.append(HumanMessage(content=prompt))

    result = giga.invoke(messages)
    results = result.content.split(';')
    subject = results[0].split(':')[1].strip().upper()
    group = results[1].split(':')[1].strip().upper()

    messages.append(result)
    state['messages'] = messages

    write_logs('step_2.log', question_human=prompt, returns=result.content)

    try:
        result_db = get_grades_db(group, subject)
        result_students_db = get_students_in_group(group)
        result_min_avg_grade = get_avg_grade_on_subject(subject)
        if not result_db or not result_students_db or not result_min_avg_grade:
            state['error_sql'] = None
            state['error_empty_sql'] = True
        else:
            student_id: list[int] = []
            student_all: list[int] = []
            grade: list[int] = []
            for row in result_db:
                student_id.append(row[0])
                grade.append(row[1])

            for row in result_students_db:
                student_all.append(row[0])
            student_id_set = set(student_id)

            for student in student_all:
                if student not in student_id_set:
                    student_id.append(student)
                    student_id_set.add(student)

            state['student_id'] = student_id
            state['grade'] = grade
            state['min_avg_grade'] = result_min_avg_grade[0]
            state['error_empty_sql'] = False

    except Exception as e:
        state['error_sql'] = str(e)
        state['error_empty_sql'] = True
        write_logs('step_2.log', question_human='Ошибка при выполнении SQL', returns=str(e))

    return state
