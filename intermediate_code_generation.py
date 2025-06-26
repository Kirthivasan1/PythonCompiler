import AST
from AST import *
from collections import deque
from config import functionTable

"""
So, we have parse tree with ast nodes and i somehow have to give this
nodes to a class and convert it to TAC with op, arg1, arg2 and
result. To do this, we need to do dfs once again? while digging, for
each type of ast nodes be it binary exp or assignment, we handle the
TAC differently. Then we also need back patching to find the index to
jump for conditionals and then finally put all of them together.
"""


class TACLine:
    def __init__(self, op, arg1=None, arg2=None, result=None, label=None):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result
        self.label = label

    def __repr__(self):
        temp = ""
        if self.label:
            temp += f"{self.label}: "
        else:
            temp += f"\t"
        if self.op == 'ASSIGN':
            return temp + f"{self.result} = {self.arg1}"
        elif self.op in {'+', '-', '*', '/', '==', '!=', '<', '<=', '>', '>='}:
            return temp + f"{self.result} = {self.arg1} {self.op} {self.arg2}"
        elif self.op == 'IFZ':
            return temp + f"IFZ {self.arg1} GOTO {self.arg2}"
        elif self.op == 'GOTO':
            return temp + f"GOTO {self.arg1}"
        elif self.op == 'BEGIN_FUNC':
            return temp + f"BEGIN_FUNC"
        elif self.op == 'END_FUNC':
            return temp + f"END_FUNC"
        elif self.op == 'PUSH_ARG':
            return temp + f"PUSH_ARG {self.arg1}"
        elif self.op == 'POP_ARG':
            return temp + f"POP_ARG"
        elif self.op == 'LCALL':
            return temp + f"{self.arg2} = LCALL {self.arg1}"
        else:
            return temp + f"{self.op} {self.arg1 or ''} {self.arg2 or ''} {self.result or ''}".strip()


def opposite_relop(operator: str):
    op_table = {'>': '<=', '<': '>=', '>=': '<', '<=': '>', '==': '!=', '!=': '=='}
    return op_table[operator]


class TACGenerator:
    def __init__(self, tree):
        self.instructions = []
        self.temp_count = 0
        self.labelCount = 0
        self.labelPresent = None
        self.generate_func_first(tree)
        self.emit("END")

    def new_temp(self):
        t = f"T{self.temp_count}"
        self.temp_count += 1
        return t

    def new_label(self, customLabel: str = None):
        if not customLabel:
            label = f"L{self.labelCount}"
            self.labelCount += 1
        else:
            label = customLabel
        return label

    def emit(self, op, arg1=None, arg2=None, result=None, label=None):
        if self.labelPresent:
            self.instructions.append(TACLine(op, arg1, arg2, result, self.labelPresent))
            self.labelPresent = None
        else:
            self.instructions.append(TACLine(op, arg1, arg2, result, label))

    def get_TAC(self):
        return self.instructions

    def generate_func_first(self, tree: ASTNode):
        if tree.nodeType == AST.PROGRAM:
            self.generate_func_first(*tree.body)  # generate STATEMENT_LIST

        elif tree.nodeType == AST.STATEMENT_LIST:
            # First we create all the functions and then go with main
            lStmt = []
            for stmt in tree.body:
                if stmt.body[0].nodeType == AST.FUNC_DEF and stmt.body != []:
                    self.generate_func_def(*stmt.body)
                else:
                    lStmt.append(stmt)
            self.labelPresent = self.new_label("MAIN")
            for statement in lStmt:
                self.generate(*statement.body)

    def generate_statement_list(self, tree: ASTNode):
        for stmt in tree.body:  # Each is a STATEMENT
            self.generate(*stmt.body)  # generate command of stmt.body

    def generate(self, tree: ASTNode):
        if tree.nodeType == AST.ASSIGNMENT:
            self.generate_assignment(tree)

        elif tree.nodeType == AST.IF_COND:
            self.generate_if(tree)

        elif tree.nodeType == AST.WHILE_LOOP:
            self.generate_while(tree)

        elif tree.nodeType == AST.FOR_LOOP:
            self.generate_for(tree)
        elif isinstance(tree, FunctionCallNode):
            if tree.funcName == 'print':
                for arg in tree.args:
                    self.emit('PRINT', arg)
            else:
                self.generate_func_call(tree)
        elif tree.nodeType == AST.RETURN:
            if isinstance(tree.body[0], ExpressionNode):
                tempVar = self.handle_expression(tree.body[0])
                self.emit("RETURN", tempVar)
            else:
                self.emit("RETURN", tree.body[0].atr)

    def generate_assignment(self, tree: ASTNode):
        expr = tree.body[0]  # should be ExpressionNode
        '''if expr.right == Token then its simple , 
        else expr.right can be ExpressionNode then generate_assignment(expr.right)'''
        if isinstance(expr, ExpressionNode):
            target = self.handle_expression(expr.left)
            if isinstance(expr.right, FunctionCallNode):
                self.generate_func_call(expr.right, target)
                return
            else:
                result = self.handle_expression(expr.right)
        else:
            target = expr.atr

            result = self.handle_expression(expr)
        self.emit('ASSIGN', result, None, target)

    def handle_expression(self, expr):
        if isinstance(expr, ASTNode | ExpressionNode):
            if expr.nodeType == TokenType.CONSTANT:
                return expr.value

            elif expr.nodeType == TokenType.IDENTIFIER:
                return expr.value

            elif expr.nodeType == TokenType.OPERATOR:
                # expr.value --> operator
                left = self.handle_expression(expr.left)  # left = left of operator
                right = self.handle_expression(expr.right)  # right = right of operator
                temp = self.new_temp()  # temp = t{n} variable used to store temp values
                self.emit(expr.value, left, right, temp)
                return temp
        elif isinstance(expr, Token):
            return expr.atr

    def generate_if(self, tree: ASTNode | IfNode):
        """
            WE have an "if" statement,
            we need to create only lEnd
            also if we have "elif":
            we need to create lElifs
            Now, with the labels,
            1. we emit (If_OppositeRelOp, left, right, lEnd)
            2. generate(trueTree)
            3. we emit ("GOTO", None, None, lEnd)
            4. we emit ("LABEL", None, None, lEnd)
            5. generate(falseTree)
            6. we emit ("LABEL", None, None, lEnd)
            7. we emit ("END", None, None, None)
            """
        # return True or False if 'elif' blocks are there
        elif_block_exists = tree.elifs != []
        lElifs = deque()  # list of labels for 'elif' conditions
        if elif_block_exists:
            for _ in tree.elifs:
                lElifs.append(self.new_label())
        lFalse = self.new_label()  # label for false of 'if' condition
        lEnd = self.new_label() if tree.alternate else lFalse  # label for end of the block

        # Handles all the binaryExpression inside if
        op = tree.test.operator.value
        left = self.handle_expression(tree.test.left)
        right = self.handle_expression(tree.test.right)

        tempIf = self.new_temp()
        self.emit(op, left, right, tempIf)
        if elif_block_exists:
            self.emit('IFZ', tempIf, lElifs[0])
        elif tree.alternate:
            self.emit('IFZ', tempIf, lFalse)
        else:
            self.emit('IFZ', tempIf, lEnd)
        self.generate(tree.consequent)
        self.emit("GOTO", lEnd)

        # Handles all the elifs
        if elif_block_exists:
            elif_pointer = 0
            while lElifs:
                elif_tree = tree.elifs[elif_pointer]
                self.labelPresent = lElifs[0]
                lElifs.popleft()
                lCurr = lElifs[0] if lElifs else lFalse
                op = elif_tree[0].operator.value  # elif_tree[0] is the ExpressionNode
                left = self.handle_expression(elif_tree[0].left)
                right = self.handle_expression(elif_tree[0].right)

                tempElif = self.new_temp()
                self.emit(op, left, right, tempElif)

                self.emit('IFZ', tempElif, lCurr)
                self.generate(elif_tree[1])  # elif_tree[1] is the commands
                elif_pointer += 1
                if tree.alternate:
                    self.emit("GOTO", lEnd)
            del elif_pointer

        if tree.alternate:
            self.labelPresent = lFalse
            self.generate(tree.alternate)
        self.labelPresent = lEnd

    def generate_while(self, tree: ASTNode | WhileNode):
        """
        1. handle_expr()
        2. emit("LABEL",None,None,lStart)
        3. emit("{opposite_relop}", left, right, lEnd)
        4. generate
        5. emit("GOTO", None, None, lStart)
        6. emit("LABEL",None, None, lEnd)
        """
        lStart = self.labelPresent if self.labelPresent else self.new_label()
        lEnd = self.new_label()
        op = tree.test.operator.value
        left = self.handle_expression(tree.test.left)
        right = self.handle_expression(tree.test.right)
        tempWhile = self.new_temp()
        self.emit(op, left, right, tempWhile, lStart)
        self.emit('IFZ', tempWhile, lEnd)
        self.generate(tree.consequent)
        self.emit("GOTO", lStart)
        self.labelPresent = lEnd

    def generate_for(self, tree: ASTNode | ForNode):
        start, stop, step = tree.iterableExpr
        self.emit('ASSIGN', start.atr, None, tree.loopVar.atr)
        lStart = self.new_label()
        lEnd = self.new_label()
        tempFor = self.new_temp()
        # if step.atr >= 0:
        #     self.emit("<=", tree.loopVar.atr, stop.atr, tempFor, lStart)
        # else:
        #     self.emit(">", tree.loopVar.atr, stop.atr, tempFor, lStart)
        self.emit(">" if start.atr > stop.atr else "<=", tree.loopVar.atr, stop.atr, tempFor, lStart)
        self.emit('IFZ', tempFor, lEnd)
        self.generate(tree.consequent)
        tempVar = self.new_temp()
        self.emit('+' if step.atr >=0 else '-', tree.loopVar.atr, abs(step.atr), tempVar)
        self.emit('ASSIGN', tempVar, None, tree.loopVar.atr)
        self.emit('GOTO', lStart)
        self.labelPresent = lEnd

    def generate_func_def(self, tree: FunctionDefNode):
        """
        1. update self.new_label to give labels custom name
        2. labelPresent = newLabel
        3. use custom name (funcName) as self.emit('BEGIN_FUNC')
        4. self.generate(statements)
        5. self.emit('END_FUNC')
        """
        labelFunc = self.new_label(tree.identifier)
        self.labelPresent = labelFunc
        self.emit('BEGIN_FUNC')
        if tree.body:
            self.generate_statement_list(tree.body)
        if tree.ret:
            self.generate(tree.ret)
        self.emit('END_FUNC')

    def generate_func_call(self, tree: FunctionCallNode, storeVar: str = None):
        """
        INPUT:
        int foo(int a, int b)
        {
            return a + b;
        }
        void main()
        {
            int c;
            int d;
            foo(c, d);
        }
        OUTPUT:
        _foo:
            BeginFunc 4;
            _t0 = a + b;
            Return _t0;
            EndFunc;
        main:
             BeginFunc 12;
             PushParam d;
             PushParam c;
             _t1 = LCall _foo;
             PopParams 8;
             EndFunc;
        # maybe also implement a check if funcName in funcTable?
        1. self.emit('PUSH_ARG', i) for i in args
        2. tReturn = new_temp()
        3. self.emit('LCALL', funcName, tReturn)
        4. self.emit('POP_ARG') for i in args
        """
        if tree.funcName not in functionTable:
            return
        for arg in tree.args:
            self.emit('PUSH_ARG', arg.atr)
        tReturn = self.new_temp()
        self.emit('LCALL', tree.funcName, tReturn)
        if storeVar:
            self.emit('ASSIGN', tReturn, None, storeVar)
        for _ in tree.args:
            self.emit('POP_ARG')
