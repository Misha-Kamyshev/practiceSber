from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda

from .graph import check_entities, validate_entities, correct_input, generate_sql, valid_final_sql, correct_final_sql, \
    check_text_or_sql, check_info, generate_sql_add_new_data
from ..static import MyState

graph = StateGraph(state_schema=MyState)

graph.add_node('check_info', RunnableLambda(check_info))
graph.add_node('check_entities', RunnableLambda(check_entities))
graph.add_node('check_text_or_sql', RunnableLambda(check_text_or_sql))
graph.add_node('validate_entities', RunnableLambda(validate_entities))
graph.add_node('correct_input', RunnableLambda(correct_input))
graph.add_node('generate_sql', RunnableLambda(generate_sql))
graph.add_node('valid_final_sql', RunnableLambda(valid_final_sql))
graph.add_node('correct_final_sql', RunnableLambda(correct_final_sql))
graph.add_node('generate_sql_add_new_data', RunnableLambda(generate_sql_add_new_data))

graph.set_entry_point('check_info')
graph.add_conditional_edges('check_info', lambda s: 'check_entities' if not s.get('add_new_data') else 'generate_sql_add_new_data')
graph.add_edge('check_entities', 'check_text_or_sql')
graph.add_conditional_edges('check_text_or_sql', lambda s: 'check_entities' if s.get('contains_text') else 'validate_entities')
graph.add_conditional_edges('validate_entities', lambda s: "correct_input" if s.get('correction_needed') else "generate_sql")
graph.add_edge('correct_input', 'check_entities')

graph.add_edge('generate_sql', 'valid_final_sql')
graph.add_conditional_edges("valid_final_sql", lambda s: END if not s.get('correction_needed') and s.get('entities_valid') else "correct_final_sql")
graph.add_edge('correct_final_sql', 'valid_final_sql')
graph.add_conditional_edges('generate_sql_add_new_data', lambda s: END if s.get('entities_valid') else "generate_sql_add_new_data")


memory = MemorySaver()

app = graph.compile(checkpointer=memory)
