from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda

from work_1.nodes.node import get_grades, assessment_analysis, recount_avg
from work_1.static import State


def route_get_grades(state: State) -> str:
    if state['count_warning'] >= 5:
        return END

    elif state['error'] is not None:
        return END

    elif state['warning']:
        return 'get_grades'

    if state['min_avg_grade'] <= state['current_avg_group']:
        return END

    return 'assessment_analysis'


def route_recount_avg(state: State) -> str:
    if state['current_avg'] >= state['min_avg_grade']:
        return END

    return 'assessment_analysis'


graph = StateGraph(state_schema=State)

# Nodes
graph.add_node('get_grades', RunnableLambda(get_grades))
graph.add_node('assessment_analysis', RunnableLambda(assessment_analysis))
graph.add_node('recount_avg', RunnableLambda(recount_avg))

# Edges
graph.set_entry_point('get_grades')
graph.add_conditional_edges('get_grades', route_get_grades)
graph.add_conditional_edges('recount_avg', route_recount_avg)
graph.add_edge('assessment_analysis', 'recount_avg')

memory = MemorySaver()

app = graph.compile(checkpointer=memory)
