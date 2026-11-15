"""
Dead Code Elimination Module
Removes unused variable declarations and assignments
that don't affect program output.
"""


def eliminate_dead_code(ast_statements):
    """
    Takes AST statements, returns:
    - live_ast: statements with dead code removed
    - removed: list of removed statements (for display)
    """
    removed = []

    # Functions/statements that produce side effects (output, input, etc.)
    SIDE_EFFECT_FUNCS = {"printf", "scanf", "puts", "gets", "putchar", "getchar"}

    # Repeat until no more dead code is found (fixed-point iteration)
    current_stmts = list(ast_statements)
    changed = True

    while changed:
        changed = False

        # Step 1: Find all variables that are "used" (read in a live context)
        used_vars = set()

        for stmt in current_stmts:
            if stmt["type"] == "function_call":
                # All variables mentioned in function call args are used
                arg_tokens = stmt.get("arg_tokens", [])
                for tok in arg_tokens:
                    if tok["type"] == "IDENTIFIER":
                        used_vars.add(tok["value"])

            elif stmt["type"] == "return":
                # All variables in return expression are used
                expr_tokens = stmt.get("expr_tokens", [])
                for tok in expr_tokens:
                    if tok["type"] == "IDENTIFIER":
                        used_vars.add(tok["value"])

        # Step 2: Propagate — if variable X is used, and X = expr uses Y, then Y is used too
        # Repeat until stable
        propagation_changed = True
        while propagation_changed:
            propagation_changed = False
            for stmt in current_stmts:
                if stmt["type"] in ("declaration", "assignment"):
                    var_name = stmt["name"]
                    if var_name in used_vars:
                        # This variable is used, so all variables in its expression are also used
                        expr_tokens = stmt.get("expr_tokens", [])
                        for tok in expr_tokens:
                            if tok["type"] == "IDENTIFIER" and tok["value"] not in used_vars:
                                used_vars.add(tok["value"])
                                propagation_changed = True

        # Step 3: Remove dead assignments and declarations
        new_stmts = []
        for stmt in current_stmts:
            if stmt["type"] in ("declaration", "assignment"):
                var_name = stmt["name"]
                if var_name not in used_vars:
                    # This is dead code — not used by any live statement
                    removed.append({
                        "line": stmt["line"],
                        "type": "dead_code",
                        "statement": format_statement(stmt),
                        "reason": f"Variable '{var_name}' is never used in program output"
                    })
                    changed = True
                    continue
            new_stmts.append(stmt)

        current_stmts = new_stmts

    return {"live_ast": current_stmts, "removed": removed}


def format_statement(stmt):
    """Format a statement dict back into readable C code."""
    if stmt["type"] == "declaration":
        if stmt["value"] is not None:
            return f"{stmt['data_type']} {stmt['name']} = {stmt['value']};"
        else:
            return f"{stmt['data_type']} {stmt['name']};"
    elif stmt["type"] == "assignment":
        return f"{stmt['name']} = {stmt['value']};"
    elif stmt["type"] == "return":
        return f"return {stmt['value']};"
    elif stmt["type"] == "function_call":
        return f"{stmt['name']}{stmt['args']};"
    return str(stmt)
