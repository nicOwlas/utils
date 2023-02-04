"""
Store files' hash in a DB
"""
import os
import sys

from db_operations import create_db, insert_db_entry, path_in_db


def scantree(path, relevant_extensions: list):
    """Recursively yield DirEntry objects for given directory."""
    for entry in os.scandir(path):
        try:
            if entry.is_dir(follow_symlinks=False):
                yield from scantree(entry.path, relevant_extensions)
            else:
                entry_extension = os.path.splitext(entry.name)[-1].lower()
                if entry_extension in set(relevant_extensions):
                    yield entry
        except PermissionError:
            # No access to file or folder
            continue


def main(root_path, db_path, relevant_extensions):
    """Store in a DB, media files hashes"""
    connection, cursor = create_db(db_path)
    files_generator = scantree(root_path, relevant_extensions)
    count_files = 0
    added_files = 0
    with connection:
        for file in files_generator:
            if file.is_file():
                count_files += 1
                print(f"Analyzing file #{count_files}")
                if not path_in_db(connection, file.path):
                    added_files += 1
                    insert_db_entry(file.path, cursor)
                    print(f"Files added: {added_files}")
            if count_files % 100 == 0:
                connection.commit()
                print(
                    f"Committing to DB - Files analyzed: {count_files} - last commited: {file.path}"
                )
        connection.commit()

    print(f"Task completed: Scanned {count_files} files. Added {added_files} files")


if __name__ == "__main__":
    INPUT_PATH = sys.argv[1]
    DB_PATH = sys.argv[2]
    media_extensions = [
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

    main(
        root_path=INPUT_PATH,
        db_path=DB_PATH,
        relevant_extensions=media_extensions,
    )
