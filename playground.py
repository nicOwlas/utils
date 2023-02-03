"""Play with yield"""
import hashlib
import json
import os
import sqlite3


def create_db(db_name: str):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS pictures (path TEXT UNIQUE, secret TEXT)"
    )
    return connection, cursor


def hash_bytestr_iter(bytesiter, hasher, ashexstr=False):
    for block in bytesiter:
        hasher.update(block)
    return hasher.hexdigest() if ashexstr else hasher.digest()


def file_as_blockiter(afile, blocksize=65536):
    with afile:
        block = afile.read(blocksize)
        while len(block) > 0:
            yield block
            block = afile.read(blocksize)


def hexhash(file_path: str):
    """Return file hash"""
    return hash_bytestr_iter(
        file_as_blockiter(open(file_path, "rb")),
        hashlib.sha256(),
        ashexstr=True,
    )


def create_db_entry(file_path: str, cursor) -> None:
    """Add an entry to the DB"""
    cursor.execute(
        "INSERT INTO pictures VALUES (?, ?)", (file_path, hexhash(file_path))
    )


def read_db_entry(cursor):
    """Display DB content"""
    rows = cursor.execute("SELECT path, secret FROM pictures").fetchall()
    print(rows)


def list_of_files(input_path: str) -> list:
    """test os.walk"""
    for directory_path, _, files in os.walk(input_path):
        for file in files:
            yield os.path.join(directory_path, file)


def export_file_names(file_name: str, output_file: str):
    """export file names"""
    print(file_name)
    # try:
    #     with open(output_file, "r", encoding="utf-8") as file:
    #         data = json.load(file)
    # except FileNotFoundError:
    #     with open(output_file, "w", encoding="utf-8") as file:
    #         json.dump(file_names, file, indent=4)
    # else:
    #     data.update(file_names)
    #     with open(output_file, "w", encoding="utf-8") as file:
    #         json.dump(data, file, indent=4)
    # file.write()


if __name__ == "__main__":
    sample_file_path = "/Users/nicolas/Downloads/image.jpeg"
    connection, cursor = create_db("pictures.db")
    create_db_entry(sample_file_path, cursor)
    read_db_entry(cursor)

    # output_file = "/Users/nicolas/Downloads/filenames.json"
    # file_generator = list_of_files(path)
    # for file in file_generator:
    #     export_file_names(file_name=file, output_file=output_file)
