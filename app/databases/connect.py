import psycopg2
from psycopg2._psycopg import connection

from app.static import DATA_SOURCE

def connect() -> connection | None:
    try:
        db_connection: psycopg2.extensions.connection = psycopg2.connect(
            dsn=DATA_SOURCE,
            port=5432
        )
        return db_connection

    except Exception as e:
        print(e)
        return None

connect()