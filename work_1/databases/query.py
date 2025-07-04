from work_1.databases.connect import connect


def get_grades_db(group: str, subject: str) -> list | None:
    connection = connect()
    query = '''SELECT s.student_id,
                      g.grade,
                      s.coefficient
               FROM students s
                        LEFT JOIN grades g
                                  ON s.student_id = g.student_id
                                      AND g.subject_id =
                                          (SELECT subject_id FROM subjects WHERE upper(subject_name) = %s LIMIT 1)
                        LEFT JOIN subjects subj
                                  ON g.subject_id = subj.subject_id
               WHERE upper(s.group_name) = %s
               ORDER BY s.student_id;
            '''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (subject, group))
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


def get_bad_students(id_students: list) -> list | None:
    connection = connect()
    query = '''
            SELECT first_name, last_name
            FROM students
            WHERE student_id = ANY (%s);
            '''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (id_students,))
            return cursor.fetchall()

    except Exception:
        raise

    finally:
        connection.close()


def get_avg_group(group: str, subject: str) -> list | None:
    connection = connect()
    query = '''
            SELECT ROUND(SUM(g.grade)::numeric / COUNT(g.grade), 2) AS group_avg_grade
            FROM grades g
                     JOIN
                 students s ON g.student_id = s.student_id
                     JOIN
                 subjects subj ON g.subject_id = subj.subject_id
            WHERE upper(s.group_name) = %s
              AND upper(subj.subject_name) = %s;
            '''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (group, subject))
            return cursor.fetchone()

    except Exception:
        raise

    finally:
        connection.close()
