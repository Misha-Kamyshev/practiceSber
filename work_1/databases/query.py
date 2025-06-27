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


def get_grades_db(group: str, subject: str):
    connection = connect()
    query = '''
            SELECT s.student_id,
                   g.grade
            FROM grades g
                     JOIN
                 students s ON g.student_id = s.student_id
                     JOIN
                 subjects subj ON g.subject_id = subj.subject_id
            WHERE upper(s.group_name) = %s
              AND upper(subj.subject_name) = %s
            ORDER BY s.student_id,
                     g.grade;
            '''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (group, subject))
            return cursor.fetchall()

    except Exception:
        raise

    finally:
        connection.close()


def get_students_in_group(group: str):
    connection = connect()
    query = '''
            SELECT s.student_id
            FROM students s
            WHERE upper(s.group_name) = %s
            ORDER BY student_id;
            '''
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (group,))
            return cursor.fetchall()

    except Exception:
        raise

    finally:
        connection.close()


def get_avg_grade_on_subject(subject: str) -> tuple | None:
    connection = connect()
    query = '''
            SELECT subj.min_avg_grade
            FROM subjects subj
            WHERE upper(subj.subject_name) = %s;
            '''
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (subject,))
            return cursor.fetchone()

    except Exception:
        raise

    finally:
        connection.close()
