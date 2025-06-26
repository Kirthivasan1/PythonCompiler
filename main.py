import sys

from file_reader import *
from lexical_analyzer import *
from parser import *
from intermediate_code_generation import *

'''
classes ToggleCase
Variable camelCase
functions snake_case
constants UPPERCASE
'''

"""
FUTURE:
    Implement String literals? Comments?
    Implement exponents for CONSTANTS
    lexical_analyser.py:
        Comments
        Logical operator (or, and, not)
    make the CFG automatic by using text file
    implement lalr parser instead of backtracking
"""


def main():
    # Reading the program

    file = file_reader(sys.argv[1])

    # Token Parsing
    tokens = lexical_analyzer(file)
    # for token in tokens:
    #     print(token)
    # NOW MAP OUT A GRAMMAR THAT THIS PROGRAMMING LANGUAGE FOLLOWS
    # AFTER THAT CODE THE LALR PARSER BUT BEFORE THAT YOU NEED FIRST AND FOLLOW COMPUTE TO USE

    parser = Parser(tokens)
    # print(parser.tree)

    TAC = TACGenerator(parser.tree).get_TAC()
    print(*TAC, sep='\n')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python main.py <filename>")
        sys.exit(1)
    main()
