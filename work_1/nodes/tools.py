from langchain.agents import tool

from work_1.databases.query import get_grades_db, get_avg_grade_on_subject, get_bad_students
from work_1.static import giga


@tool
def get_grades(group: str, subject: str) -> list[dict] | str:
    """
    Получить оценки всех студентов заданной группы по указанному предмету из базы данных.

    Args:
        group (str): Название группы, например, "ИТ-101".
        subject (str): Название предмета, например, "Алгоритмы".

    Returns:
        list[dict]: Список словарей в формате:
            - 'id_student': id_студента;
            - 'grade': оценка;
            - 'coefficient': коэффициент мотивации.
        str: Сообщение об ошибке, если запрос к БД не удался.
    """
    try:
        grades_tuple = get_grades_db(group, subject)
        grades_dict = []
        for id_student, grade, coefficient in grades_tuple:
            grades_dict.append({'id_student': id_student, 'grade': grade, 'coefficient': coefficient})
        return grades_dict
    except Exception as e:
        return 'Ошибка БД: ' + str(e)


@tool
def calculate_avg(grades: list[dict]) -> float:
    """
    Вычислить средний балл по списку оценок, игнорируя отсутствующие оценки (None).

    Args:
        grades (list[dict]): Список словарей формата:
            - 'grade': оценка,
            - 'id_student': ID студента,
            - 'coefficient': коэффициент мотивации.

    Returns:
        float: Средний балл группы. Если оценок нет — 0.0.
    """
    sum_grade = 0
    length = 0
    for grade_row in grades:
        grade = grade_row['grade']
        if grade is not None:
            sum_grade += grade
            length += 1

    if length == 0:
        return 0.0

    return sum_grade / length


@tool
def get_avg_subject(subject: str) -> float | str:
    """
    Получить минимальный целевой средний балл по предмету из базы данных.

    Args:
        subject (str): Название предмета.

    Returns:
        float: Средний целевой балл по предмету.
        str: Сообщение об ошибке, если запрос к БД не удался.
    """
    try:
        print(get_avg_grade_on_subject(subject)[0])
        return get_avg_grade_on_subject(subject)[0]

    except Exception as e:
        return 'Ошибка БД: ' + str(e)


@tool
def check_avg(avg_group: float, avg_subject: float) -> bool:
    """
    Проверить, достигает ли средний балл группы необходимого среднего балла по предмету.

    Args:
        avg_group (float): Средний балл группы.
        avg_subject (float): Необходимый средний балл по предмету.

    Returns:
        bool: True, если средний балл группы не ниже необходимого, иначе False.
    """
    return avg_subject <= avg_group


@tool
def choice_students(grades: list[dict]) -> str:
    """
    Выбрать одного студента для повышения оценки согласно заданным правилам.

    Правила выбора:
    1. В первую очередь выбираются студенты без оценки (None).
    2. Затем — студенты с максимальным коэффициентом мотивации.
    3. Среди них — те, у кого оценка ниже.
    4. Студенты с оценкой 5 не выбираются.

    Каждый выбранный студент считается получившим оценку 5 (если её не было или меньше 5).

    Args:
        grades (list[dict]): Список словарей формата:
            - 'grade': оценка;
            - 'id_student': ID студента;
            - 'coefficient': коэффициент мотивации.


    Returns:
        str: Строка в формате "студент, которому необходимо исправить оценку: <id выбранного студента>"
             (без лишних пояснений).
    """
    prompt = (
        'Выбери студента\n'
        'Ты должен строго следовать этим правилам для выбора студентов:\n'
        '1. В первую очередь выбирай студентов БЕЗ ОЦЕНКИ (None) — они в максимальном приоритете.\n'
        '2. Затем выбирай студентов с НАИБОЛЬШИМ коэффициентом мотивации.\n'
        '3. Среди них сначала бери тех, у кого ОЦЕНКА НИЖЕ.\n'
        '4. НИКОГДА не выбирай студентов, у которых уже оценка 5 — они не нуждаются в исправлении.\n\n'
        'Каждый выбранный студент:\n'
        '- Если у него нет оценки (None), считается как будто он получает оценку 5.\n'
        '- Если у него оценка меньше 5, она заменяется на 5.\n\n'
        'После каждого выбора программа пересчитает средний балл группы:\n'
        '- Если балл будет все еще низким, тебе необходимо выбрать еще одного студента по правилам.\n'
        'Если оценка отсутствует, она будет записана как None.\n\n'
        'Пожалуйста, верни только ID выбранного студента (число).\n\n'
        f'Данные студентов: {grades}'
    )

    response = giga.chat(messages=[{"role": "user", "content": prompt}])

    return response.choices[0].message.content


@tool
def change_grades(grades: list[dict], id_student: int) -> list[dict]:
    """
    Обновить оценки студентов для пересчета среднего балла, установив оценку 5 выбранному студенту.

    Args:
        grades (list[dict]): Список словарей в формате:
          - 'id_student': id,
          - 'grade': оценка,
          - 'coefficient': коэффициент мотивации.
        id_student (int): ID студента, которому ставится оценка 5.

    Returns:
        list[dict]: Обновлённый список оценок в формате:
        - 'id_student': id_student,
        - 'grade': оценка,
        - 'coefficient': коэффициент мотивации.
    """
    new_grades = []
    for grade in grades:
        if grade['id_student'] == id_student:
            new_grades.append({'id_student': grade['id_student'], 'grade': 5, 'coefficient': grade['coefficient']})
        else:
            new_grades.append(grade)
    return new_grades


@tool
def get_student_names(id_students: list, avg_group: float, avg_subject: float) -> str:
    """
    Получить конечный ответ из базы данных для отправки пользователю.

    Args:
        id_students (list): ID студентов которым необходимо исправить оценки.
        avg_group (float): Средний балл группы до того как началось изменение оценок.
        avg_subject (float): Средний балл по предмету для группы

    Returns:
        str: результат для вывода пользователю.
    """
    try:
        current_students_list = get_bad_students(id_students)
        current_students = ', '.join(f'{first} {last}' for first, last in current_students_list)

        return  (f"Средний балл группы: {avg_group}; "
                f"необходимый средний балл: {avg_subject}; "
                f"студенты, которым необходимо получить оценки: {current_students}")


    except Exception as e:
        return "Ошибка БД: " + str(e)


