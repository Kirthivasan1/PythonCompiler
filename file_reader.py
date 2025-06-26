from typing import List


class FileObject:
    """
    A helper class to represent the contents of a file and provide controlled line-by-line,
    character-by-character access for parsing or tokenization purposes.

    Attributes:
        lines (List[str]): The list of lines read from the file.
        currentLine (int): Index of the current line being processed.
        lineNum (int): Current line number (used for external referencing).
        colNum (int): Current column number in the current line.
    """
    def __init__(self, lines: List[str] = None):
        """
        Initializes the FileObject with lines from a file.

        Args:
            lines (List[str], optional): A list of strings, each representing a line from the source file.
        """
        self.lines = lines
        self.currentLine = 0
        self.lineNum = 0
        self.colNum = 0

    def at(self, lineNo):
        """
        Returns the content at the specified line number.

        Args:
            lineNo (int): The line number to retrieve.

        Returns:
            str: The line at the given line number.
        """
        return self.lines[lineNo]

    def __len__(self):
        """
        Returns the number of lines in the file.

        Returns:
            int: The number of lines.
        """
        return len(self.lines)

    def current_char(self):
        """
        Returns the current character at the pointer (lineNum, colNum).

        Returns:
            str: The character at the current file position.
        """
        return self.lines[self.lineNum][self.colNum]


def file_reader(inp: str) -> FileObject:
    """
    Reads the input file and returns a FileObject containing the lines of the file.

    Args:
        inp (str): The path to the input file.

    Returns:
        FileObject: An object representing the contents of the file for further processing.
    """
    text = []
    with open(inp, "r") as f:
        for line in f:
            text.append(line.rstrip('\n'))
    fileObj = FileObject(text)
    return fileObj
