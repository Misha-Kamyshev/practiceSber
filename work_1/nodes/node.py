from langchain_core.messages import HumanMessage, SystemMessage

from work_1.databases.query import extract_sql, query_to_databases, get_grades_db, get_students_in_group, \
    get_avg_grade_on_subject, get_bad_students
from work_1.static import State, DB_SCHEMA, giga
from work_1.logger import write_logs


def check_group_and_subject(state: State) -> State:
    messages = state['messages']
    if state['start']:
        messages.append(SystemMessage(content=DB_SCHEMA))
        state['start'] = False

    prompt = (
            'Тебе необходимо составить SQL-запрос для проверки существования предмета и группы, которые указаны в запросе. '
            'Для поиска используй функцию UPPER для названий группы и предмета, и значения подставляй тоже большими буквами. '
            'Ты должен ответить **только** в следующем формате (без кода, пояснений, описаний):\n'
            '```sql\n...твой запрос...\n```\n'
            'Никаких комментариев, кода вне блока, пояснений — только SQL-запрос в указанном формате.\n'
            'Запрос пользователя: ' + state['user_input'])

    if state['error_empty_sql']:
        prompt = (
                'Твой SQL-запрос выполнился успешно, но вернул None. '
                'Проверь текст запроса на ошибки и исправь его. '
                'Ты должен ответить **только** в следующем формате (без кода, пояснений, описаний):\n'
                '```sql\n...твой запрос...\n```\n'
                'Никаких комментариев, кода вне блока, пояснений — только SQL-запрос в указанном формате.\n'
                'Запрос пользователя: ' + state['user_input'] + '\n'
                                                                'Твой предыдущий SQL-запрос: ' + state['check_sql'])

    if state['error_sql']:
        prompt = (
                'Твой SQL-запрос не выполнился. Исправь его и напиши снова. '
                'Если ошибка связана с ненайденной колонкой, помни, что название группы находится в таблице students, '
                'а название предмета в таблице subjects. '
                'Ты должен ответить **только** в следующем формате (без кода, пояснений, описаний):\n'
                '```sql\n...твой запрос...\n```\n'
                'Никаких комментариев, кода вне блока, пояснений — только SQL-запрос в указанном формате.\n'
                'Запрос пользователя: ' + state['user_input'] + '\n'
                                                                'Твой предыдущий SQL-запрос: ' + state[
                    'check_sql'] + '\nОшибка выполнения: ' + state['error_sql'])

    messages.append(HumanMessage(content=prompt))

    result = giga.invoke(messages)
    messages.append(result)

    state['messages'] = messages
    state['check_sql'] = result.content

    state['result'] = 'Ошибка выполнения попробуйте снова'
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


    if not state['error_empty_sql']:
        state['count_error_sql'] = 0

    return state


def get_grades(state: State) -> State:
    prompt = ('Тебе необходимо определить, о каком предмете и какой группе говорится в запросе. '
              'Ты должен ответить **только** в следующем формате (без кода, пояснений, описаний):\n'
              'предмет: <НАЗВАНИЕ ПРЕДМЕТА В ВЕРХНЕМ РЕГИСТРЕ>; группа: <НАЗВАНИЕ ГРУППЫ В ВЕРХНЕМ РЕГИСТРЕ>\n'
              'Пример: предмет: МАТЕМАТИКА; группа: ИТ-102\n'
              'Никаких комментариев, кода, объяснений — только результат в указанном формате.\n'
              'Запрос: ' + state['user_input'])

    if state['error_empty_sql']:
        prompt = ('Ошибка в названии группы или предмета, возможна опечатка. '
                  'Проверь ошибки в названиях группы и предмета, и верни исправленный вариант. '
                  'Ты должен ответить **только** в следующем формате (без кода, пояснений, описаний):\n'
                  'предмет: <НАЗВАНИЕ ПРЕДМЕТА В ВЕРХНЕМ РЕГИСТРЕ>; группа: <НАЗВАНИЕ ГРУППЫ В ВЕРХНЕМ РЕГИСТРЕ>\n'
                  'Пример: предмет: МАТЕМАТИКА; группа: ИТ-101\n'
                  'Никаких комментариев, кода, объяснений — только результат в указанном формате.\n'
                  'Запрос пользователя: ' + state['user_input'])

    messages = state['messages']
    messages.append(HumanMessage(content=prompt))

    result = giga.invoke(messages)
    messages.append(result)
    state['messages'] = messages

    results = result.content.split(';')
    subject = results[0].split(':')[1].strip().upper()
    group = results[1].split(':')[1].strip().upper()

    state['result'] = 'Ошибка выполнения попробуйте снова'
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
        state['result'] = 'Ошибка запроса в базу данных'
        state['error_sql'] = str(e)
        state['error_empty_sql'] = True
        write_logs('step_2.log', question_human='Ошибка при выполнении SQL', returns=str(e))

    return state


def assessment_analysis(state: State) -> State:
    prompt = (
        'Тебе необходимо проанализировать оценки группы по предмету, посчитать средний балл, '
        'сравнить этот балл с необходимым баллом по предмету. '
        'Понять какому минимальному количеству студентов необходимо получить оценку(и), '
        'чтобы средний балл группы соответствовал минимальному баллу группы. '
        'Также может быть, что у студента нет оценки. '
        'Ты должен ответить **только** в следующем формате (без кода, пояснений, описаний):\n'
        'средний балл группы: <число>; необходимый средний балл: <число>; студенты, которым необходимо получить оценки: <через запятую>\n'
        'Если средний балл группы больше или равен необходимому, то в конце напиши "нет" вместо списка студентов.\n'
        'Пример 1 (балл ниже нужного): средний балл группы: 4.0; необходимый средний балл: 4.5; студенты, которым необходимо получить оценки: Иванов, Петров\n'
        'Пример 2 (балл выше нужного): средний балл группы: 4.6; необходимый средний балл: 4.0; студенты, которым необходимо получить оценки: нет\n'
        'Никаких комментариев, кода, кавычек, квадратных скобок или объяснений — только строка с результатом в указанном формате.\n'
        f'Данные: студенты: {state["student_id"]}, оценки студентов: {state["grade"]}.')

    messages = state['messages']
    messages.append(HumanMessage(content=prompt))

    result = giga.invoke(messages)
    messages.append(result)
    state['messages'] = messages

    write_logs('step_3.log', question_human=prompt, returns=result.content)


    results = result.content.split('; ')
    avg_group = results[0].strip()
    bad_students: list[str] = []
    if results[2].split(':')[1].strip() != 'нет':
        id_bad_students = list(map(int, results[2].split(':')[1].strip().split(', ')))
        result_bad_students_db = get_bad_students(id_bad_students)

        for row in result_bad_students_db:
            bad_students.append(f"{row[0]} {row[1]}")
    else:
        bad_students = ['нет']

    state[
        'result'] = f"{avg_group}; необходимый средний балл: {state['min_avg_grade']}; студенты, которым необходимо получить оценки: {', '.join(bad_students)}"

    return state

# TODO Он может отправить данные не в том формате как я их жду и надо будет это учесть в split()
