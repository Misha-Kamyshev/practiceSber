from langchain_core.messages import HumanMessage, SystemMessage

from work_1.databases.query import get_grades_db, get_students_in_group, get_avg_grade_on_subject, get_bad_students, \
    get_coefficient_students, get_coefficient_subject
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

    if state['error_empty_sql']:
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

    results = result.content.split(';')
    subject = results[0].split(':')[1].strip().upper()
    group = results[1].split(':')[1].strip().upper()

    write_logs('step_2.log', question_human=prompt, returns=result.content)

    try:
        result_db = get_grades_db(group, subject)
        result_students_db = get_students_in_group(group)
        result_min_avg_grade = get_avg_grade_on_subject(subject)
        result_coefficient_students = get_coefficient_students(group)
        result_coefficient_subject = get_coefficient_subject(subject)

        if not all([result_db, result_students_db, result_min_avg_grade, result_coefficient_students,
                    result_coefficient_subject]):
            state['result'] = 'Ошибка выполнения попробуйте снова'
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

            data: list[tuple[int, int, float]] = []
            for i, sid in enumerate(student_id):
                student_grade = grade[i] if i < len(grade) else 0
                student_coefficient = next(
                    (coefficient[1] for coefficient in result_coefficient_students if coefficient[0] == sid), 1.0)

                data.append((sid, student_grade, student_coefficient))

            state['data'] = data
            state['min_avg_grade'] = result_min_avg_grade[0]
            state['coefficient_subject'] = result_coefficient_subject[0]
            state['error_empty_sql'] = False
            state['error_sql'] = None

    except Exception as e:
        state['result'] = 'Ошибка запроса в базу данных'
        state['error_sql'] = str(e)
        state['error_empty_sql'] = True
        write_logs('step_2.log', question_human='Ошибка при выполнении SQL', returns=str(e))

    return state


def assessment_analysis(state: State) -> State:
    prompt = (
        'Тебе необходимо проанализировать оценки группы по предмету. '
        'Для каждого студента даны его ID, оценка и коэффициент мотивации. '
        'Также известен коэффициент сложности предмета (одинаковый для всех студентов).\n\n'
        'Вычисли средний балл группы по следующей формуле:\n'
        'средний балл группы = (сумма(оценка × коэффициент мотивации)) / (коэффициент сложности × количество студентов)\n\n'
        '**Важно**: если оценка равна 0 — это значит, что у студента нет оценки.\n\n'
        'Сравни получившийся средний балл с необходимым. Если балл недостаточен, определи, '
        'каким студентам без оценки нужно выставить оценку(и), чтобы средний балл соответствовал требуемому. '
        'Если балл уже достаточен — напиши "нет".\n\n'
        'Ты должен ответить **только** в следующем формате (без кода, пояснений, описаний):\n'
        'средний балл группы: <число>; необходимый средний балл: <число>; студенты, которым необходимо получить оценки: <id через запятую>\n\n'
        'Пример 1: средний балл группы: 4.0; необходимый средний балл: 4.5; студенты, которым необходимо получить оценки: 1, 5\n'
        'Пример 2: средний балл группы: 4.6; необходимый средний балл: 4.0; студенты, которым необходимо получить оценки: нет\n\n'
        f'Данные: {state["data"]}; коэффициент сложности: {state["coefficient_subject"]}; необходимый средний балл: {state["min_avg_grade"]}')

    messages = state['messages']
    messages.append(HumanMessage(content=prompt))

    result = giga.invoke(messages)
    messages.append(result)
    state['messages'] = messages

    write_logs('step_3.log', question_human=prompt, returns=result.content)

    results = result.content.split('; ')
    avg_group = results[0].strip()
    bad_students: list[str] = []
    if float(avg_group.split(':')[1].strip()) >= state['min_avg_grade']:
        bad_students = ['нет']

    else:
        id_bad_students = list(map(int, results[2].split(':')[1].strip().split(', ')))
        result_bad_students_db = get_bad_students(id_bad_students)

        for row in result_bad_students_db:
            bad_students.append(f"{row[0]} {row[1]}")




    state['result'] = (f"{avg_group}; необходимый средний балл: {state['min_avg_grade']}; "
                       f"студенты, которым необходимо получить оценки: {', '.join(bad_students)}")

    return state
