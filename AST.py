from enum import Enum
from lexical_analyzer import Token, TokenType
from typing import List
from config import *


class AST(Enum):
    PROGRAM = "PROGRAM"
    STATEMENT_LIST = "STATEMENT_LIST"
    STATEMENT = "STATEMENT"
    ASSIGNMENT = "ASSIGNMENT"
    EXPRESSION = "EXPRESSION"
    TERM = "TERM"
    FACTOR = "FACTOR"
    IF_COND = "IF_COND"
    WHILE_LOOP = "WHILE_LOOP"
    FOR_LOOP = "FOR_LOOP"
    FUNC_DEF = "FUNC_DEF"
    PARAM = "PARAM"
    FUNC_CALL = "FUNC_CALL"
    ARG_LIST = "ARG_LIST"
    RETURN = "RETURN"
    CONDITION = "CONDITION"
    RELOP = "RELOP"


class ASTNode:

    def __init__(self, nodeType: AST):
        self.nodeType: AST = nodeType  # e.g., "ASSIGNMENT", "IF", "LOOP"
        self.loc = {'start': 0, 'end': 0}
        self.range = [0, 0]
        self.body: List[Token | ASTNode | ExpressionNode] = []  # For nested expressions/statements

    def add(self, item):
        if item is not None:
            self.body.append(item)

    def __repr__(self, indent=0):
        prefix = "  " * indent
        repr_str = f"{prefix}{self.nodeType.name}"  # or str(self.nodeType) if not enum
        repr_str += "\n"
        for item in self.body:
            if isinstance(item, ASTNode):
                repr_str += item.__repr__(indent + 1)
            else:
                repr_str += f"{'  ' * (indent + 1)}{str(item)}\n"
        return repr_str


class ExpressionNode(ASTNode):
    def __init__(self, operator: str | int):
        super().__init__(AST.EXPRESSION)
        if isinstance(operator, int) or (isinstance(operator, str) and operator.isdigit()):
            self.nodeType = TokenType.CONSTANT
        elif isinstance(operator, str) and operator.isidentifier():
            self.nodeType = TokenType.IDENTIFIER
        else:
            self.nodeType = TokenType.OPERATOR
        self.value = operator
        self.left = None
        self.right = None

    def __repr__(self, level=0):
        indent = '\t' * level
        result = f"{indent}{self.nodeType}: {self.value}\n"

        child_level = level + 1
        if self.left:
            left_repr = self.left.__repr__(child_level).rstrip('\n')
            result += f"{left_repr}\n"

        if self.right:
            right_repr = self.right.__repr__(child_level).rstrip('\n')
            result += f"{right_repr}\n"

        return result

    def format_expr(self, level=0):
        if self.left is None and self.right is None:
            return str(self.value)

        left_expr = self.left.format_expr() if isinstance(self.left, ExpressionNode) else self.left.atr
        right_expr = self.right.format_expr() if isinstance(self.right, ExpressionNode) else self.right.atr

        # Add parentheses around right/left only if they are operator nodes
        if isinstance(self.left, ExpressionNode) and self.left.nodeType == TokenType.OPERATOR:
            left_expr = f"({left_expr})"
        if isinstance(self.right, ExpressionNode) and self.right.nodeType == TokenType.OPERATOR:
            right_expr = f"({right_expr})"

        return f"{left_expr} {self.value} {right_expr}"

    def evaluate(self):
        if self.nodeType == TokenType.CONSTANT:
            return int(self.value)

        if self.nodeType == TokenType.IDENTIFIER:
            return fetchSymbolTable(self.value)

        if self.nodeType == TokenType.OPERATOR:
            left_val = self.left.evaluate()
            right_val = self.right.evaluate()

            if self.value == '+':
                return left_val + right_val
            elif self.value == '-':
                return left_val - right_val
            elif self.value == '*':
                return left_val * right_val
            elif self.value == '/':
                return left_val / right_val
            elif self.value == '>':
                return left_val > right_val
            elif self.value == '<':
                return left_val < right_val
            elif self.value == '==':
                return left_val == right_val

        raise NotImplementedError(f"Unknown node type: {self.nodeType}")


def expression_tree_builder(operator: Token | str, left: Token | str | ExpressionNode,
                            right: Token | str | ExpressionNode) -> ExpressionNode:
    root = ExpressionNode(operator.atr) if type(operator) == Token else ExpressionNode(operator)
    root.left = left if type(left) == Token else ExpressionNode(left) if type(
        left) == str else left
    root.right = right if type(right) == Token else ExpressionNode(right) if type(
        right) == str else right
    return root


class BinaryExpressionNode(ASTNode):
    def __init__(self, operator: ExpressionNode = None, left=None, right=None):
        super().__init__(AST.CONDITION)
        self.operator = operator
        self.left = left
        self.right = right
        self.result = None

    def __repr__(self, indent=0):
        prefix = "  " * indent
        result = f"{prefix}BINARY_EXPR\n"
        result += f"{prefix}  Operator: {self.operator}\n"
        result += f"{prefix}  Left:\n"
        result += self.left.__repr__(indent + 2) if self.left else f"{prefix}    <empty>\n"
        result += f"{prefix}  Right:\n"
        result += self.right.__repr__(indent + 2) if self.right else f"{prefix}    <empty>\n"
        return result

    def evaluate(self):

        self.result = None
        left_val = self.left.evaluate()
        right_val = self.right.evaluate()

        # Perform the comparison
        if self.operator.value == '==':
            self.result = left_val == right_val
        elif self.operator.value == '!=':
            self.result = left_val != right_val
        elif self.operator.value == '<':
            self.result = left_val < right_val
        elif self.operator.value == '<=':
            self.result = left_val <= right_val
        elif self.operator.value == '>':
            self.result = left_val > right_val
        elif self.operator.value == '>=':
            self.result = left_val >= right_val
        else:
            raise ValueError(f"Unknown operator: {self.operator.value}")
        return self.result


class IfNode(ASTNode):
    def __init__(self, test: BinaryExpressionNode = None, consequent: ASTNode = None, alternate: ASTNode = None):
        super().__init__(AST.IF_COND)
        if alternate is None:
            alternate = []
        if consequent is None:
            consequent = []
        self.test = test
        self.consequent = consequent
        self.elifs = []
        self.alternate = alternate

    def __repr__(self, indent=0):
        prefix = "  " * indent
        result = f"{prefix}IF_COND\n"

        # Test condition
        result += f"{prefix}  Test:\n"
        result += self.test.__repr__(indent + 2) if self.test else f"{prefix}    <empty>\n"

        # Consequent block
        result += f"{prefix}  Consequent:\n"
        result += self.consequent.__repr__(indent + 2) if self.consequent else f"{prefix}    <empty>\n"

        # Elif blocks (if any)
        if hasattr(self, 'elifs') and self.elifs:
            for idx, (cond, block) in enumerate(self.elifs):
                result += f"{prefix}  Elif {idx + 1}:\n"
                result += f"{prefix}    Test:\n"
                result += cond.__repr__(indent + 3) if cond else f"{prefix}      <empty>\n"
                result += f"{prefix}    Consequent:\n"
                result += block.__repr__(indent + 3) if block else f"{prefix}      <empty>\n"

        # Else block (if any)
        if self.alternate and self.alternate.body:
            result += f"{prefix}  Alternate:\n"
            result += self.alternate.__repr__(indent + 2)

        return result


class WhileNode(ASTNode):
    def __init__(self, test: BinaryExpressionNode = None, consequent: ASTNode = None):
        super().__init__(AST.WHILE_LOOP)
        if consequent is None:
            consequent = []
        self.test = test
        self.consequent = consequent

    def __repr__(self, indent=0):
        prefix = "  " * indent
        result = f"{prefix}WHILE_LOOP\n"

        # Test condition
        result += f"{prefix}  Test:\n"
        result += self.test.__repr__(indent + 2) if self.test else f"{prefix}    <empty>\n"

        # Consequent block
        result += f"{prefix}  Consequent:\n"
        result += self.consequent.__repr__(indent + 2) if self.consequent else f"{prefix}    <empty>\n"
        return result


class ParamsNode(ASTNode):
    def __init__(self) -> None:
        super().__init__(AST.PARAM)
        self.params: List[Token] = []

    def add(self, identifier: Token) -> None:
        self.params.append(identifier)

    def __repr__(self, indent=0):
        prefix = " " * indent
        return f"{prefix}{self.params}\n"


class FunctionDefNode(ASTNode):

    def __init__(self, identifier: str, params: ParamsNode | None, body: ASTNode, ret: ASTNode | ExpressionNode):
        super().__init__(AST.FUNC_DEF)
        self.identifier = identifier
        self.params = params
        self.body = body
        self.ret = ret

    def __repr__(self, indent=0):
        prefix = "  " * indent
        result = f"{prefix}FUNCTION DECLARATION\n"
        # Function name
        result += f"{prefix}  Name: {self.identifier}\n"

        # Parameters
        if self.params:
            result += f"{prefix}  Params: {self.params.params}\n"

        # Consequent block
        if self.body:
            result += f"{prefix}  Body:\n"
            result += self.body.__repr__(indent + 2)

        # Return statement
        if self.ret:
            result += f"  {self.ret.__repr__(indent)}\n"
        return result


class FunctionCallNode(ASTNode):
    def __init__(self, funcName: str = None, args=None) -> None:
        super().__init__(AST.FUNC_CALL)
        if args is None:
            args = []
        self.funcName = funcName
        self.args = args if args else []

    def __repr__(self, indent=0):
        prefix = "  " * indent
        result = f"{prefix}FUNC_CALL\n"
        result += f"{prefix}  Function: {self.funcName}\n"
        if self.args:
            result += f"{prefix}  Arguments:\n"
            for arg in self.args:
                result += f"{prefix}    {arg}\n"
        return result


class ForNode(ASTNode):
    def __init__(self, loopVar: str, iterableExpr: List[int], consequent: ASTNode) -> None:
        super().__init__(AST.FOR_LOOP)
        self.loopVar = loopVar
        self.iterableExpr = iterableExpr
        self.consequent = consequent

    def __repr__(self, indent=0):
        prefix = "  " * indent
        result = f"{prefix}FOR_LOOP\n"
        result += f"{prefix}  Loop Variable: {self.loopVar}\n"
        result += f"{prefix}  Start, Stop, Step: {self.iterableExpr}\n"
        result += f"{prefix}  Body:\n"
        result += self.consequent.__repr__(indent + 2)
        return result
