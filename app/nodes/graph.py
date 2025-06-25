from langchain_core.messages import HumanMessage

from app.databases.query import query_to_databases, extract_sql
from app.static import giga, MyState, DB_SCHEMA


def check_entities(state: MyState):
    system_prompt = "Проверь, упоминается ли какой-либо студент или предмет. Верни SQL-запрос SELECT с WHERE и LIMIT 1. Только SQL."
    messages = state.get('messages')
    messages[-1].content = DB_SCHEMA + system_prompt + "Запрос\n" + messages[-1].content
    state['user_input'] = messages[-1].content

    result = giga.invoke(messages)
    write_logs('node_1.log', result.content)
    messages.append(result)
    state['messages'] = messages

    return state


def validate_entities(state: MyState) -> MyState:
    sql = extract_sql(state.get('messages')[-1].content)
    print(sql)
    try:
        result = query_to_databases(sql)
        write_logs('node_2.log', result)
        if result and all(value is not None for value in result[0]):
            state['entities_valid'] = True
            state['correction_needed'] = False
        else:
            state['entities_valid'] = True
            state['correction_needed'] = True
            state['check_sql'] = state.get('messages')[-1].content
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
        system_prompt = DB_SCHEMA + "В ходе проверочного SQL-запроса была найдена ошибка. Исправь запрос, ошибка может быть в словах по которым ведется поиск и верни только исправленный SQL-запрос SELECT с WHERE и LIMIT 1. Только SQL.\n Запрос: " + state.get(
            'check_sql')
    else:
        system_prompt = DB_SCHEMA + "В ходе выполнения проверочного SQL-запроса, запрос не был выполнен. Исправь запрос ошибка может быть в словах по которым ведется поиск и верни только исправленный SQL-запрос SELECT с WHERE и LIMIT 1. Только SQL.\n Ошибка: " + state.get(
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
    system_prompt = DB_SCHEMA + \
                    "Составь SQL-запрос по PostgreSQL. Верни только SQL в блоке ```sql ...```"

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

    messages = state.get('messages', [])
    messages.append(HumanMessage(content=state.get('system_prompt', '') + system_prompt + f'\nSQL: {sql}'))

    result = giga.invoke(messages)
    write_logs('node_6.log', result.content)
    state['final_sql'] = extract_sql(result.content.strip())

    messages.append(result)
    state['messages'] = messages

    state['correction_needed'] = False
    state['entities_valid'] = None

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
