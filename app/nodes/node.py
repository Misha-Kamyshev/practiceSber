from langgraph.graph import StateGraph, END, MessagesState
from langchain_core.runnables import RunnableLambda

from app.static import State
from .graph import check_entities, validate_entities, correct_input, generate_sql, valid_final_sql, correct_final_sql

graph = StateGraph(State)

graph.add_node('check_entities', RunnableLambda(check_entities))
graph.add_node('validate_entities', RunnableLambda(validate_entities))
graph.add_node('correct_input', RunnableLambda(correct_input))
graph.add_node('generate_sql', RunnableLambda(generate_sql))
graph.add_node('valid_final_sql', RunnableLambda(valid_final_sql))
graph.add_node('correct_final_sql', RunnableLambda(correct_final_sql))

graph.set_entry_point('check_entities')
graph.add_edge('check_entities', 'validate_entities')
graph.add_conditional_edges('validate_entities', lambda s: "correct_input" if s.get('correction_needed') else "generate_sql")
graph.add_edge('correct_input', 'check_entities')

graph.add_edge('generate_sql', 'valid_final_sql')
graph.add_conditional_edges("valid_final_sql", lambda s: END if not s.get('correction_needed') and s.get('entities_valid') else "correct_final_sql")
graph.add_edge('correct_final_sql', 'valid_final_sql')

app = graph.compile()
