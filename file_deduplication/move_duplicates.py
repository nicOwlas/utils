import os
import pathlib
import shutil
import sqlite3
import sys


def main(db_name: str, destination_folder: str) -> None:
    """Remove duplicated files"""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Find duplicated hashes
    cursor.execute(
        """
        SELECT secret, COUNT(*)
        FROM pictures
        GROUP BY secret
        HAVING COUNT(*) > 1
    """
    )

    # Delete duplicates keeping the shortest path
    for row in cursor.fetchall():
        hash, count = row

        cursor.execute(
            """
            SELECT path
            FROM pictures
            WHERE secret = ?
            ORDER BY LENGTH(path)
        """,
            (hash,),
        )

        paths = [path for path, in cursor.fetchall()]
        for path in paths[1:]:
            try:
                destination = os.path.join(destination_folder, path[1:])

                pathlib.Path(os.path.dirname(destination)).mkdir(
                    parents=True, exist_ok=True
                )
                print(f"Moving {path}")
                shutil.move(path, destination)
            except FileNotFoundError:
                print(f"File not found: {path}")
                continue
            else:
                cursor.execute(
                    """
                    DELETE FROM pictures
                    WHERE secret = ? AND path = ?
                """,
                    (hash, path),
                )
        conn.commit()

    conn.close()


if __name__ == "__main__":
    db_path = sys.argv[1]
    duplicates_folder = sys.argv[2]
    main(db_path, duplicates_folder)
