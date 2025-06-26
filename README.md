# 🐍 Python Subset Compiler 

A custom compiler front-end for a subset of Python, built from scratch without using external parser libraries like PLY, Lex/Yacc, or ANTLR.

This project performs **lexical analysis**, **recursive descent parsing**, **AST construction**, and **Three-Address Code (TAC) generation** for a Python-like language, supporting core constructs such as functions, control flow, and loops.

---

## ✨ Features

- **Lexical Analyzer:** Custom tokenizer to recognize keywords, identifiers, constants (integers and floats), operators, and indentation-based block structure.
- **Recursive Descent Parser:** Built manually to handle a Python-like grammar.
- **AST Generation:** Constructs an Abstract Syntax Tree (AST) representing program structure.
- **Three-Address Code (TAC) Generation:** Intermediate representation generator supporting:
  - Arithmetic operations and assignments
  - Conditional statements (`if`, `elif`, `else`)
  - Looping constructs (`while`, `for`)
  - Function definitions and function calls with arguments
  - Integer-only `range(start, stop, step)` in `for` loops
  - Built-in `print` statements
  - Label reuse and GOTO-based TAC for efficient control flow
- **Testing Suite:** Organized test folder validating lexing, parsing, and code generation.

---

## 🔄 Compilation Pipeline

1. **Lexing:** Converts source code into tokens.
2. **Parsing:** Constructs an AST using recursive descent.
3. **AST Construction:** Represents the syntactic and semantic structure of the program.
4. **TAC Generation:** Emits Three-Address Code from the AST for interpretation or further compilation.

---

## 🚀 How to Run

```bash
# 1. Clone the repository
git clone https://github.com/Kirthivasan1/PythonCompiler.git
cd PythonCompiler

# 2. Write your test program in 'src.py'
#    Example:
#    def inc(x):
#        return x + 1
#    
#    a = 5
#    a = inc(a)
#    print(a)

# 3. Run the compiler with your source file
python main.py src.py
