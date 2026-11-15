"""
Parser Module - Syntax Analysis
Checks token stream for basic syntax correctness.
Produces a simple AST (list of statement dicts).
"""


def parse(tokens):
    """
    Takes a list of tokens from the lexer.
    Returns:
      - ast: list of statement dicts (for downstream use)
      - errors: list of syntax error dicts
      - warnings: list of warning dicts
    """
    errors = []
    warnings = []
    ast = []

    # Filter out comments and preprocessor directives for parsing
    filtered = [t for t in tokens if t["type"] not in ("COMMENT", "PREPROCESSOR")]

    # --- Check brace matching ---
    brace_stack = []
    for tok in filtered:
        if tok["value"] == "{":
            brace_stack.append(tok["line"])
        elif tok["value"] == "}":
            if brace_stack:
                brace_stack.pop()
            else:
                errors.append({
                    "message": "Unexpected closing brace '}'",
                    "line": tok["line"]
                })
    for open_line in brace_stack:
        errors.append({
            "message": "Unmatched opening brace '{'",
            "line": open_line
        })

    # --- Check parenthesis matching ---
    paren_stack = []
    for tok in filtered:
        if tok["value"] == "(":
            paren_stack.append(tok["line"])
        elif tok["value"] == ")":
            if paren_stack:
                paren_stack.pop()
            else:
                errors.append({
                    "message": "Unexpected closing parenthesis ')'",
                    "line": tok["line"]
                })
    for open_line in paren_stack:
        errors.append({
            "message": "Unmatched opening parenthesis '('",
            "line": open_line
        })

    # --- Parse statements ---
    pos = 0

    while pos < len(filtered):
        tok = filtered[pos]

        # Skip braces (they delimit blocks)
        if tok["value"] in ("{", "}"):
            pos += 1
            continue

        # --- Variable declaration: type identifier = expr ; ---
        if tok["type"] == "KEYWORD" and tok["value"] in ("int", "float", "double", "char", "void"):
            result, pos = parse_declaration(filtered, pos, errors)
            if result:
                ast.append(result)
            continue

        # --- Return statement ---
        if tok["type"] == "KEYWORD" and tok["value"] == "return":
            result, pos = parse_return(filtered, pos, errors)
            if result:
                ast.append(result)
            continue

        # --- printf / scanf call ---
        if tok["type"] == "KEYWORD" and tok["value"] in ("printf", "scanf"):
            result, pos = parse_function_call(filtered, pos, errors)
            if result:
                ast.append(result)
            continue

        # --- Function definition: type name ( ... ) { ... } ---
        # We detect this by: KEYWORD IDENTIFIER (  — skip the function header
        if tok["type"] == "KEYWORD" and tok["value"] in ("int", "float", "double", "char", "void"):
            pos += 1
            continue

        # --- Assignment: identifier = expr ; ---
        if tok["type"] == "IDENTIFIER":
            result, pos = parse_assignment(filtered, pos, errors)
            if result:
                ast.append(result)
            continue

        # --- Skip function-related keywords ---
        if tok["type"] == "KEYWORD" and tok["value"] == "main":
            pos += 1
            continue

        # --- Anything else: skip with warning ---
        pos += 1

    # If there were brace/paren errors, return early
    if errors:
        return {"ast": ast, "errors": errors, "warnings": warnings}

    # --- Check for missing semicolons in statements ---
    # (Already checked inside parse_declaration etc.)

    return {"ast": ast, "errors": errors, "warnings": warnings}


def parse_declaration(tokens, pos, errors):
    """
    Parse: type identifier = expression ;
    or:    type identifier ;
    Returns (statement_dict, new_pos)
    """
    start_line = tokens[pos]["line"]
    data_type = tokens[pos]["value"]
    pos += 1

    # Check for 'main' after type (function definition)
    if pos < len(tokens) and tokens[pos]["value"] == "main":
        # Skip function header: main ( )
        pos += 1
        while pos < len(tokens) and tokens[pos]["value"] != "{" and tokens[pos]["value"] != ";":
            pos += 1
        return None, pos

    # Expect identifier
    if pos >= len(tokens) or tokens[pos]["type"] != "IDENTIFIER":
        errors.append({
            "message": f"Expected variable name after '{data_type}'",
            "line": start_line
        })
        # Skip to semicolon
        while pos < len(tokens) and tokens[pos]["value"] != ";":
            pos += 1
        if pos < len(tokens):
            pos += 1
        return None, pos

    var_name = tokens[pos]["value"]
    pos += 1

    # Case 1: just declaration — type var ;
    if pos < len(tokens) and tokens[pos]["value"] == ";":
        pos += 1
        return {
            "type": "declaration",
            "data_type": data_type,
            "name": var_name,
            "value": None,
            "line": start_line
        }, pos

    # Case 2: declaration with assignment — type var = expr ;
    if pos < len(tokens) and tokens[pos]["value"] == "=":
        pos += 1  # skip '='

        # Collect expression tokens until semicolon
        expr_tokens = []
        while pos < len(tokens) and tokens[pos]["value"] != ";":
            # If we hit a keyword or a type, the semicolon is probably missing
            if tokens[pos]["type"] == "KEYWORD" and tokens[pos]["value"] in (
                "int", "float", "double", "char", "void",
                "printf", "scanf", "return", "if", "else", "while", "for"
            ):
                errors.append({
                    "message": f"Missing semicolon after declaration of '{var_name}'",
                    "line": start_line
                })
                # Don't consume this token — it starts the next statement
                break
            expr_tokens.append(tokens[pos])
            pos += 1

        if pos < len(tokens) and tokens[pos]["value"] == ";":
            pos += 1
        elif not errors or errors[-1]["line"] != start_line:
            errors.append({
                "message": f"Missing semicolon after declaration of '{var_name}'",
                "line": start_line
            })

        expr_str = " ".join(t["value"] for t in expr_tokens)
        return {
            "type": "declaration",
            "data_type": data_type,
            "name": var_name,
            "value": expr_str,
            "expr_tokens": expr_tokens,
            "line": start_line
        }, pos

    # Unexpected token
    errors.append({
        "message": f"Unexpected token '{tokens[pos]['value']}' in declaration of '{var_name}'",
        "line": start_line
    })
    while pos < len(tokens) and tokens[pos]["value"] != ";":
        pos += 1
    if pos < len(tokens):
        pos += 1
    return None, pos


def parse_assignment(tokens, pos, errors):
    """
    Parse: identifier = expression ;
    """
    start_line = tokens[pos]["line"]
    var_name = tokens[pos]["value"]
    pos += 1

    if pos >= len(tokens) or tokens[pos]["value"] != "=":
        # Could be a function call like identifier(...)
        if pos < len(tokens) and tokens[pos]["value"] == "(":
            return parse_function_call_from(var_name, tokens, pos, errors, start_line)
        errors.append({
            "message": f"Expected '=' after '{var_name}'",
            "line": start_line
        })
        while pos < len(tokens) and tokens[pos]["value"] != ";":
            pos += 1
        if pos < len(tokens):
            pos += 1
        return None, pos

    pos += 1  # skip '='

    # Collect expression tokens until semicolon
    expr_tokens = []
    while pos < len(tokens) and tokens[pos]["value"] != ";":
        # If we hit a keyword, semicolon is probably missing
        if tokens[pos]["type"] == "KEYWORD" and tokens[pos]["value"] in (
            "int", "float", "double", "char", "void",
            "printf", "scanf", "return", "if", "else", "while", "for"
        ):
            errors.append({
                "message": f"Missing semicolon after assignment to '{var_name}'",
                "line": start_line
            })
            break
        expr_tokens.append(tokens[pos])
        pos += 1

    if not expr_tokens:
        errors.append({
            "message": f"Empty expression in assignment to '{var_name}'",
            "line": start_line
        })

    if pos < len(tokens) and tokens[pos]["value"] == ";":
        pos += 1
    else:
        errors.append({
            "message": f"Missing semicolon after assignment to '{var_name}'",
            "line": start_line
        })

    expr_str = " ".join(t["value"] for t in expr_tokens)
    return {
        "type": "assignment",
        "name": var_name,
        "value": expr_str,
        "expr_tokens": expr_tokens,
        "line": start_line
    }, pos


def parse_return(tokens, pos, errors):
    """
    Parse: return expression ;
    """
    start_line = tokens[pos]["line"]
    pos += 1  # skip 'return'

    expr_tokens = []
    while pos < len(tokens) and tokens[pos]["value"] != ";":
        expr_tokens.append(tokens[pos])
        pos += 1

    if pos < len(tokens) and tokens[pos]["value"] == ";":
        pos += 1
    else:
        errors.append({
            "message": "Missing semicolon after return statement",
            "line": start_line
        })

    expr_str = " ".join(t["value"] for t in expr_tokens)
    return {
        "type": "return",
        "value": expr_str,
        "expr_tokens": expr_tokens,
        "line": start_line
    }, pos


def parse_function_call(tokens, pos, errors):
    """
    Parse: printf("...", args) ;  or  scanf("...", args) ;
    """
    start_line = tokens[pos]["line"]
    func_name = tokens[pos]["value"]
    pos += 1

    if pos >= len(tokens) or tokens[pos]["value"] != "(":
        errors.append({
            "message": f"Expected '(' after '{func_name}'",
            "line": start_line
        })
        while pos < len(tokens) and tokens[pos]["value"] != ";":
            pos += 1
        if pos < len(tokens):
            pos += 1
        return None, pos

    return parse_function_call_from(func_name, tokens, pos, errors, start_line)


def parse_function_call_from(func_name, tokens, pos, errors, start_line):
    """
    Parse the argument list of a function call starting from '('.
    """
    # Collect everything from ( to matching )
    paren_depth = 0
    arg_tokens = []

    while pos < len(tokens):
        if tokens[pos]["value"] == "(":
            paren_depth += 1
        elif tokens[pos]["value"] == ")":
            paren_depth -= 1
            if paren_depth == 0:
                arg_tokens.append(tokens[pos])
                pos += 1
                break
        arg_tokens.append(tokens[pos])
        pos += 1

    if paren_depth != 0:
        errors.append({
            "message": f"Unmatched parenthesis in call to '{func_name}'",
            "line": start_line
        })

    # Expect semicolon
    if pos < len(tokens) and tokens[pos]["value"] == ";":
        pos += 1
    else:
        errors.append({
            "message": f"Missing semicolon after call to '{func_name}'",
            "line": start_line
        })

    args_str = " ".join(t["value"] for t in arg_tokens)
    return {
        "type": "function_call",
        "name": func_name,
        "args": args_str,
        "arg_tokens": arg_tokens,
        "line": start_line
    }, pos
