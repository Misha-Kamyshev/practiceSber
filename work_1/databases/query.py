from work_1.databases.connect import connect


def extract_sql(sql: str) -> str:
    if sql.startswith("```") and sql.endswith("```"):
        lines = sql.splitlines()
        sql_query = '\n'.join(lines[1:-1])
    else:
        sql_query = sql

    return sql_query


def query_to_databases(sql: str):
    connection = connect()

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    except Exception:
        raise

    finally:
        connection.close()
