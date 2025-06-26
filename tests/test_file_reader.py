from file_reader import *
from tempfile import TemporaryDirectory
import os
import unittest


class TestFileReader(unittest.TestCase):
    def test_file_reader_reads_content(self):
        with TemporaryDirectory() as tempDirName:
            file_path = os.path.join(tempDirName, "main.py")
            with open(file_path, 'w') as f:
                f.write("a = 5")

            reader = file_reader(file_path)
            self.assertEqual(reader.lines, ['a = 5'])

    def test_file_reader_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            file_reader("non_existent.txt")


if __name__ == '__main__':
    unittest.main()
