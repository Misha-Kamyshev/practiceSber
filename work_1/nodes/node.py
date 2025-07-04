from langchain_core.messages import HumanMessage, SystemMessage

from work_1.databases.query import get_avg_group, get_avg_grade_on_subject, get_bad_students, get_grades_db
from work_1.static import State, DB_SCHEMA, giga
from work_1.logger import write_logs


def get_grades(state: State) -> State:
    messages = state['messages']
    if not messages:
        messages.append(SystemMessage(content=DB_SCHEMA))

    prompt = ('Тебе необходимо определить, о каком предмете и какой группе говорится в запросе. '
              'Ты должен ответить **только** в следующем формате (без кода, пояснений, описаний):\n'
              'предмет: <НАЗВАНИЕ ПРЕДМЕТА В ВЕРХНЕМ РЕГИСТРЕ>; группа: <НАЗВАНИЕ ГРУППЫ В ВЕРХНЕМ РЕГИСТРЕ>\n'
              'Пример: предмет: МАТЕМАТИКА; группа: ИТ-102\n'
              'Никаких комментариев, кода, объяснений — только результат в указанном формате.\n'
              'Запрос: ' + state['user_input'])

    if state['warning']:
        prompt = ('Ошибка в названии группы или предмета, возможна опечатка. '
                  'Проверь ошибки в названиях группы и предмета, и верни исправленный вариант. '
                  'Ты должен ответить **только** в следующем формате (без кода, пояснений, описаний):\n'
                  'предмет: <НАЗВАНИЕ ПРЕДМЕТА В ВЕРХНЕМ РЕГИСТРЕ>; группа: <НАЗВАНИЕ ГРУППЫ В ВЕРХНЕМ РЕГИСТРЕ>\n'
                  'Пример: предмет: МАТЕМАТИКА; группа: ИТ-101\n'
                  'Никаких комментариев, кода, объяснений — только результат в указанном формате.\n'
                  'Запрос пользователя: ' + state['user_input'])

    messages.append(HumanMessage(content=prompt))

    result = giga.invoke(messages)
    messages.append(result)
    state['messages'] = messages

    write_logs('step_1.log', question_human=prompt, returns=result.content)

    results = result.content.split(';')
    subject = results[0].split(':')[1].strip().upper()
    group = results[1].split(':')[1].strip().upper()


    try:
        result_avg_group = get_avg_group(group, subject)
        result_min_avg_grade = get_avg_grade_on_subject(subject)
        result_grades = get_grades_db(group, subject)

        if not all([result_min_avg_grade, result_avg_group, result_grades]):
            state['result'] = 'Ошибка выполнения попробуйте снова'
            state['error'] = None
            state['warning'] = True

        else:
            state['warning'] = False
            state['error'] = None
            state['count_warning'] += 1

            state['current_avg_group'] = float(result_avg_group[0])
            state['min_avg_grade'] = result_min_avg_grade[0]
            state['grade'] = result_grades
            state['result'] = (f"Средний балл группы: {result_avg_group[0]}; "
                               f"необходимый средний балл: {result_min_avg_grade[0]};")

    except Exception as e:
        state['result'] = 'Ошибка запроса в базу данных'
        state['error'] = str(e)
        state['warning'] = True

        write_logs('step_1.log', question_human='Ошибка при выполнении SQL', returns=str(e))

    return state


def assessment_analysis(state: State) -> State:
    prompt = ""
    if state['warning']:
        prompt += (
            'Твой предыдущий ответ был не правильный и средний балл все еще низкий.\n'
            'Тебе необходимо взять других студентов.\n'
        )

    prompt += (
        'Ты должен строго следовать этим правилам для выбора студентов:\n'
        '1. В первую очередь выбирай студентов БЕЗ ОЦЕНКИ (None) — они в максимальном приоритете.\n'
        '2. Затем выбирай студентов с НАИБОЛЬШИМ коэффициентом мотивации.\n'
        '3. Среди них сначала бери тех, у кого ОЦЕНКА НИЖЕ.\n'
        '4. НИКОГДА не выбирай студентов, у которых уже оценка 5 — они не нуждаются в исправлении.\n\n'
        'Каждый выбранный студент:\n'
        '- Если у него нет оценки (None), считается как будто он получает оценку 5.\n'
        '- Если у него оценка меньше 5, она заменяется на 5.\n\n'
        'После каждого выбора обязательно пересчитывай средний балл группы:\n'
        '- Учти все оценки (исправленные и нет) и дели на общее число студентов.\n'
        '- Если средний балл становится ≥ необходимого, остановись.\n'
        '- При сравнении баллов не округляй числа, то есть (4.6 < 5.0), (4.823 < 5.0), (4.6 > 3.845), (5.0 = 5.0)\n\n'
        'В ответе напиши свои рассуждения, ты не должен рассуждать через код\n'
        'Каждый студент представлен в формате: (id_студента, оценка, коэффициент мотивации).\n'
        'Если оценка отсутствует, она будет записана как None.\n\n'
        '**В последней строке после рассуждений ты должен вернуть ТОЛЬКО ответ в следующем формате (без кода, пояснений, описаний):**\n'
        '"студенты, которым необходимо получить оценки: <id через запятую>"\n\n'
        f'Данные студентов: {state["grade"]}; текущий средний балл: {state["current_avg_group"]}; необходимый средний балл: {state["min_avg_grade"]}'
    )

    messages = state['messages']
    messages.append(HumanMessage(content=prompt))

    result = giga.invoke(messages)

    messages.append(result)
    state['messages'] = messages

    write_logs('step_2.log', question_human=prompt, returns=result.content)

    try:
        results = result.content.split('\n')[-1].split(': ')
        bad_students: list[str] = []
        id_bad_students = list(map(int, results[1].strip().split(', ')))
        result_bad_students_db = get_bad_students(id_bad_students)

        for row in result_bad_students_db:
            bad_students.append(f"{row[0]} {row[1]}")

        state['result'] += f" студенты, которым необходимо получить оценки: {', '.join(bad_students)}"

    except (IndexError, ValueError, AttributeError) as e:
        state['warning'] = True
        state['count_warning'] += 1

        write_logs('step_2.log', question_human="Ошибка при работе с ответом от ИИ", returns=str(e))

    return state


def recount_avg(state: State) -> State:
    messages = state['messages']
    result = messages[-1].content.split(':')[1].strip().split(', ')
    grade: list[tuple] = []
    result = set(map(int, result))

    for row in state['grade']:
        if row[0] in result:
            grade.append((row[0], 5, row[2]))
        else:
            grade.append(row)

    avg = 0
    len_avg = 0
    for row in grade:
        if row[1] is not None:
            avg += row[1]
            len_avg += 1

    state['current_avg'] = avg / len_avg
    state['warning'] = True

    print(grade)
    return state
