import os
import sqlite3
import unicodedata

from unidecode import unidecode


def main(root_path: str, db_name: str) -> None:
    """Remove rows with visually similar paths (but accents are encoded differently for instance).
    The row is deleted if it leads to the same file"""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Find duplicated hashes
    cursor.execute(
        """
    SELECT ascii_path, COUNT(*)
    FROM pictures
    GROUP BY ascii_path
    HAVING COUNT(*) > 1 AND ascii_path IS NOT NULL
    """
    )

    # Delete duplicates keeping the shortest path
    for index, row in enumerate(cursor.fetchall()):
        ascii_path, count = row

        cursor.execute(
            """
            SELECT ROWID, path, ascii_path, dhash
            FROM pictures
            WHERE ascii_path = ?
            ORDER BY LENGTH(dhash)
        """,
            (ascii_path,),
        )

        items = [
            {"rowid": rowid, "path": path, "dhash": dhash}
            for (rowid, path, ascii_path, dhash) in cursor.fetchall()
        ]
        original_item = items[-1]  # Keeping the item with the longest dhash
        full_path_original = os.path.join(root_path, original_item.get("path"))
        for item in items[:-1]:
            try:
                full_path = os.path.join(root_path, item.get("path"))
                if os.path.samefile(full_path_original, full_path):
                    print(
                        f"#{index}: Keeping {original_item.get('path')} Removing {item.get('path')}"
                    )
                    cursor.execute(
                        """
                    DELETE FROM pictures
                    WHERE path = ? and rowid = ?
                    """,
                        (item.get("path"), item.get("rowid")),
                    )

            except FileNotFoundError:
                print(f"File not found: {item.get('path')}")
                cursor.execute(
                    """
                    DELETE FROM pictures
                    WHERE path = ? and rowid = ?
                """,
                    (item.get("path"), item.get("rowid")),
                )
                continue
        conn.commit()

    conn.close()


if __name__ == "__main__":
    root_path = "/Users/nicolas/Library/CloudStorage/GoogleDrive-nicolas.draber@gmail.com/My Drive/Pictures"  # sys.argv[1]
    db_path = "/Users/nicolas/Library/CloudStorage/GoogleDrive-nicolas.draber@gmail.com/My Drive/Pictures/Pictures.db"  # sys.argv[2]
    main(root_path, db_path)
