import sqlite3

from file_hash import dhash, hexhash


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


def is_dhash_null(connection, file_path: str):
    """Returns True if a given row dhash value is NULL """
    cursor = connection.cursor()
    cursor.execute(
        "SELECT CASE WHEN dhash IS NULL THEN 1 ELSE 0 END FROM pictures WHERE path = ?",
        (file_path,),
    )

    row = cursor.fetchone()

    # Check if dhash is empty
    if row is not None and row[0] == 1:
        return True
    else:
        return False


def update_dhash(file_path: str, cursor) -> None:
    """Add an entry to the DB"""
    cursor.execute(
        "UPDATE pictures SET dhash = ? WHERE path = ? AND dhash IS NULL",
        (dhash(file_path), file_path),
    )


def read_db_entry(cursor):
    """Display DB content"""
    rows = cursor.execute("SELECT path, hash, dhash FROM pictures").fetchall()
    print(rows)
