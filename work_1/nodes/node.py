from langchain_core.messages import HumanMessage, SystemMessage

from work_1.databases.query import get_avg_group, get_avg_grade_on_subject, get_grades_db, get_bad_students
from work_1.logger import write_logs
from work_1.static import State, DB_SCHEMA, giga


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

            state['current_avg_group'] = state['avg_group'] = float(result_avg_group[0])
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
    rules = (
        'Ты должен строго следовать этим правилам для выбора студентов:\n'
        '1. В первую очередь выбирай студентов БЕЗ ОЦЕНКИ (None) — они в максимальном приоритете.\n'
        '2. Затем выбирай студентов с НАИБОЛЬШИМ коэффициентом мотивации.\n'
        '3. Среди них сначала бери тех, у кого ОЦЕНКА НИЖЕ.\n'
        '4. НИКОГДА не выбирай студентов, у которых уже оценка 5 — они не нуждаются в исправлении.\n\n'
        '5. НЕЛЬЗЯ выбирать одного и того же студента больше одного раза.\n'
        'Каждый выбранный студент:\n'
        '- Если у него нет оценки (None), считается как будто он получает оценку 5.\n'
        '- Если у него оценка меньше 5, она заменяется на 5.\n\n'
        'После каждого выбора программа пересчитает средний балл группы:\n'
        '- Если балл будет все еще низким, тебе необходимо выбрать еще одного студента по правилам.\n'
        'Каждый студент представлен в формате: (id_студента, оценка, коэффициент мотивации).\n'
        'Если оценка отсутствует, она будет записана как None.\n\n'
        '**Ты должен вернуть ТОЛЬКО ответ в следующем формате (без кода, пояснений, описаний):**\n'
        '"студент, которому необходимо исправить оценку: <id выбранного студента>"\n\n'
    )

    if state['select_next']:
        selected_students_set = set(state['selected_students'])
        grade = [
            s for s in state['grade']
            if s[0] not in selected_students_set and s[1] != 5
        ]

        prompt = (
            'Выбери следующего студента\n'
            f'{rules}'
            f'Данные студентов: {grade}; новый средний балл: {state["current_avg_group"]}; необходимый средний балл: {state["min_avg_grade"]}'
        )

    else:
        prompt = (
            'Выбери первого студента по тем-же правилам.\n'
            f'{rules}'
            f'Данные студентов: {state["grade"]}; текущий средний балл: {state["current_avg_group"]}; необходимый средний балл: {state["min_avg_grade"]}'
        )

    messages = state['messages']
    messages.append(HumanMessage(content=prompt))

    result = giga.invoke(messages)

    messages.append(result)
    state['messages'] = messages

    write_logs('step_2.log', question_human=prompt, returns=result.content)

    try:
        results = result.content.split(': ')
        state['selected_students'].append((int(results[1].strip())))
        state['select_next'] = True

    except (IndexError, ValueError, AttributeError) as e:
        state['warning'] = True
        state['count_warning'] += 1

        write_logs('step_2.log', question_human="Ошибка при работе с ответом от ИИ", returns=str(e))

    return state


def recount_avg(state: State) -> State:
    grade = state['grade']
    change_student = state['selected_students']

    new_grade: list[tuple] = []
    change_student_set = set(change_student)
    sum_grade = 0

    for row in grade:
        if row[0] in change_student_set:
            sum_grade += 5
            new_grade.append((row[0], 5, row[2]))

        else:
            if row[1] is not None:
                sum_grade += row[1]
            new_grade.append(row)

    state['current_avg_group'] = sum_grade / len(grade)
    state['grade'] = new_grade

    if state['min_avg_grade'] <= state['current_avg_group']:
        current_students_list = get_bad_students(change_student)
        current_students = ', '.join(f'{first} {last}' for first, last in current_students_list)

        state['result'] = (
            f"Средний балл группы: {state['avg_group']}; "
            f"необходимый средний балл: {state['min_avg_grade']}; "
            f"студенты, которым необходимо получить оценки: {current_students}"
        )

    return state
