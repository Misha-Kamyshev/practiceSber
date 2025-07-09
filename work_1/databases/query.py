from work_1.databases.connect import connect


def get_grades_db(group: str, subject_id: int) -> list[tuple] | None:
    connection = connect()
    query = '''SELECT s.student_id,
                      g.grade,
                      s.coefficient
               FROM students s
                        LEFT JOIN grades g
                                  ON s.student_id = g.student_id
                                      AND g.subject_id = %s
                        LEFT JOIN subjects subj
                                  ON g.subject_id = subj.subject_id
               WHERE upper(s.group_name) = %s
               ORDER BY s.student_id;
            '''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (subject_id, group))
            return cursor.fetchall()

    except Exception:
        raise

    finally:
        connection.close()


def get_avg_grade_on_subject(subject: int) -> float | None:
    connection = connect()
    query = '''SELECT subj.min_avg_grade
               FROM subjects subj
               WHERE subj.subject_id = %s;
            '''
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (subject,))
            return float(cursor.fetchone()[0])

    except Exception:
        raise

    finally:
        connection.close()


def get_bad_students(id_students: list) -> list | None:
    connection = connect()
    query = '''SELECT first_name, last_name
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


def get_avg_group(group: str, subject_id: int) -> float | None:
    connection = connect()
    query = '''SELECT ROUND(SUM(g.grade)::numeric / COUNT(g.grade), 2) AS group_avg_grade
               FROM grades g
                        JOIN
                    students s ON g.student_id = s.student_id
                        JOIN
                    subjects subj ON g.subject_id = subj.subject_id
               WHERE upper(s.group_name) = %s
                 AND subj.subject_id = %s;
            '''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (group, subject_id))
            return float(cursor.fetchone()[0])

    except Exception:
        raise

    finally:
        connection.close()


def get_subject() -> list | None:
    connection = connect()
    query = '''SELECT subject_id
               FROM subjects
               ORDER BY subject_name;
            '''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    except Exception:
        raise

    finally:
        connection.close()


def get_group() -> list | None:
    connection = connect()
    query = '''SELECT DISTINCT UPPER(group_name) AS group_upper
               FROM students
               ORDER BY group_upper;
            '''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    except Exception:
        raise

    finally:
        connection.close()


def write_new_grade(id_student: int, id_subject: int, grade: int) -> None:
    connection = connect()
    query = '''UPDATE grades
               SET grade = %s
               WHERE student_id = %s
                 and subject_id = %s;
            '''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (grade, id_student, id_subject))
            connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
