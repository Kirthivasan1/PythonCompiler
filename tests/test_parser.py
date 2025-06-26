import tokenize
import unittest

import AST
from lexical_analyzer import *
from parser import *


class TestParser(unittest.TestCase):
    def validator(self, parser, lNodes, debug=False):
        index = 0

        def _print(msg):
            if debug:
                print(msg)

        def _validate(node, depth=0):
            nonlocal index
            indent = "  " * depth

            if index >= len(lNodes):
                self.fail(f"{indent}Ran out of expected nodes. Last node checked: {node}")

            expected = lNodes[index]

            # ───── Leaf: TokenNode ─────
            if hasattr(node, 'tokenType') and node.tokenType is not None:
                _print(f"{indent}Token: {node.tokenType}, Expected: {expected}\n")
                self.assertEqual(node.tokenType, expected)
                index += 1
                return

            # ───── ExpressionNode ─────
            elif isinstance(node, ExpressionNode):
                _print(f"{indent}Expression: {node.nodeType}, Expected: {expected}\n")
                self.assertEqual(node.nodeType, expected)
                index += 1
                if node.left:
                    _validate(node.left, depth + 1)
                if node.right:
                    _validate(node.right, depth + 1)
                return

            # ───── BinaryExpressionNode ─────
            elif isinstance(node, BinaryExpressionNode):
                _print(f"{indent}BinaryExpr: {AST.CONDITION}, Expected: {expected}\n")
                self.assertEqual(AST.CONDITION, expected)
                index += 1
                if isinstance(node.operator, str):
                    _validate(ExpressionNode(node.operator), depth + 1)
                else:
                    _validate(node.operator, depth + 1)
                _validate(node.left, depth + 1)
                _validate(node.right, depth + 1)
                return


            # ───── IfNode ─────
            elif isinstance(node, IfNode):
                _print(f"{indent}IfNode: {AST.IF_COND}, Expected: {expected}\n")
                self.assertEqual(AST.IF_COND, expected)
                index += 1
                _validate(node.test, depth + 1)
                _validate(node.consequent, depth + 1)
                for (elif_cond, elif_block) in node.elifs:
                    _validate(elif_cond, depth + 1)
                    _validate(elif_block, depth + 1)
                if node.alternate:
                    _validate(node.alternate, depth + 1)
                return

            # ───── WhileNode ─────
            elif isinstance(node, WhileNode):
                _print(f"{indent}WhileLoop: {AST.WHILE_LOOP}, Expected: {expected}\n")
                self.assertEqual(AST.WHILE_LOOP, expected)
                index += 1
                _validate(node.test, depth + 1)
                _validate(node.consequent, depth + 1)
                return

            # ───── ForNode ─────
            elif isinstance(node, ForNode):
                _print(f"{indent}ForLoop: {AST.FOR_LOOP}, Expected: {expected}\n")
                self.assertEqual(AST.FOR_LOOP, expected)
                index += 1
                _validate(node.loopVar, depth + 1)
                _validate(node.iterableExpr[0], depth + 1)
                _validate(node.iterableExpr[1], depth + 1)
                _validate(node.iterableExpr[2], depth + 1)
                # Optionally validate loopVar & iterableExpr if needed
                _validate(node.consequent, depth + 1)
                return

            # ───── FunctionDefNode ─────
            elif isinstance(node, FunctionDefNode):
                _print(f"{indent}FunctionDef: {node.nodeType}, Expected: {expected}\n")
                self.assertEqual(node.nodeType, expected)
                index += 1

                if node.params:
                    _validate(node.params, depth + 1)

                if node.body:
                    _validate(node.body, depth + 1)

                if node.ret:
                    _validate(node.ret, depth + 1)

                return

            # ───── ParamsNode ─────
            elif isinstance(node, ParamsNode):
                _print(f"{indent}Params: {node.nodeType}, Expected: {expected}\n")
                self.assertEqual(node.nodeType, expected)
                index += 1
                for param in node.params:
                    expected_param = lNodes[index]
                    _print(f"{indent}  Token: {param.tokenType}, Expected: {expected_param}\n")
                    self.assertEqual(param.tokenType, expected_param)
                    index += 1
                return

            # ───── FunctionCallNode ─────
            elif isinstance(node, FunctionCallNode):
                _print(f"{indent}FuncCall: {AST.FUNC_CALL}, Expected: {expected}\n")
                self.assertEqual(AST.FUNC_CALL, expected)
                index += 1
                for arg in node.args:
                    _validate(arg, depth + 1)
                return

            # ───── Generic ASTNode ─────
            elif isinstance(node, ASTNode):
                _print(f"\n{indent}ASTNode: {node.nodeType}, Expected: {expected}\n")
                self.assertEqual(node.nodeType, expected)
                index += 1
                for child in node.body:
                    _validate(child, depth + 1)
                return

            else:
                self.fail(f"{indent}Unknown node type or structure: {node}\n")

        _validate(parser)
        self.assertEqual(index, len(lNodes), f"Only matched {index}/{len(lNodes)} nodes\n")

    def test_parser_simple_assignment(self):
        lexer = lexical_analyzer(FileObject(["a = 5"]))
        parser = Parser(lexer).tree
        lNodes = [AST.PROGRAM,
                  AST.STATEMENT_LIST,
                  AST.STATEMENT,
                  AST.ASSIGNMENT,
                  TokenType.OPERATOR,
                  TokenType.IDENTIFIER,
                  TokenType.CONSTANT]
        self.validator(parser, lNodes)

    def test_parser_complex_assignment(self):
        lexer = lexical_analyzer(FileObject(["a = ((5 * 10) + (10 / 2))"]))
        parser = Parser(lexer).tree
        lNodes = [
            AST.PROGRAM,
            AST.STATEMENT_LIST,
            AST.STATEMENT,
            AST.ASSIGNMENT,
            TokenType.OPERATOR,  # '='
            TokenType.IDENTIFIER,  # a
            TokenType.OPERATOR,  # '+'
            TokenType.OPERATOR,  # '*'
            TokenType.CONSTANT,  # 5
            TokenType.CONSTANT,  # 10
            TokenType.OPERATOR,  # '/'
            TokenType.CONSTANT,  # 10
            TokenType.CONSTANT  # 2
        ]

        self.validator(parser, lNodes)

    def test_parser_if_statement(self):
        lexer = lexical_analyzer(FileObject([
            'a = 1',
            'if a < 5:',
            '    a = 5'
        ]))
        parser = Parser(lexer).tree

        lNodes = [
            AST.PROGRAM,
            AST.STATEMENT_LIST,

            # a = 1
            AST.STATEMENT,
            AST.ASSIGNMENT,
            TokenType.OPERATOR,  # '='
            TokenType.IDENTIFIER,  # a
            TokenType.CONSTANT,  # 1

            # if a < 5:
            AST.STATEMENT,
            AST.IF_COND,

            # Test (expression): a < 5
            AST.CONDITION,
            TokenType.OPERATOR,  # <
            TokenType.IDENTIFIER,  # a
            TokenType.CONSTANT,  # 5

            # Consequent: a = 5
            AST.STATEMENT_LIST,
            AST.STATEMENT,
            AST.ASSIGNMENT,
            TokenType.OPERATOR,  # '='
            TokenType.IDENTIFIER,  # a
            TokenType.CONSTANT  # 5
        ]

        self.validator(parser, lNodes)

    def test_parser_if_else_statement(self):
        lexer = lexical_analyzer(FileObject([
            'a = 1',
            'if a < 5:',
            '    a = 5',
            'else:',
            '    a = 1'
        ]))
        parser = Parser(lexer).tree

        lNodes = [
            AST.PROGRAM,
            AST.STATEMENT_LIST,

            # a = 1
            AST.STATEMENT,
            AST.ASSIGNMENT,
            TokenType.OPERATOR,  # '='
            TokenType.IDENTIFIER,  # a
            TokenType.CONSTANT,  # 1

            # if a < 5:
            AST.STATEMENT,
            AST.IF_COND,

            # Test (expression): a < 5
            AST.CONDITION,
            TokenType.OPERATOR,  # <
            TokenType.IDENTIFIER,  # a
            TokenType.CONSTANT,  # 5

            # Consequent: a = 5
            AST.STATEMENT_LIST,
            AST.STATEMENT,
            AST.ASSIGNMENT,
            TokenType.OPERATOR,  # '='
            TokenType.IDENTIFIER,  # a
            TokenType.CONSTANT,  # 5

            # else:
            AST.STATEMENT_LIST,
            AST.STATEMENT,
            AST.ASSIGNMENT,
            TokenType.OPERATOR,  # '='
            TokenType.IDENTIFIER,  # a
            TokenType.CONSTANT  # 1
        ]

        self.validator(parser, lNodes)

    def test_parser_if_elif_statement(self):
        lexer = lexical_analyzer(FileObject([
            'a = 1',
            'if a == 5:',
            '    a = 5',
            'elif a != 5 :',
            '    a = 1'
        ]))
        parser = Parser(lexer).tree

        lNodes = [
            AST.PROGRAM,
            AST.STATEMENT_LIST,

            # a = 1
            AST.STATEMENT,
            AST.ASSIGNMENT,
            TokenType.OPERATOR,  # '='
            TokenType.IDENTIFIER,  # a
            TokenType.CONSTANT,  # 1

            # if a < 5:
            AST.STATEMENT,
            AST.IF_COND,

            # Test (expression): a < 5
            AST.CONDITION,
            TokenType.OPERATOR,  # <
            TokenType.IDENTIFIER,  # a
            TokenType.CONSTANT,  # 5

            # Consequent: a = 5
            AST.STATEMENT_LIST,
            AST.STATEMENT,
            AST.ASSIGNMENT,
            TokenType.OPERATOR,  # '='
            TokenType.IDENTIFIER,  # a
            TokenType.CONSTANT,  # 5

            # elif a != 5:
            AST.CONDITION,
            TokenType.OPERATOR,
            TokenType.IDENTIFIER,
            TokenType.CONSTANT,

            # Consequent: a = 1
            AST.STATEMENT_LIST,
            AST.STATEMENT,
            AST.ASSIGNMENT,
            TokenType.OPERATOR,  # '='
            TokenType.IDENTIFIER,  # a
            TokenType.CONSTANT  # 1
        ]

        self.validator(parser, lNodes)

    def test_parser_if_elif_else_statement(self):
        lexer = lexical_analyzer(FileObject([
            'a = 1',
            'if a == 5:',
            '    a = 5',
            'elif a != 5 :',
            '    a = 1',
            'else:',
            '    a = 10'
        ]))
        parser = Parser(lexer).tree

        lNodes = [
            AST.PROGRAM,
            AST.STATEMENT_LIST,

            # a = 1
            AST.STATEMENT,
            AST.ASSIGNMENT,
            TokenType.OPERATOR,  # '='
            TokenType.IDENTIFIER,  # a
            TokenType.CONSTANT,  # 1

            # if a < 5:
            AST.STATEMENT,
            AST.IF_COND,

            # Test (expression): a < 5
            AST.CONDITION,
            TokenType.OPERATOR,  # <
            TokenType.IDENTIFIER,  # a
            TokenType.CONSTANT,  # 5

            # Consequent: a = 5
            AST.STATEMENT_LIST,
            AST.STATEMENT,
            AST.ASSIGNMENT,
            TokenType.OPERATOR,  # '='
            TokenType.IDENTIFIER,  # a
            TokenType.CONSTANT,  # 5

            # elif a != 5:
            AST.CONDITION,
            TokenType.OPERATOR,
            TokenType.IDENTIFIER,
            TokenType.CONSTANT,

            # Consequent: a = 1
            AST.STATEMENT_LIST,
            AST.STATEMENT,
            AST.ASSIGNMENT,
            TokenType.OPERATOR,  # '='
            TokenType.IDENTIFIER,  # a
            TokenType.CONSTANT,  # 1

            # else
            AST.STATEMENT_LIST,
            AST.STATEMENT,
            AST.ASSIGNMENT,
            TokenType.OPERATOR,  # '='
            TokenType.IDENTIFIER,  # a
            TokenType.CONSTANT  # 10
        ]

        self.validator(parser, lNodes)

    def test_while_loop(self):
        lexer = lexical_analyzer(FileObject([
            "a = 0",
            "while a < 10:",
            "    a = a + 1"
        ]))
        parser = Parser(lexer).tree

        lNodes = [
            AST.PROGRAM,
            AST.STATEMENT_LIST,
            AST.STATEMENT,
            AST.ASSIGNMENT,
            TokenType.OPERATOR,  # '='
            TokenType.IDENTIFIER,  # a
            TokenType.CONSTANT,  # 0

            # while a < 10:
            AST.STATEMENT,
            AST.WHILE_LOOP,

            # test: a < 10
            AST.CONDITION,
            TokenType.OPERATOR,
            TokenType.IDENTIFIER,
            TokenType.CONSTANT,

            # consequent
            AST.STATEMENT_LIST,
            AST.STATEMENT,
            AST.ASSIGNMENT,
            TokenType.OPERATOR,
            TokenType.IDENTIFIER,
            TokenType.OPERATOR,
            TokenType.IDENTIFIER,
            TokenType.CONSTANT
        ]

        self.validator(parser, lNodes)

    def test_func_def_with_return(self):
        lexer = lexical_analyzer(FileObject([
            "def add(x, y):",
            "    return x + y"
        ]))
        parser = Parser(lexer).tree
        lNodes = [
            AST.PROGRAM,
            AST.STATEMENT_LIST,
            AST.STATEMENT,
            AST.FUNC_DEF,
            AST.PARAM,
            TokenType.IDENTIFIER,  # x
            TokenType.IDENTIFIER,  # y
            AST.RETURN,
            TokenType.OPERATOR,  # '+'
            TokenType.IDENTIFIER,
            TokenType.IDENTIFIER
        ]
        self.validator(parser, lNodes)

    def test_func_call(self):
        lexer = lexical_analyzer(FileObject([
            "def add(x,y):",
            "    return x + y",
            "a = 1",
            "b = 2",
            "add(a,b)"
        ]))
        parser = Parser(lexer).tree
        lNodes = [
            AST.PROGRAM,
            AST.STATEMENT_LIST,
            AST.STATEMENT,
            AST.FUNC_DEF,

            # def add(x,y):
            AST.PARAM,
            TokenType.IDENTIFIER,  # x
            TokenType.IDENTIFIER,  # y

            # return x + y
            AST.RETURN,
            TokenType.OPERATOR,  # '+'
            TokenType.IDENTIFIER,
            TokenType.IDENTIFIER,

            # a = 1
            AST.STATEMENT,
            AST.ASSIGNMENT,
            TokenType.OPERATOR,
            TokenType.IDENTIFIER,
            TokenType.CONSTANT,

            # b = 2
            AST.STATEMENT,
            AST.ASSIGNMENT,
            TokenType.OPERATOR,
            TokenType.IDENTIFIER,
            TokenType.CONSTANT,

            # add(a,b)
            AST.STATEMENT,
            AST.FUNC_CALL,
            TokenType.IDENTIFIER,
            TokenType.IDENTIFIER
        ]

        self.validator(parser, lNodes)

    def test_assignment_with_functionCall(self):
        lexer = lexical_analyzer(FileObject([
            "def add(x,y):",
            "    return x + y",
            "a = 1",
            "b = 2",
            "c = add(a,b)"
        ]))
        parser = Parser(lexer).tree
        lNodes = [
            AST.PROGRAM,
            AST.STATEMENT_LIST,
            AST.STATEMENT,
            AST.FUNC_DEF,

            # def add(x,y):
            AST.PARAM,
            TokenType.IDENTIFIER,  # x
            TokenType.IDENTIFIER,  # y

            # return x + y
            AST.RETURN,
            TokenType.OPERATOR,  # '+'
            TokenType.IDENTIFIER,
            TokenType.IDENTIFIER,

            # a = 1
            AST.STATEMENT,
            AST.ASSIGNMENT,
            TokenType.OPERATOR,
            TokenType.IDENTIFIER,
            TokenType.CONSTANT,

            # b = 2
            AST.STATEMENT,
            AST.ASSIGNMENT,
            TokenType.OPERATOR,
            TokenType.IDENTIFIER,
            TokenType.CONSTANT,

            # c = add(a,b)
            AST.STATEMENT,
            AST.ASSIGNMENT,
            TokenType.OPERATOR,
            TokenType.IDENTIFIER,
            AST.FUNC_CALL,
            TokenType.IDENTIFIER,
            TokenType.IDENTIFIER
        ]

        self.validator(parser, lNodes)

    def test_for_loop(self):
        lexer = lexical_analyzer(FileObject([
            'for i in range(10, 0, -0.1):',
            '    print(i)'
        ]))
        parser = Parser(lexer).tree
        lNodes = [
            AST.PROGRAM,
            AST.STATEMENT_LIST,
            AST.STATEMENT,
            AST.FOR_LOOP,

            # iterVariable
            TokenType.IDENTIFIER,
            # start
            TokenType.CONSTANT,
            # stop
            TokenType.CONSTANT,
            # step
            TokenType.CONSTANT,

            # Consequent
            AST.STATEMENT_LIST,
            AST.STATEMENT,
            AST.FUNC_CALL,
            TokenType.IDENTIFIER
        ]

        self.validator(parser, lNodes, True)


if __name__ == '__main__':
    unittest.main()
