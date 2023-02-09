import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, "..")

from directory_cleanup import delete_empty_dirs


class TestDirectoryCleanup(unittest.TestCase):
    def setUp(self):
        self.test_root = tempfile.mkdtemp()
        with open(os.path.join(self.test_root, "test.txt"), "w", encoding="utf-8") as f:
            f.write("Test")

    def tearDown(self):
        shutil.rmtree(self.test_root)

    def test_delete_empty_dirs(self):
        # Create test directories
        subdir1 = os.path.join(self.test_root, "subdir1")
        os.mkdir(subdir1)
        subdir2 = os.path.join(subdir1, "subdir2")
        os.mkdir(subdir2)
        subdir3 = os.path.join(subdir2, "subdir3")
        os.mkdir(subdir3)
        eadir = os.path.join(subdir3, "@eaDir")
        os.mkdir(eadir)

        # Test delete_empty_dirs
        delete_empty_dirs(self.test_root)

        # Assert that only the root directory remains
        self.assertTrue(os.path.isdir(self.test_root))
        self.assertFalse(os.path.exists(subdir1))
        self.assertFalse(os.path.exists(subdir2))
        self.assertFalse(os.path.exists(subdir3))
        self.assertFalse(os.path.exists(eadir))


if __name__ == "__main__":
    unittest.main()
