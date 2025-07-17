from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

import tools
from work_1.static import GigaChatLLM, AUTHORIZATION_KEY

from langchain.agents import initialize_agent
from langchain.agents import AgentType

tools_list = [
    tools.get_grades,
    tools.calculate_avg,
    tools.get_avg_subject,
    tools.check_avg,
    tools.choice_students,
    tools.change_grades,
    tools.get_student_names
]

llm = GigaChatLLM(credentials=AUTHORIZATION_KEY)

prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "Ты агент, который отвечает пользователю только используя доступные инструменты. "
        "Нельзя придумывать свои данные — используй инструменты.\n"
        "Когда даёшь финальный ответ (`Final Answer`), обязательно:\n"
        "- Используй корректный JSON\n"
        "- Все строки должны быть в двойных кавычках, никаких `обратных кавычек`\n"
        "- Пример:\n"
        "  {\"action\": \"Final Answer\", \"action_input\": \"Твой ответ пользователю\"}\n"
        "Если возникает ошибка базы данных — верни 'Ошибка БД: ...'."
    ),
    HumanMessagePromptTemplate.from_template("{input}")
])

agent = initialize_agent(
    tools=tools_list,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=False,
    prompt=prompt
)

response = agent.invoke("Подходит ли средний балл у группы ИТ-101 по предмету алгоритмы к минимальному по этому предмету")
print(response)
