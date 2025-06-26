from langchain_core.messages import HumanMessage, SystemMessage

from work_1.databases.query import extract_sql, query_to_databases
from work_1.static import State, DB_SCHEMA, giga


def check_group_and_subject(state: State) -> State:
    messages = state['messages']
    if state['start']:
        messages.append(SystemMessage(content=DB_SCHEMA))
        state['start'] = False

    prompt = "Тебе необходимо составить SQL-запрос для проверки существования предмета и группы, которые указаны в запросе. Формат вывода: ```sql ... ```.\nЗапрос: " \
             + state['user_input']

    if state['error_empty_sql']:
        prompt = 'Твой SQL-запрос выполнился успешно, но ничего не вернул. Проверь еще раз текст запроса на ошибки в словах и исправь SQL-запрос. Формат вывода: ```sql ... ```.\nЗапрос: ' \
                 + state['user_input'] + '\nSQL-запрос: ' + state['check_sql']

    if state['error_sql']:
        prompt = 'Твой SQL-запрос не выполнился. Исправь его и напиши снова. Формат вывода: ```sql ... ```.\nЗапрос: ' \
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


def write_logs(file: str, returns: str, question_human: str = "-"):
    with open(file, 'a', encoding='utf-8') as file:
        file.write("\n-----------------Начало--------------------\n")
        file.write(f"Запрос: {question_human}\n\n\n")
        file.write(f"Ответ ИИ: {returns}\n")
        file.write('-------------------Конец---------------------\n')

        file.close()
