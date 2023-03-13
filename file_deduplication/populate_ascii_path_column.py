import sqlite3
import sys

from unidecode import unidecode


def ascii_path(root_path: str, db_name: str) -> None:
    """Remove non existing files"""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Find duplicated hashes
    cursor.execute(
        """
        SELECT rowid, path, ascii_path
        FROM pictures ORDER BY rowid
    """
    )
    # Update ascii_path with its unidecode version
    updated_path = 0
    for index, row in enumerate(cursor.fetchall()):
        rowid, path, ascii_path = row
        unidecode_path = unidecode(path).lower()
        if ascii_path != unidecode_path:
            updated_path += 1
            print(f"#{index}: {path} -> {unidecode_path}")
            cursor.execute(
                """
                UPDATE pictures
                SET ascii_path = ?
                WHERE rowid = ?
                """,
                (unidecode_path, rowid),
            )

        if updated_path > 0 and updated_path % 100 == 0:
            conn.commit()

    conn.commit()
    conn.close()


if __name__ == "__main__":
    root_path = sys.argv[1]
    db_path = sys.argv[2]
    ascii_path(root_path, db_path)
