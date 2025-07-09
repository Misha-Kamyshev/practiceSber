from langchain_core.messages import HumanMessage, SystemMessage

from work_1.logger import write_logs
from work_1.static import State, giga, DB_SCHEMA


def assessment_analysis(state: State) -> State:
    messages = state['messages']
    if not messages:
        messages.append(SystemMessage(content=DB_SCHEMA))

    if state['select_next']:
        selected_students_set = set(state['selected_students'])
        grade = [
            s for s in state['grade']
            if s[0] not in selected_students_set and s[1] != 5
        ]

        prompt = (
            'Выбери следующего студента\n'
            f'Данные студентов: {grade}; новый средний балл: {state["current_avg_group"]}; необходимый средний балл: {state["min_avg_grade"]}'
        )

    else:
        prompt = (
            'Выбери первого студента по тем-же правилам.\n'
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

    new_grade: list[tuple[int, int, float]] = []
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

    for row in grade:
        if row[0] == change_student[-1]:
            state['result'].append(row)

    return state
