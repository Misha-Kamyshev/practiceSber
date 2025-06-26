from copy import deepcopy

from langchain_core.messages import HumanMessage, SystemMessage

from app.databases.query import query_to_databases, extract_sql, insert_to_databases
from app.static import giga, MyState, DB_SCHEMA


def check_info(state: MyState) -> MyState:
    messages = state.get('messages')
    if state['start']:
        messages.insert(0, SystemMessage(content=DB_SCHEMA))
        state['start'] = False
    state['messages'] = messages

    messages = deepcopy(state.get('messages'))

    system_prompt = "Тебе необходимо проанализировать запрос пользователя. Если в запросе указано добавление информации в базу данных - верни слово 'добавление' (пример: Я хочу поставить оценку 5 студенту Петр Петров по предмету Математика), если проверка данных - верни 'SQL'. Ты должен вернуть только одно слово."

    messages.append(system_prompt + "Запрос\n" + state.get('user_input'))

    state['check_prompt'] = True
    state['add_new_data'] = False

    result = giga.invoke(messages)
    if result.content.strip() == 'добавление':
        state['add_new_data'] = True
    elif result.content.strip() == 'SQL':
        state['add_new_data'] = False

    state['entities_valid'] = True

    return state



def check_entities(state: MyState):
    system_prompt = "Проверь, упоминается ли какой-либо студент или предмет. Верни SQL-запрос (SELECT с WHERE и LIMIT 1) в блоке ```sql ... ```. Если не упоминается - верни одно слово 'нет'."
    if state.get('contains_text'):
        system_prompt = "В предыдущем ответе ты проигнорировал мое задание написать только SQL. Ответь на поставленный вопрос только SQL-запросом.\nВопрос: " + \
                        state.get('user_input')
    messages = state.get('messages')
    messages.append(HumanMessage(content=(system_prompt + "Запрос:\n" + state.get('user_input'))))

    result = giga.invoke(messages)
    print(result.content)
    if result.content == 'нет':
        state['check_prompt'] = False

    write_logs('node_1.log', result.content)
    messages.append(result)
    state['messages'] = messages
    state['check_sql'] = result.content.strip()

    return state


def check_text_or_sql(state: MyState):
    system_prompt = ("Поверь содержит ли это обычный текст или только SQL-запросы. "
                     "Если содержит текст верни 'да', если только sql верни 'нет' - только одно слово и больше ничего") + \
                    state.get('check_sql')
    messages = state.get('messages')
    messages.append(HumanMessage(content=system_prompt))

    result = giga.invoke(messages)
    messages.append(result)
    state['messages'] = messages

    if result.content.strip().lower() == 'да':
        state['contains_text'] = True
    else:
        state['contains_text'] = False

    return state


def validate_entities(state: MyState) -> MyState:
    sql = extract_sql(state.get('check_sql'))
    try:
        result = query_to_databases(sql)
        write_logs('node_2.log', result)
        if result and all(value is not None for value in result[0]):
            state['entities_valid'] = True
            state['correction_needed'] = False
        else:
            state['entities_valid'] = True
            state['correction_needed'] = True
    except Exception as e:
        state['entities_valid'] = False
        state['correction_needed'] = True
        state['error'] = str(e)
        state['check_sql'] = state.get('messages')[-1].content
        write_logs('node_2.log', str(e))

    return state


def correct_input(state: MyState) -> MyState:
    if not state.get('correction_needed'):
        return state

    if state.get('entities_valid'):
        system_prompt = "В ходе проверочного SQL-запроса была найдена ошибка. Исправь запрос, ошибка может быть в словах по которым ведется поиск и верни только исправленный SQL-запрос SELECT с WHERE и LIMIT 1. Верни только SQL в блоке ```sql ... ```.\n Запрос: " + state.get(
            'check_sql')
    else:
        system_prompt = "В ходе выполнения проверочного SQL-запроса, запрос не был выполнен. Исправь запрос ошибка может быть в словах по которым ведется поиск и верни только исправленный SQL-запрос SELECT с WHERE и LIMIT 1. Верни только SQL в блоке ```sql ... ```.\n Ошибка: " + state.get(
            'error')

    messages = state.get('messages')
    messages.append(HumanMessage(content=system_prompt))

    result = giga.invoke(messages)
    messages.append(result)
    write_logs('node_3.log', result.content)

    state['messages'] = messages

    state['correction_needed'] = False
    state['entities_valid'] = None

    return state


def generate_sql(state: MyState) -> MyState:
    user_input = state.get('user_input')
    system_prompt = "Составь SQL-запрос по PostgreSQL. Верни только SQL в блоке ```sql ...```"

    messages = state.get('messages')
    messages.append(HumanMessage(content=system_prompt + f'\nЗапрос: {user_input}'))

    result = giga.invoke(messages)
    state['final_sql'] = extract_sql(result.content.strip())
    write_logs('node_4.log', result.content)

    messages.append(result)
    state['messages'] = messages

    return state


def valid_final_sql(state: MyState) -> MyState:
    sql = state.get('final_sql')
    state['correction_needed'] = False
    state['entities_valid'] = True

    try:
        result = query_to_databases(sql)
        write_logs('node_5.log', result)
        if not result:
            state['correction_needed'] = True
            return state

        state['final_result'] = result
        return state

    except Exception as e:
        state['error'] = str(e)
        state['entities_valid'] = False
        state['correction_needed'] = True

        return state


def correct_final_sql(state: MyState) -> MyState:
    if not state.get('correction_needed'):
        return state

    sql = state.get('final_sql')

    system_prompt = ""
    if state.get('correction_needed'):
        system_prompt = "SQL-запрос выполнился, но ничего не вернул. Исправь SQL-запрос. Верни только SQL в блоке ```sql ... ```"
    if state.get('entities_valid') is False:
        error = state.get('error')
        system_prompt = f"SQL-запрос не выполнился и вернул ошибку: {error}. Исправь sql-запрос. Верни только SQL в блоке ```sql ... ```"

    messages = state.get('messages')
    messages.append(HumanMessage(content=state.get('system_prompt', '') + system_prompt + f'\nSQL: {sql}'))

    result = giga.invoke(messages)
    write_logs('node_6.log', result.content)
    state['final_sql'] = extract_sql(result.content.strip())

    messages.append(result)
    state['messages'] = messages

    state['correction_needed'] = False
    state['entities_valid'] = None

    return state


def generate_sql_add_new_data(state: MyState) -> MyState:
    system_prompt = "Составь SQL-запрос для добавления новой информации в таблицу бд. Верни только SQL в блоке ```sql ... ```.\nЗапрос:" \
                    + state.get('user_input')
    if not state.get('entities_valid'):
        system_prompt = "Твой SQL-запрос выполнился с ошибкой, исправь и верни только SQL в блоке ```sql ... ```.\nОшибка:" \
                        + state.get('error')

    messages = state.get('messages')
    messages.append(HumanMessage(content=system_prompt))

    result = giga.invoke(messages)
    print(result.content)
    write_logs('node_add_data.log', result.content)

    sql = extract_sql(result.content.strip())
    try:
        insert_to_databases(sql)
        state['entities_valid'] = True
        state['final_result'] = ["Успешно"]
    except Exception as e:
        state['error'] = str(e)
        state['entities_valid'] = False

    messages.append(result)
    state['messages'] = messages

    return state


def write_logs(file_name: str, log):
    with open(file_name, 'a', encoding="utf-8") as file:
        if isinstance(log, list):
            answer = []
            for row in log:
                line = " | ".join(str(item) for item in row)
                answer.append(line)
            log = '\n'.join(answer)

        file.write(
            "\n------------Начало ответа--------------\n" + log + "\n----------------Конец ответа-----------------\n")
