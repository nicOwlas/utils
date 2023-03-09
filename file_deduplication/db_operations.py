import sqlite3

from file_hash import hexhash


def create_db(db_name: str):
    """Create a DB with a single table : Pictures"""
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS pictures (path TEXT UNIQUE, hash TEXT, dhash TEXT)"
    )
    return connection, cursor


def is_path_in_db(connection, file_path: str):
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT 1 FROM pictures
        WHERE path = ?
    """,
        (file_path,),
    )
    return cursor.fetchone() is not None


def insert_db_entry(file_path: str, cursor) -> None:
    """Add an entry to the DB"""
    try:
        cursor.execute(
            "INSERT INTO pictures VALUES (?, ?, ?)",
            (file_path, hexhash(file_path), dhash(file_path)),
        )
    except PermissionError:
        pass


def read_db_entry(cursor):
    """Display DB content"""
    rows = cursor.execute("SELECT path, secret FROM pictures").fetchall()
    print(rows)
