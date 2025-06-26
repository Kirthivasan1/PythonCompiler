def fetchSymbolTable(x):
    if x in symbolTable:
        return symbolTable[x]
    else:
        raise Exception(f"Undefined variable:'{x}'.")


symbolTable = {}
functionTable = {}
