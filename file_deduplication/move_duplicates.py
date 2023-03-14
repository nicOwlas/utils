import json
import os
import pathlib
import shutil
import sqlite3
from argparse import ArgumentParser

from delete_ghost_paths import delete_ghost_paths
from populate_db import populate_db


def move_duplicates(
    root_path: str,
    db_name: str,
    destination_folder: str,
    file_filter: list,
    directories_to_ignore: list,
    dry_run: bool,
    db_key: str,
) -> None:
    """Move duplicate files - sharing the same hash"""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Delete rows for which no file can be found in the root directory
    delete_ghost_paths(root_path, db_name)

    populate_db(
        root_path,
        db_path,
        directories_to_ignore,
        file_filter,
    )

    # Find duplicated hashes
    cursor.execute(
        f"""
        SELECT {db_key}, COUNT(*)
        FROM pictures
        GROUP BY {db_key}
        HAVING COUNT(*) > 1 AND {db_key} IS NOT NULL
    """
    )

    # Delete duplicates keeping the shortest path
    duplicates = {}
    for row in cursor.fetchall():
        key, count = row

        cursor.execute(
            f"""
            SELECT rowid, path
            FROM pictures
            WHERE {db_key} = ?
            ORDER BY LENGTH(path)
        """,
            (key,),
        )

        items = [{"rowid": rowid, "path": path} for (rowid, path) in cursor.fetchall()]
        duplicates[key] = [item["path"] for item in items]
        if not dry_run:
            for item in items[1:]:
                try:
                    destination = os.path.join(destination_folder, item.get("path"))

                    pathlib.Path(os.path.dirname(destination)).mkdir(
                        parents=True, exist_ok=True
                    )
                    print(f"Moving {item.get('path')}")
                    shutil.move(os.path.join(root_path, item.get("path")), destination)
                except FileNotFoundError:
                    print(f"File not found: {item.get('path')}")
                finally:
                    cursor.execute(
                        """
                        DELETE FROM pictures
                        WHERE path = ? AND rowid = ?
                    """,
                        (item.get("path"), item.get("rowid")),
                    )
            conn.commit()

    conn.close()
    with open("./duplicates.json", "w", encoding="utf-8") as file:
        json.dump(duplicates, file, indent=4)


if __name__ == "__main__":
    # Default values if no argument is passed
    root_path = "/Users/nicolas/Library/CloudStorage/GoogleDrive-nicolas.draber@gmail.com/My Drive/Pictures"
    db_path = "/Users/nicolas/Library/CloudStorage/GoogleDrive-nicolas.draber@gmail.com/My Drive/Pictures/Pictures.db"
    duplicates_folder = "/Users/nicolas/Library/CloudStorage/GoogleDrive-nicolas.draber@gmail.com/My Drive/Pictures/to_delete"
    directories_to_ignore = ["@eaDir", "Lightroom"]
    file_filter = [
        ".jpeg",
        ".heic",
        ".tiff",
        ".jpg",
        ".cr2",
        ".raf",
        ".zip",
        ".png",
        ".mov",
        ".avi",
        ".mp4",
        ".dng",
    ]

    parser = ArgumentParser()
    parser.add_argument(
        "-pic",
        "--pictures_dir",
        dest="pictures_dir",
        default=root_path,
        help="Main directory where pictures are stored",
    )

    parser.add_argument(
        "-db",
        "--database",
        dest="db_path",
        default=db_path,
        help="Picture database location",
    )

    parser.add_argument(
        "-dup",
        "--duplicates_dir",
        dest="duplicates_dir",
        default=duplicates_folder,
        help="Directory where duplicates are moved",
    )

    parser.add_argument(
        "-f",
        "--file_filter",
        dest="file_filter",
        default=file_filter,
        help="File extensions to be scanned",
    )

    parser.add_argument(
        "-i",
        "--ignore",
        dest="directories_to_ignore",
        default=directories_to_ignore,
        help="Name of directories that won't be scanned",
    )

    parser.add_argument(
        "-dr",
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="DB is updated but no duplicates files are move. A duplicates.json is written with the names of the files that would be moved",
    )

    parser.add_argument(
        "-k",
        "--db_key",
        dest="db_key",
        default="hash",
        help="'hash' or 'dhash' database key to be used to find file duplicates. dhash only works on jpeg and heic files.",
    )

    args = parser.parse_args()

    pictures_dir = args.pictures_dir
    db_path = args.db_path
    duplicates_dir = args.duplicates_dir
    file_filter = args.file_filter
    directories_to_ignore = args.directories_to_ignore
    dry_run = args.dry_run
    db_key = args.db_key

    move_duplicates(
        pictures_dir,
        db_path,
        duplicates_dir,
        file_filter,
        directories_to_ignore,
        dry_run,
        db_key,
    )
