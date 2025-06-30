from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda

from work_1.nodes.node import get_grades, assessment_analysis
from work_1.static import State


def route_get_grades(state: State) -> str:
    if state['count_error_sql'] >= 5:
        return END

    elif state['error_sql'] is not None:
        return END

    elif state['error_empty_sql']:
        return 'get_grades'

    return 'assessment_analysis'


graph = StateGraph(state_schema=State)

# Nodes
graph.add_node('get_grades', RunnableLambda(get_grades))
graph.add_node('assessment_analysis', RunnableLambda(assessment_analysis))

# Edges
graph.set_entry_point('get_grades')
graph.add_conditional_edges('get_grades', route_get_grades)
graph.add_edge('assessment_analysis', END)

memory = MemorySaver()

app = graph.compile(checkpointer=memory)
