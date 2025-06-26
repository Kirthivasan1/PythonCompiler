import unittest
from lexical_analyzer import *


class TestLexicalAnalyzer(unittest.TestCase):

    def list_asserter(self, lexer, lTt, lAtr):
        for index in range(len(lexer)):
            self.asserter(lexer[index], lTt[index], lAtr[index])

    def asserter(self, word: Token, tt: TokenType, atr: str):
        self.assertEqual(word.tokenType, tt)
        self.assertEqual(word.atr, atr)

    def test_lexer_simple_assignment(self):
        lexer = lexical_analyzer(FileObject(["a = 5"]))
        lTokenTypes = [
            TokenType.IDENTIFIER, TokenType.OPERATOR, TokenType.CONSTANT,
            TokenType.NEWLINE, TokenType.EOF
        ]
        lAttributes = ['a', '=', '5', '\\n', '$']
        self.list_asserter(lexer, lTokenTypes, lAttributes)

    def test_lexer_complex_assignment(self):
        lexer = lexical_analyzer(FileObject(["a = 5*10.2 + 10 / 2"]))
        lTokenTypes = [
            TokenType.IDENTIFIER, TokenType.OPERATOR, TokenType.CONSTANT, TokenType.OPERATOR, TokenType.CONSTANT, TokenType.OPERATOR, TokenType.CONSTANT, TokenType.OPERATOR, TokenType.CONSTANT,
            TokenType.NEWLINE, TokenType.EOF
        ]
        lAttributes = ['a', '=', '5', '*', '10.2', '+', '10', '/', '2', '\\n', '$']
        self.list_asserter(lexer, lTokenTypes, lAttributes)

    def test_lexer_if_elif_else(self):
        lexer = lexical_analyzer(FileObject([
            'if ( a == 5 ):',
            '    a = 1',
            'elif ( a == 6 ):',
            '    a = 2',
            'else :',
            '    a = 3'
        ]))
        lTokenTypes = [
            TokenType.CONDITIONAL, TokenType.SYMBOL, TokenType.IDENTIFIER, TokenType.RELOP,
            TokenType.CONSTANT, TokenType.SYMBOL, TokenType.SEMICOLON, TokenType.NEWLINE,
            TokenType.BLOCK_BEGIN, TokenType.IDENTIFIER, TokenType.OPERATOR, TokenType.CONSTANT,
            TokenType.NEWLINE, TokenType.BLOCK_END,
            TokenType.CONDITIONAL, TokenType.SYMBOL, TokenType.IDENTIFIER, TokenType.RELOP,
            TokenType.CONSTANT, TokenType.SYMBOL, TokenType.SEMICOLON, TokenType.NEWLINE,
            TokenType.BLOCK_BEGIN, TokenType.IDENTIFIER, TokenType.OPERATOR, TokenType.CONSTANT,
            TokenType.NEWLINE, TokenType.BLOCK_END,
            TokenType.CONDITIONAL, TokenType.SEMICOLON, TokenType.NEWLINE,
            TokenType.BLOCK_BEGIN, TokenType.IDENTIFIER, TokenType.OPERATOR,
            TokenType.CONSTANT, TokenType.NEWLINE, TokenType.BLOCK_END,
            TokenType.EOF
        ]
        lAttributes = [
            'if', '(', 'a', '==', '5', ')', ':', '\\n', 'begin', 'a', '=', '1', '\\n', 'end',
            'elif', '(', 'a', '==', '6', ')', ':', '\\n', 'begin', 'a', '=', '2', '\\n', 'end',
            'else', ':', '\\n', 'begin', 'a', '=', '3', '\\n', 'end', '$'
        ]
        self.list_asserter(lexer, lTokenTypes, lAttributes)

    def test_function_definition(self):
        lexer = lexical_analyzer(FileObject([
            'def add ( x , y ):',
            '    return x + y'
        ]))
        lTokenTypes = [
            TokenType.FUNCTION, TokenType.IDENTIFIER, TokenType.SYMBOL, TokenType.IDENTIFIER,
            TokenType.SYMBOL, TokenType.IDENTIFIER, TokenType.SYMBOL, TokenType.SEMICOLON,
            TokenType.NEWLINE,
            TokenType.BLOCK_BEGIN, TokenType.KEYWORD, TokenType.IDENTIFIER, TokenType.OPERATOR,
            TokenType.IDENTIFIER, TokenType.NEWLINE, TokenType.BLOCK_END,
            TokenType.EOF
        ]
        lAttributes = [
            'def', 'add', '(', 'x', ',', 'y', ')', ':', '\\n',
            'begin', 'return', 'x', '+', 'y', '\\n', 'end', '$'
        ]
        self.list_asserter(lexer, lTokenTypes, lAttributes)

    def test_nested_blocks(self):
        lexer = lexical_analyzer(FileObject([
            'if a == 1:',
            '    if b == 2:',
            '        c = 3',
            '    d = 4',
            'e = 5'
        ]))
        lTokenTypes = [
            TokenType.CONDITIONAL, TokenType.IDENTIFIER, TokenType.RELOP, TokenType.CONSTANT,
            TokenType.SEMICOLON, TokenType.NEWLINE,
            TokenType.BLOCK_BEGIN,
            TokenType.CONDITIONAL, TokenType.IDENTIFIER, TokenType.RELOP, TokenType.CONSTANT,
            TokenType.SEMICOLON, TokenType.NEWLINE,
            TokenType.BLOCK_BEGIN, TokenType.IDENTIFIER, TokenType.OPERATOR, TokenType.CONSTANT,
            TokenType.NEWLINE, TokenType.BLOCK_END,
            TokenType.IDENTIFIER, TokenType.OPERATOR, TokenType.CONSTANT, TokenType.NEWLINE,
            TokenType.BLOCK_END,
            TokenType.IDENTIFIER, TokenType.OPERATOR, TokenType.CONSTANT, TokenType.NEWLINE,
            TokenType.EOF
        ]
        lAttributes = [
            'if', 'a', '==', '1', ':', '\\n',
            'begin',
            'if', 'b', '==', '2', ':', '\\n',
            'begin', 'c', '=', '3', '\\n', 'end',
            'd', '=', '4', '\\n',
            'end',
            'e', '=', '5', '\\n',
            '$'
        ]
        self.list_asserter(lexer, lTokenTypes, lAttributes)

    def test_unrecognized_symbols(self):
        lexer = lexical_analyzer(FileObject(["x @ y"]))
        lTokenTypes = [
            TokenType.IDENTIFIER, TokenType.SYMBOL, TokenType.IDENTIFIER,
            TokenType.NEWLINE, TokenType.EOF
        ]
        lAttributes = ['x', '@', 'y', '\\n', '$']
        self.list_asserter(lexer, lTokenTypes, lAttributes)


if __name__ == '__main__':
    unittest.main()
