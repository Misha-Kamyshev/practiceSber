from langchain_core.messages import HumanMessage

from app.databases.query import query_to_databases, extract_sql
from app.static import giga, State, DB_SCHEMA


def check_entities(state: State) -> State:
    state['system_prompt'] = DB_SCHEMA
    user_input = state.get('user_input')
    system_prompt = "Проверь, упоминается ли какой-либо студент или предмет. Верни SQL-запрос SELECT с WHERE и LIMIT 1. Только SQL."

    messages = [
        HumanMessage(content=state.get('system_prompt') + system_prompt + f'\nЗапрос + {user_input}')
    ]

    result = giga.invoke(messages)
    write_logs('node_1.log', result.content)
    state['check_sql'] = extract_sql(result.content.strip())

    return state


def validate_entities(state: State) -> State:
    sql = state.get('check_sql')
    try:
        result = query_to_databases(sql)
        write_logs('node_2.log', result)
        if result:
            state['entities_valid'] = True
        else:
            state['entities_valid'] = False
            state['correction_needed'] = True
    except Exception as e:
        state['entities_valid'] = False
        state['error'] = str(e)
        write_logs('node_2.log', str(e))

    return state


def correct_input(state: State) -> State:
    if not state.get('correction_needed'):
        return state

    user_input = state.get('user_input')
    system_prompt = "Ты нашел ошибку в данных в запросе пользователя. Исправь текст пользователя. Верни только исправленную строку."
    messages = [
        HumanMessage(content=state.get('system_prompt') + system_prompt + f'\nЗапрос: {user_input}')
    ]

    result = giga.invoke(messages)
    state['user_input'] = result.content.strip()
    write_logs('node_3.log', result.content)

    state['correction_needed'] = False
    state['entities_valid'] = None

    return state


def generate_sql(state: State) -> State:
    user_input = state.get('user_input')
    system_prompt = "Составь SQL-запрос по PostgreSQL. Верни только SQL в блоке ```sql ...```"
    messages = [
        HumanMessage(content=state.get('system_prompt') + system_prompt + f'\nЗапрос: {user_input}')
    ]

    result = giga.invoke(messages)
    state['final_sql'] = extract_sql(result.content.strip())
    write_logs('node_4.log', result.content)
    return state


def valid_final_sql(state: State) -> State:
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


def correct_final_sql(state: State) -> State:
    if not state.get('correction_needed'):
        return state

    sql = state.get('final_sql')

    system_prompt = ""
    if state.get('correction_needed'):
        system_prompt = "SQL-запрос выполнился, но ничего не вернул. Исправь SQL-запрос. Верни только SQL в блоке ```sql ... ```"
    if state.get('entities_valid'):
        error = state.get('error')
        system_prompt = f"SQL-запрос не выполнился и вернул ошибку: {error}. Исправь sql-запрос. Верни только SQL в блоке ```sql ... ```"

    messages = [
        HumanMessage(content=state.get('system_prompt') + system_prompt + f'\nSQL: {sql}')
    ]

    result = giga.invoke(messages)
    write_logs('node_6.log', result.content)
    state['final_sql'] = extract_sql(result.content.strip())

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

        file.write("\n------------Начало ответа--------------\n" + log + "\n----------------Конец ответа-----------------\n")
