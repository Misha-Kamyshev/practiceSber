from work_1.databases.connect import connect


def get_grades_db(group: str, subject: str) -> list | None:
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


def get_students_in_group(group: str) -> list | None:
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


def get_coefficient_students(group: str) -> list | None:
    connection = connect()

    query = '''
            SELECT student_id, coefficient
            FROM students
            WHERE upper(group_name) = %s
            ORDER BY student_id
            '''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (group,))
            return cursor.fetchall()

    except Exception:
        raise

    finally:
        connection.close()


def get_coefficient_subject(subject_name: str) -> list | None:
    connection = connect()
    query = '''
            SELECT difficulty_factor
            FROM subjects
            WHERE upper(subject_name) = %s
            '''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (subject_name,))
            return cursor.fetchone()

    except Exception:
        raise

    finally:
        connection.close()
