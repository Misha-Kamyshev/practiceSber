from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda

from work_1.nodes.node import check_group_and_subject, get_grades
from work_1.static import State


def route_check_group_and_subject(state: State) -> str:
    if state['count_error_sql'] >= 5:
        state['result'] = 'Ошибка выполнения попробуйте снова'
        return END
    elif state['error_empty_sql']:
        state['count_error_sql'] = state['count_error_sql'] + 1
        return 'check_group_and_subject'
    state['count_error_sql'] = 0
    return 'get_grades'


def route_get_grades(state: State) -> str:
    if state['count_error_sql'] >= 5:
        state['result'] = 'Ошибка выполнения попробуйте снова'
        return END
    elif state['error_sql'] in None:
        state['result'] = 'Ошибка запроса в базу данных'
        return END
    elif state['error_empty_sql']:
        state['count_error_sql'] = state['count_error_sql'] + 1
        return 'get_grades'
    state['count_error_sql'] = 0
    return 'get_grades'


graph = StateGraph(state_schema=State)

# Nodes
graph.add_node('check_group_and_subject', RunnableLambda(check_group_and_subject))
graph.add_node('get_grades', RunnableLambda(get_grades))

# Edges
graph.set_entry_point('check_group_and_subject')
graph.add_conditional_edges('check_group_and_subject', route_check_group_and_subject)
graph.add_conditional_edges('get_grades', route_get_grades)

memory = MemorySaver()

app = graph.compile(checkpointer=memory)
