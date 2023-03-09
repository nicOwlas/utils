import hashlib
import os
import shutil
import sys
import tempfile
import unittest

from PIL import Image, ImageDraw

sys.path.insert(0, "..")
from file_hash import dhash, hexhash


class TestPictureDbFunctions(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory and some files to use in the tests
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = {"test1.txt": b"test1", "test2.txt": b"test2"}
        for file_name, file_data in self.test_files.items():
            file_path = os.path.join(self.temp_dir, file_name)
            with open(file_path, "wb") as f:
                f.write(file_data)

        # Create an image to test the perceptual hash
        # Define the size of the image
        width = 400
        height = 400

        # Create a new image with a white background
        image = Image.new("RGB", (width, height), "white")

        # Draw a blue square in the center of the image
        square_size = 200
        x0 = (width - square_size) // 2
        y0 = (height - square_size) // 2
        x1 = x0 + square_size
        y1 = y0 + square_size
        draw = ImageDraw.Draw(image)
        draw.rectangle((x0, y0, x1, y1), fill="blue")

        # Save the image to disk
        image.save(os.path.join(self.temp_dir, "blue_square.png"))

    def tearDown(self):
        # Remove the temporary directory and files created in setUp
        shutil.rmtree(self.temp_dir)

    def test_hexhash(self):
        # Test hexhash function
        file_hashes = {
            "test1.txt": "1b4f0e9851971998e732078544c96b36c3d01cedf7caa332359d6f1d83567014",
            "test2.txt": "60303ae22b998861bce3b28f33eec1be758a213c86c93c076dbe9f558c11c752",
        }
        for file_name, file_data in self.test_files.items():
            file_path = os.path.join(self.temp_dir, file_name)
            self.assertEqual(hexhash(file_path), file_hashes[file_name])

    def test_dhash(self):
        # Test perceptual hash
        file_path = os.path.join(self.temp_dir, "blue_square.png")
        self.assertEqual(
            str(dhash(file_path)),
            "0000000800000418245a245a245a245a245a245a245a245a0418000000080000",
        )

    def test_invalid_file(self):
        with self.subTest(file_type="invalid"):
            file_path = "test.txt"
            with self.assertRaises(Exception):
                result = dhash(file_path)


if __name__ == "__main__":
    unittest.main()
