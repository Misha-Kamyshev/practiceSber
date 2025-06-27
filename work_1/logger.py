def write_logs(file: str, returns: str, question_human: str = "-"):
    with open(file, 'a', encoding='utf-8') as file:
        file.write("\n-----------------Начало--------------------\n")
        file.write(f"Запрос: {question_human}\n\n\n")
        file.write(f"Ответ ИИ: {returns}\n")
        file.write('-------------------Конец---------------------\n')

        file.close()
