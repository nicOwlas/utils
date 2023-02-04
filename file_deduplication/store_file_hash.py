"""
Store files' hash in a DB
"""
import os
import sys

from db_operations import create_db, insert_db_entry
from file_hash import hexhash


def scantree(path, relevant_extensions: list = []):
    """Recursively yield DirEntry objects for given directory."""
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            yield from scantree(entry.path, relevant_extensions)
        else:
            entry_extension = os.path.splitext(entry.name)[-1].lower()
            if entry_extension in set(relevant_extensions):
                yield entry


def main(root_path, db_path, relevant_extensions):
    """Store in a DB, media files hashes"""
    connection, cursor = create_db(db_path)
    files_generator = scantree(root_path, relevant_extensions)
    count_files = 0
    with connection:
        for file in files_generator:
            if file.is_file():
                count_files += 1
                insert_db_entry(file.path, cursor)
                print(f"File analyzed: {count_files}")
            if count_files % 100 == 0:
                connection.commit()
                print(
                    f"Committing to DB - Files analyzed: {count_files} - last commited: {file.path}"
                )
        connection.commit()

    print(f"Task completed: Scanned {count_files} files")


if __name__ == "__main__":
    INPUT_PATH = sys.argv[1]
    DB_PATH = sys.argv[2]
    media_extensions = [
        ".jpeg",
        ".jpg",
        ".cr2",
        ".raf",
        ".zip",
        ".png",
        ".mov",
        ".avi",
        ".mp4",
    ]

    main(
        root_path=INPUT_PATH,
        db_path=DB_PATH,
        relevant_extensions=media_extensions,
    )
