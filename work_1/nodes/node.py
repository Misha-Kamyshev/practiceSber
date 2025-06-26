from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda

from .graph import check_entities, validate_entities, correct_input, generate_sql, valid_final_sql, correct_final_sql, \
    check_text_or_sql, check_info, generate_sql_add_new_data
from ..static import MyState

graph = StateGraph(state_schema=MyState)


memory = MemorySaver()

app = graph.compile(checkpointer=memory)
