import os
import sqlite3
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, "..")

from db_operations import create_db, insert_db_entry, path_in_db, read_db_entry
from file_hash import hexhash


class TestPictureDbFunctions(unittest.TestCase):
    def setUp(self):
        self.connection, self.cursor = create_db("test_pictures.db")
        self.file_path = "./test.txt"

    def tearDown(self):
        self.connection.close()
        os.remove("test_pictures.db")

    def test_create_db(self):
        connection, cursor = create_db("test_pictures.db")
        self.assertIsInstance(connection, sqlite3.Connection)
        self.assertIsInstance(cursor, sqlite3.Cursor)

    def test_path_in_db(self):
        # Test if path is not in the DB
        result = path_in_db(self.connection, self.file_path)
        self.assertFalse(result)

        # Test if path is in the DB
        insert_db_entry(self.file_path, self.cursor)
        result = path_in_db(self.connection, self.file_path)
        self.assertTrue(result)

    def test_insert_db_entry(self):
        insert_db_entry(self.file_path, self.cursor)
        result = self.cursor.execute("SELECT path FROM pictures").fetchone()
        self.assertEqual(result, (self.file_path,))

    def test_read_db_entry(self):
        insert_db_entry(self.file_path, self.cursor)
        read_db_entry(self.cursor)

    def test_hexhash(self):
        hexhash_mock = MagicMock(
            return_value="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )
        with unittest.mock.patch("file_hash.hexhash", hexhash_mock):
            insert_db_entry(self.file_path, self.cursor)
            result = self.cursor.execute("SELECT secret FROM pictures").fetchone()
            self.assertEqual(
                result,
                ("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",),
            )


if __name__ == "__main__":
    unittest.main()
