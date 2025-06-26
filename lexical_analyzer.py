import re
from typing import List
from enum import Enum
from file_reader import FileObject
import keyword
from config import fetchSymbolTable

# CONSTANTS:
# Keywords
CONDITIONALS = {c: "CONDITIONAL" for c in ["if", "elif", "else"]}
# Operators
OPERATORS = {op: "OPERATOR" for op in ["+", "-", "*", "/", "=", "**", "//", "%"]}
# Relational Operators
RELOP = {relop: "RELOP" for relop in ['==', '!=', '<', '<=', '>', '>=']}
# Loops
LOOPS = {loop: "LOOP" for loop in ['for', 'while']}


class TokenType(Enum):
    """
    Enumeration of possible token types recognized by the lexical analyzer.

    Each token type corresponds to a syntactic category in the source code.

    Members:
        KEYWORD       - Basic keywords like in, return, etc.
        CONDITIONAL   - Keywords that represent conditions (if, elif, else).
        OPERATOR      - Arithmetic operators (+, -, *, etc.).
        INDENTATION   - Represents an indentation (empty word or tabs).
        RELOP         - Relational operators (==, !=, <, etc.).
        LOOP          - Loop constructs (for, while).
        IDENTIFIER    - Variable or function names.
        CONSTANT      - Numeric constants.
        FUNCTION      - Function definition keyword (def).
        RETURN        - Return definition keyword (return).
        SYMBOL        - Any miscellaneous symbol not otherwise classified.
        SEMICOLON     - Colon character (:) used for block start.
        BLOCK_BEGIN   - Token representing the start of a new indentation block.
        BLOCK_END     - Token representing the end of an indentation block.
        NEWLINE       - Represents the end of a line.
        EOF           - End-of-file marker.
    """
    KEYWORD = "KEYWORD"
    CONDITIONAL = "CONDITIONAL"
    OPERATOR = "OPERATOR"
    INDENTATION = "INDENTATION"
    RELOP = "RELOP"
    LOOP = "LOOP"
    IDENTIFIER = "IDENTIFIER"
    CONSTANT = "CONSTANT"
    FUNCTION = "FUNCTION"
    SYMBOL = "SYMBOL"
    SEMICOLON = "SEMICOLON"
    BLOCK_BEGIN = "BLOCK BEGIN"
    BLOCK_END = "BLOCK END"
    NEWLINE = "NEWLINE"
    EOF = "EOF"


class Token:
    """
    Represents a token in the source code with metadata about its type,
    string value, and source position (line and column numbers).

    Attributes:
        tokenType (TokenType): The category/type of the token (e.g., IDENTIFIER, OPERATOR).
        atr (str): The actual string value of the token.
        lineNo (int): The line number where the token is found.
        colNo (int): The column number in the line where the token starts.
    """

    def __init__(self, tokenType: TokenType, atr: str | float = None, lineNo: int = None, colNo: int = None) -> None:
        self.tokenType = tokenType
        self.atr = atr
        self.lineNo = lineNo
        self.colNo = colNo

    def __repr__(self, indent=0) -> str:
        """
        Returns a formatted string representation of the token.

        Args:
            indent (int): Number of tab characters to prepend.

        Returns:
            str: A human-readable string representing the token.
        """
        return "\t" * indent + f"{self.tokenType.name}: {self.atr} \n"

    def evaluate(self):
        """
        Evaluates the token value using a symbol table (if IDENTIFIER)
        or returns the integer value if it's a constant.

        Returns:
            int or any: Evaluated value of the token.
        """
        if self.tokenType == TokenType.IDENTIFIER:
            return fetchSymbolTable(self.atr)
        else:
            return int(self.atr)


def make_token(tType: TokenType, value: str, line: int = None, col: int = None) -> Token:
    """
    Helper function to create a Token instance.

    Args:
        tType (TokenType): The token's type.
        value (str): The token's value.
        line (int): The line number.
        col (int): The column number.

    Returns:
        Token: A Token object with the provided details.
    """
    return Token(tType, value, line, col)


def token_giver(word: str, line: int = None, col: int = None) -> Token:
    """
    Classifies a word into its appropriate token type using regex and lookup tables.

    Args:
        word (str): The word to classify.
        line (int): The line number where the word appears.
        col (int): The column number where the word appears.

    Returns:
        Token: The generated token corresponding to the word.
    """
    # Keyword
    if word in CONDITIONALS:
        return make_token(TokenType.CONDITIONAL, word, line, col)

    # Loops
    if word in LOOPS:
        return Token(TokenType.LOOP, word, line, col)

    # Indentation
    elif not word:
        return make_token(TokenType.INDENTATION, '\\t', line, col)

    # Operator
    elif word in OPERATORS:
        return make_token(TokenType.OPERATOR, word, line, col)

    # Relational Operator
    elif word in RELOP:
        return make_token(TokenType.RELOP, word, line, col)

    # Semicolon
    elif word == ":":
        return make_token(TokenType.SEMICOLON, word, line, col)

    # def function
    elif word == "def":
        return make_token(TokenType.FUNCTION, word, line, col)

    elif keyword.iskeyword(word):
        return make_token(TokenType.KEYWORD, word, line, col)

    # Identifier
    elif bool(re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', word)) and not keyword.iskeyword(word):
        return make_token(TokenType.IDENTIFIER, word, line, col)

    # Constant (Update later to work for float and exponential numbers)
    elif re.fullmatch(r"-?\d+(\.\d+)?", word):
        return make_token(TokenType.CONSTANT, word, line, col)

    # Default to symbol if none of the above match
    else:
        return make_token(TokenType.SYMBOL, word, line, col)


def lexical_analyzer(inp: FileObject) -> List[Token]:
    """
    Tokenizes the input Python-like source code from a FileObject into a list of tokens.

    - Tracks indentation and generates BLOCK_BEGIN / BLOCK_END tokens accordingly.
    - Recognizes keywords, identifiers, constants, operators, and symbols.
    - Adds NEWLINE tokens at the end of each logical line and an EOF token at the end.

    Args:
        inp (FileObject): An object wrapping source code lines for processing.

    Returns:
        List[Token]: A list of Token objects representing the lexical structure of the source code.

    Raises:
        IndentationError: If an unexpected indentation is found.
    """
    listOfTokens = []
    indent_stack = [0]
    lineNo = 0
    colNo = 0
    for lineNo in range(len(inp)):
        colNo = 0
        line = inp.at(lineNo)
        indent_level = len(line) - len(line.lstrip())
        stripped_line = line.strip()

        # Skip empty lines
        if not stripped_line:
            continue

        # Handle indentation changes
        if indent_level > indent_stack[-1]:
            # Indentation increased - add BLOCK BEGIN
            indent_stack.append(indent_level)
            listOfTokens.append(Token(TokenType.BLOCK_BEGIN, "begin", lineNo))
        elif indent_level < indent_stack[-1]:
            # Indentation decreased - add BLOCK END tokens
            while indent_stack and indent_level < indent_stack[-1]:
                indent_stack.pop()
                listOfTokens.append(Token(TokenType.BLOCK_END, "end", lineNo - 1))

            if indent_level != indent_stack[-1]:
                raise IndentationError(f"unexpected indent at Line {lineNo}, {line.strip()}\n ")
        # Process the actual line content
        pattern = r"==|!=|<=|>=|[A-Za-z_][A-Za-z0-9_]*|-?\d+(?:\.\d+)?|[^\s\w]"
        tokens_in_line = re.findall(pattern, stripped_line)

        for word in tokens_in_line:
            listOfTokens.append(token_giver(word, lineNo, colNo))
            colNo += 1
        listOfTokens.append(Token(TokenType.NEWLINE, "\\n", lineNo, colNo))
        colNo += 1

    # Add remaining BLOCK END tokens at EOF
    while len(indent_stack) > 1:
        indent_stack.pop()
        listOfTokens.append(Token(TokenType.BLOCK_END, "end", lineNo, colNo))
        colNo += 1

    listOfTokens.append(Token(TokenType.EOF, '$', lineNo + 1))
    return listOfTokens
