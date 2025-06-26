# Grammar
from typing import Any

from AST import *
from AST import ASTNode
from lexical_analyzer import Token, TokenType
from config import *


class GrammarError(Exception):
    """
    Exception raised for syntax errors encountered during parsing.

    Attributes:
        token (Token): The token where the error occurred.
        expected (str): A string describing the expected token or syntax.
    """

    def __init__(self, message: str, token: Token = None, expected: str = None) -> None:
        self.token = token
        self.expected = expected
        error_message = f"Grammar Error: {message}"
        if token:
            error_message += f" | Found: {token.tokenType} : '{token.atr}'"
            error_message += f" at line no {token.lineNo}, {token.colNo}"
        if expected:
            error_message += f" | Expected: {expected}"
        super().__init__(error_message)


class Parser:
    """
    Recursive-descent parser for a simplified programming language.

    Parses a list of tokens and builds an Abstract Syntax Tree (AST) while optionally
    evaluating expressions in-line based on the symbol table.
    """
    """
    <program>        -> <statement_list>
    <statement_list> -> <statement>
    <statement>      -> <if_statement>
                     | <while_loop>
    <assignment>     -> IDENTIFIER '=' <expression> | IDENTIFIER '=' <function_call>
    <expression>     -> <term> <expression_1>
    <expression_1>   -> '+' <term> <expression_1>
                     | '-' <term> <expression_1>
                     | None
    <term>           -> <factor> <term_1>
    <term_1>         -> '*' <factor> <term_1>
                     | '/' <factor> <term_1>
                     | None
    <factor>         -> '(' <expression> ')'
                     | NUMBER
                     | IDENTIFIER
    <while_loop>     -> 'while' '(' <condition> ')' '{' <statement_list> '}'
    <condition>      -> <expression> <relop> <expression>
    <relop>          -> '==' | '!=' | '<' | '<=' | '>' | '>='

    In the future, try to implement this grammar by reading a text file and if possible try to eliminate left
    recursion and use that grammar
    """

    def __init__(self, listOfTokens: List[Token]) -> None:
        """
        Initializes the parser with a list of tokens.

        Args:
           listOfTokens (List[Token]): The tokenized input from the lexer.
        """
        self.tokens = listOfTokens
        self.pos = 0
        self.lookahead: Token = self.tokens[self.pos] if self.tokens else None
        self.listOfExpressions = []
        self.tree = None
        self.should_evaluate = True

        self.program()

    def match(self):
        """
        Advances the token pointer to the next token.
        """
        # if self.debug:
        #     old_token = f"{self.lookahead.tokenType}:'{self.lookahead.atr}'" if self.lookahead else "None"

        if self.pos + 1 < len(self.tokens):
            self.pos += 1
            self.lookahead = self.tokens[self.pos]
        else:
            self.lookahead = None  # End of input

    def check(self, **kwargs: Any) -> bool:
        """
        Checks if the current token matches the provided attributes.

        Keyword Args:
            tokenType (TokenType): Optional token type to match.
            atr (str): Optional attribute string to match.

        Returns:
            bool: True if current token matches all provided attributes.
        """
        if self.lookahead is None:
            return False

        for key, value in kwargs.items():
            if key == 'tokenType':
                return self.lookahead.tokenType == value
            elif key == 'atr':
                return self.lookahead.atr == value
        return False

    def error_grammar(self, expected=None):
        raise GrammarError("Invalid syntax", self.lookahead, expected)

    def consume(self, **kwargs: Any) -> Token | None:
        """
        Consumes the current token if it matches the given criteria.

        Keyword Args:
            tokenType (TokenType): Token type to match.
            atr (str): Attribute string to match.

        Returns:
            Optional[Token]: The consumed token if matched, else None.
        """
        if not kwargs:
            token = self.lookahead
            self.match()
            return token  # Return the token, still advances the parser
        if not self.check(**kwargs):
            return None
        else:
            token = self.lookahead
            self.match()
            return token

    def consume_error(self, **kwargs) -> Token | None:
        """
        Tries to consume a token matching the given criteria. Raises GrammarError if it fails.

        Returns:
            Token: The successfully matched token.

        Raises:
            GrammarError: If no matching token is found.
        """
        key, value = list(kwargs.items())[0]
        if len(kwargs.items()) == 2:
            message = kwargs['message']
        else:
            message = value

        # Special handling for BLOCK_END at EOF
        if (key == 'tokenType' and value == TokenType.BLOCK_END and
                self.check(tokenType=TokenType.EOF)):
            return None

        temp = self.consume(**{key: value})
        if not temp:
            self.error_grammar(expected=message)
        else:
            return temp

    def program(self) -> None:
        """
        Parses the root <program> rule and initializes the AST root.
        """
        self.tree = ASTNode(AST.PROGRAM)
        self.tree.add(self.statement_list())

    def statement_list(self) -> ASTNode:
        """
        Parses a list of statements, accounting for newlines and indentation blocks.

        Returns:
            ASTNode: Node representing a list of statements.
        """
        stmnt_list = ASTNode(AST.STATEMENT_LIST)
        iteration_count = 0

        while (not self.check(tokenType=TokenType.EOF) and
               not self.check(tokenType=TokenType.BLOCK_END) and
               self.lookahead is not None):

            iteration_count += 1
            if iteration_count > 100:  # Safety check
                print("ERROR: Too many iterations in statement_list, breaking to prevent infinite loop")
                break

            stmt = self.statement()
            if stmt:
                stmnt_list.add(stmt)

            # Try to consume newline if present
            if self.check(tokenType=TokenType.NEWLINE):
                self.consume(tokenType=TokenType.NEWLINE)

            # If we encounter BLOCK_END or EOF, break (don't consume here)
            if self.check(tokenType=TokenType.BLOCK_END) or self.check(tokenType=TokenType.EOF):
                break

            # Safety check - if statement() returned None, and we're not advancing
            if stmt is None:
                if self.check(tokenType=TokenType.NEWLINE):
                    self.consume(tokenType=TokenType.NEWLINE)
                else:
                    print(f"[WARNING] No statement parsed and can't advance from: {self.lookahead}")
                    break

        return stmnt_list

    def statement(self) -> ASTNode | None:
        """
        Parses a single statement based on the current token.

        Returns:
            ASTNode or None: The parsed statement node, or None if not recognized.
        """
        if self.check(tokenType=TokenType.IDENTIFIER):
            if self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].atr == '=':
                stmnt = ASTNode(AST.STATEMENT)
                assignment = self.assignment()
                stmnt.add(assignment)
                return stmnt
            elif self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].atr == '(':
                stmnt = ASTNode(AST.STATEMENT)
                stmnt.add(self.function_call())
                return stmnt
            else:
                self.error_grammar()
        elif self.check(atr='if'):
            stmnt = ASTNode(AST.STATEMENT)
            if_stmt = self.if_statement()
            stmnt.add(if_stmt)
            return stmnt
        elif self.check(atr='while'):
            stmnt = ASTNode(AST.STATEMENT)
            while_stmt = self.while_loop()
            stmnt.add(while_stmt)
            return stmnt
        elif self.check(atr='def'):
            stmnt = ASTNode(AST.STATEMENT)
            func_def = self.function_def()
            stmnt.add(func_def)
            return stmnt
        elif self.check(atr='for'):
            stmnt = ASTNode(AST.STATEMENT)
            for_stmt = self.for_loop()
            stmnt.add(for_stmt)
            return stmnt
        else:
            return None

    # <assignment>     -> IDENTIFIER '=' <expression>

    def assignment(self) -> ASTNode:
        """
        Parses an assignment: IDENTIFIER '=' <expression> | IDENTIFIER '=' <function_call>

        Returns:
            ASTNode: Node representing the assignment.
        """
        left = self.consume_error(tokenType=TokenType.IDENTIFIER)
        self.consume_error(atr='=')
        # Function on rhs
        if self.check(tokenType=TokenType.IDENTIFIER) and self.tokens[self.pos + 1].atr == '(':
            right = self.function_call()
        else:
            right = self.expression()  # This should return an ASTNode
        # parent = self.add(parent, root)
        node = ExpressionNode('=')
        node.left = left
        node.right = right
        root = ASTNode(AST.ASSIGNMENT)
        root.add(node)
        if self.should_evaluate:
            if type(node.right) == Token:
                if node.right.tokenType == TokenType.CONSTANT:
                    symbolTable[left.atr] = int(node.right.atr) if '.' not in node.right.atr else float(node.right.atr)
                else:
                    symbolTable[left.atr] = symbolTable[right.atr]
            elif type(node.right) == FunctionCallNode:
                symbolTable[left.atr] = node.right
            else:
                symbolTable[left.atr] = node.right.evaluate()
        return root

    # < expression >     -> < term > <expression_1>
    def expression(self) -> ExpressionNode | Token:
        """
        Parses an arithmetic expression using left-recursive structure.

        Returns:
            ASTNode or Token: Root of the expression subtree.
        """
        root = self.term()
        while self.lookahead.atr in ('+', '-'):
            op = self.consume().atr
            right = self.term()
            root = expression_tree_builder(op, root, right)

        return root

    # T  -> F T'
    def term(self) -> ASTNode | Token:
        """
        Parses a multiplicative term in an expression.

        Returns:
            ASTNode or Token: Node for term subtree.
        """
        root = self.factor()
        while self.lookahead.atr in ('*', '/'):
            op = self.consume().atr  # Get operator (* or /)
            right = self.factor()  # Parse next factor
            root = expression_tree_builder(op, root, right)
        return root

    # F  -> '(' E ')' | CONSTANT | IDENTIFIER
    def factor(self) -> Token | ASTNode:
        """
        Parses a factor: a number, variable, or parenthesized expression.

        Returns:
            Token or ASTNode: Parsed atomic unit.
        """
        temp = self.consume()
        if temp.atr in functionTable:
            self.consume(atr='(')
            args = self.arg_list()
            self.consume(atr=')')
            return FunctionCallNode(temp, args)
        elif temp.atr == '(':
            # consumed '('
            temp = self.expression()
            self.consume(atr=')')
            return temp
        elif temp.tokenType == TokenType.CONSTANT or temp.tokenType == TokenType.IDENTIFIER:
            # consumed 'CONSTANT'
            return temp

        else:
            self.error_grammar(expected="CONSTANT, IDENTIFIER, expression")

    # < if_statement >   -> 'if' '(' < condition > ')' ':' \n 'begin' < statement_list > 'end'
    # |'if''('<condition>')'':'\n\'begin'<statement_list>'end'\n\'elif''('condition')'':'\n\'begin'<statement_list>'end'
    # |'if''('<condition>')'':'\n\'begin'<statement_list>'end'\n\'else'':''begin'< statement_list >'end'
    def if_statement(self) -> IfNode:
        """
        Parses an if/elif/else block with optional branches.

        Returns:
            IfNode: AST representation of the entire conditional construct.
        """
        self.consume_error(atr='if')
        if_stmnt = IfNode()

        # Parse condition
        if self.consume(atr='('):
            if_stmnt.test = self.condition()
            self.consume_error(atr=')')
        else:
            if_stmnt.test = self.condition()

        condition_result = if_stmnt.test.evaluate()
        any_branch_executed = condition_result
        saved_flag = self.should_evaluate
        self.should_evaluate = saved_flag and condition_result

        self.consume_error(atr=':')
        self.consume(tokenType=TokenType.NEWLINE)
        self.consume_error(tokenType=TokenType.BLOCK_BEGIN, message='INDENTATION')

        # if condition is false, ignore the consequent statement list
        self.should_evaluate = condition_result

        # Parse if block
        if_stmnt.consequent = self.statement_list()

        # Consume BLOCK_END after if block (only if it exists)
        if self.check(tokenType=TokenType.BLOCK_END):
            self.consume(tokenType=TokenType.BLOCK_END)

        # Handle elif clauses
        while self.check(atr='elif'):
            self.consume(atr='elif')
            if self.consume(atr='('):
                elif_cond = self.condition()
                self.consume_error(atr=')')
            else:
                elif_cond = self.condition()

            elif_result = elif_cond.evaluate()
            branch_taken = not any_branch_executed and elif_result
            any_branch_executed = any_branch_executed or elif_result
            self.should_evaluate = saved_flag and branch_taken

            self.consume_error(atr=':')
            self.consume(tokenType=TokenType.NEWLINE)
            self.consume_error(tokenType=TokenType.BLOCK_BEGIN, message='INDENTATION')
            elif_block = self.statement_list()

            # Consume BLOCK_END after elif
            if self.check(tokenType=TokenType.BLOCK_END):
                self.consume(tokenType=TokenType.BLOCK_END)

            if_stmnt.elifs.append((elif_cond, elif_block))
        # if the condition result is true, ignore alternate statement list
        self.should_evaluate = not condition_result

        # Handle else clause
        if self.check(atr='else'):
            self.consume(atr='else')
            self.consume_error(atr=':')
            self.consume(tokenType=TokenType.NEWLINE)
            self.consume_error(tokenType=TokenType.BLOCK_BEGIN, message='INDENTATION')

            self.should_evaluate = saved_flag and not any_branch_executed
            if_stmnt.alternate = self.statement_list()

            # Consume BLOCK_END after else (only if it exists)
            if self.check(tokenType=TokenType.BLOCK_END):
                self.consume(tokenType=TokenType.BLOCK_END)

        self.should_evaluate = saved_flag
        # revert should_evaluate back to True
        self.should_evaluate = True

        return if_stmnt

    # <condition>      -> <expression> <relop> <expression>
    def condition(self) -> BinaryExpressionNode:
        """
        Parses a condition: <expression> <relop> <expression>

        Returns:
            BinaryExpressionNode: AST representation of the condition.
        """
        left = self.expression()
        relop = self.relop()
        right = self.expression()
        Node = BinaryExpressionNode(relop, left, right)
        # Node.evaluate()
        return Node

    # <relop>          -> '==' | '!=' | '<' | '<=' | '>' | '>='
    def relop(self) -> ExpressionNode:
        """
        Parses a relational operator.

        Returns:
            str: The relational operator symbol as a string.
        """
        token = self.consume(tokenType=TokenType.RELOP)
        if token:
            return ExpressionNode(token.atr)  # Return the actual operator string, not the Token object
        else:
            self.error_grammar(expected="Relational operator (==, !=, <, <=, >, >=)")

    # <while_loop>     -> 'while' '(' <condition> ')' ':' \n 'begin' <statement_list> 'end'
    def while_loop(self) -> WhileNode:
        """
        Parses a while loop structure.

        Returns:
            WhileNode: AST node representing the loop.
        """
        self.consume_error(atr='while')
        while_stmt = WhileNode()
        if self.consume(atr='('):
            # consumed '('
            while_stmt.test = self.condition()
            self.consume_error(atr=')')
        else:
            while_stmt.test = self.condition()

        condition_result = while_stmt.test.evaluate()
        saved_flag = self.should_evaluate
        self.should_evaluate = saved_flag and condition_result

        self.consume_error(atr=':')
        self.consume(tokenType=TokenType.NEWLINE)
        self.consume_error(tokenType=TokenType.BLOCK_BEGIN, message='INDENTATION')

        self.should_evaluate = not condition_result

        while_stmt.consequent = self.statement_list()
        return while_stmt

    # <function_def>   -> 'def' IDENTIFIER '(' <param_list> ')' '{' <statement_list> '}'More actions
    def function_def(self):
        body = None
        ret = None
        self.consume_error(atr='def')
        identifier = self.consume_error(tokenType=TokenType.IDENTIFIER)
        self.consume_error(atr='(')
        parameters = self.param_list()
        if parameters:
            for param in parameters.params:
                symbolTable[param] = 0
        self.consume_error(atr=')')
        self.consume_error(tokenType=TokenType.SEMICOLON)
        self.consume_error(tokenType=TokenType.NEWLINE)
        self.consume_error(tokenType=TokenType.BLOCK_BEGIN, message='INDENTATION')
        while not self.check(atr='return') and not self.check(tokenType=TokenType.BLOCK_END):
            body = self.statement_list()
        if self.check(atr='return'):
            ret = ASTNode(AST.RETURN)
            return_stmt = self.return_statement()
            ret.add(return_stmt)
            self.consume_error(tokenType=TokenType.NEWLINE)
        self.consume_error(tokenType=TokenType.BLOCK_END)
        functionTable[identifier.atr] = {"params": parameters, "return": ret}
        return FunctionDefNode(identifier.atr, parameters, body, ret)

    # < function_call >  -> IDENTIFIER '(' < arg_list > ')'

    def function_call(self):
        funcCall = FunctionCallNode()
        funcName = self.consume_error(tokenType=TokenType.IDENTIFIER).atr
        self.consume_error(atr='(')
        args = []
        if not self.check(atr=')'):
            args = self.arg_list()
        self.consume_error(atr=')')
        if funcName in functionTable or funcName in ["print", "range"]:
            funcCall.funcName = funcName
            funcCall.args = args
            return funcCall
        else:
            self.error_grammar(f"Function {funcName} is not defined")

    # < arg_list >       -> < expression > ',' < arg_list > | < expression > | ε
    def arg_list(self):
        args = []
        currExp = self.expression()
        while currExp:
            if isinstance(currExp, Token):
                if currExp.tokenType == TokenType.IDENTIFIER:
                    args.append(currExp)
                elif currExp.tokenType == TokenType.CONSTANT:
                    try:
                        val = int(currExp.atr)
                    except ValueError:
                        val = float(currExp.atr)
                    args.append(Token(TokenType.CONSTANT, val))
                # args.append(currExp)
            elif isinstance(currExp, ExpressionNode):
                args.append(currExp.evaluate())
            if not self.consume(atr=','):
                return args
            currExp = self.consume(tokenType=TokenType.IDENTIFIER)
            if not currExp:
                currExp = self.consume(tokenType=TokenType.CONSTANT)
        return args

    # <param_list>     -> IDENTIFIER ',' <param_list> | IDENTIFIER | ε
    def param_list(self) -> ParamsNode:
        lParams = ParamsNode()
        currId = self.consume(tokenType=TokenType.IDENTIFIER)
        while currId:
            lParams.add(Token(tokenType=TokenType.IDENTIFIER, atr=currId.atr))
            if not self.consume(atr=','):
                return lParams
            currId = self.consume(tokenType=TokenType.IDENTIFIER)
        return lParams

    # < return_statement > -> 'return' < expression >
    def return_statement(self) -> ExpressionNode | Token:
        self.consume_error(atr='return')
        exp = self.expression()
        return exp

    # <for_loop>->'for''(' IDENTIFIER 'in' 'range' '(' NUMBER ',' NUMBER ')' ')' ':' \n 'begin' < statement_list > 'end'
    # <for_loop>->'for''(' IDENTIFIER 'in' 'range' '(' NUMBER ',' NUMBER ')' ')' ':' \n 'begin' < statement_list > 'end'
    def for_loop(self):
        self.consume_error(atr='for')
        loopVar = self.consume(tokenType=TokenType.IDENTIFIER)
        self.consume(atr='in')
        iterable = self.function_call()
        lenArgs = len(iterable.args)
        start, stop, step = 0, 0, 0
        if lenArgs == 1:
            start = 0
            stop = iterable.args[0]
            step = 1
        elif lenArgs == 2:
            start, stop = iterable.args
            step = 1
        elif lenArgs == 3:
            start, stop, step = iterable.args

        symbolTable[loopVar.atr] = start

        self.consume_error(tokenType=TokenType.SEMICOLON)
        self.consume_error(tokenType=TokenType.NEWLINE)
        self.consume_error(tokenType=TokenType.BLOCK_BEGIN)
        consequent = self.statement_list()
        return ForNode(loopVar, [start, stop, step], consequent)
