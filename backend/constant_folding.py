"""
Constant Folding Module
Evaluates constant expressions at compile time.
Also performs constant propagation where safe.
"""


def fold_constants(ast_statements):
    """
    Takes AST statements, returns:
    - folded_ast: modified statements with constants folded
    - changes: list of changes made (for display)
    """
    changes = []
    folded_ast = []

    # Track known constant values for propagation
    known_constants = {}

    for stmt in ast_statements:
        new_stmt = dict(stmt)  # shallow copy

        if stmt["type"] == "declaration" and stmt["value"] is not None:
            original_expr = stmt["value"]
            expr_tokens = stmt.get("expr_tokens", [])

            # Try to fold the expression
            folded_value = try_fold_expression(expr_tokens, known_constants)

            if folded_value is not None and str(folded_value) != original_expr:
                new_stmt["value"] = str(folded_value)
                new_stmt["expr_tokens"] = [{"type": "CONSTANT", "value": str(folded_value), "line": stmt["line"]}]
                changes.append({
                    "line": stmt["line"],
                    "type": "constant_fold",
                    "original": f"{stmt['data_type']} {stmt['name']} = {original_expr}",
                    "optimized": f"{stmt['data_type']} {stmt['name']} = {folded_value}",
                    "description": f"Folded '{original_expr}' to '{folded_value}'"
                })

            # Track the constant value for propagation
            final_value = folded_value if folded_value is not None else try_parse_number(original_expr.strip())
            if final_value is not None:
                known_constants[stmt["name"]] = final_value

        elif stmt["type"] == "assignment" and stmt.get("value"):
            original_expr = stmt["value"]
            expr_tokens = stmt.get("expr_tokens", [])

            folded_value = try_fold_expression(expr_tokens, known_constants)

            if folded_value is not None and str(folded_value) != original_expr:
                new_stmt["value"] = str(folded_value)
                new_stmt["expr_tokens"] = [{"type": "CONSTANT", "value": str(folded_value), "line": stmt["line"]}]
                changes.append({
                    "line": stmt["line"],
                    "type": "constant_fold",
                    "original": f"{stmt['name']} = {original_expr}",
                    "optimized": f"{stmt['name']} = {folded_value}",
                    "description": f"Folded '{original_expr}' to '{folded_value}'"
                })

            final_value = folded_value if folded_value is not None else try_parse_number(original_expr.strip())
            if final_value is not None:
                known_constants[stmt["name"]] = final_value
            else:
                # Variable is no longer a known constant
                known_constants.pop(stmt["name"], None)

        folded_ast.append(new_stmt)

    return {"folded_ast": folded_ast, "changes": changes}


def try_fold_expression(expr_tokens, known_constants):
    """
    Try to evaluate an expression made of constants and known-constant variables.
    Returns the computed numeric value, or None if it can't be fully folded.
    """
    if not expr_tokens:
        return None

    # Build a list of values and operators
    items = []
    for tok in expr_tokens:
        if tok["type"] == "CONSTANT":
            val = try_parse_number(tok["value"])
            if val is None:
                return None  # Can't fold non-numeric constants
            items.append(("num", val))
        elif tok["type"] == "IDENTIFIER":
            # Check if this variable has a known constant value
            if tok["value"] in known_constants:
                items.append(("num", known_constants[tok["value"]]))
            else:
                return None  # Variable with unknown value — can't fold
        elif tok["type"] == "OPERATOR" and tok["value"] in ("+", "-", "*", "/", "%"):
            items.append(("op", tok["value"]))
        elif tok["value"] == "(":
            items.append(("paren", "("))
        elif tok["value"] == ")":
            items.append(("paren", ")"))
        else:
            return None  # Unknown token type — can't fold

    # Now evaluate the expression respecting operator precedence
    try:
        result = evaluate_items(items)
        if result is None:
            return None
        # Return integer if it's a whole number
        if isinstance(result, float) and result == int(result):
            return int(result)
        return result
    except Exception:
        return None


def evaluate_items(items):
    """
    Evaluate a list of (type, value) items with proper precedence.
    """
    # First resolve parentheses
    items = resolve_parens(items)
    if items is None:
        return None

    # Then handle precedence: * / % first, then + -
    items = apply_operators(items, ["*", "/", "%"])
    if items is None:
        return None
    items = apply_operators(items, ["+", "-"])
    if items is None:
        return None

    if len(items) == 1 and items[0][0] == "num":
        return items[0][1]
    return None


def resolve_parens(items):
    """Resolve innermost parenthesized sub-expressions."""
    while any(i[0] == "paren" for i in items):
        # Find innermost '('
        open_idx = None
        for idx, item in enumerate(items):
            if item == ("paren", "("):
                open_idx = idx

        if open_idx is None:
            break

        # Find matching ')'
        close_idx = None
        for idx in range(open_idx + 1, len(items)):
            if items[idx] == ("paren", ")"):
                close_idx = idx
                break

        if close_idx is None:
            return None  # Mismatched parentheses

        # Evaluate the sub-expression
        sub = items[open_idx + 1:close_idx]
        sub = apply_operators(sub, ["*", "/", "%"])
        if sub is None:
            return None
        sub = apply_operators(sub, ["+", "-"])
        if sub is None:
            return None

        if len(sub) == 1 and sub[0][0] == "num":
            items = items[:open_idx] + [sub[0]] + items[close_idx + 1:]
        else:
            return None

    return items


def apply_operators(items, operators):
    """Apply given operators left to right."""
    i = 0
    while i < len(items):
        if items[i][0] == "op" and items[i][1] in operators:
            if i == 0 or i >= len(items) - 1:
                return None
            left = items[i - 1]
            right = items[i + 1]
            if left[0] != "num" or right[0] != "num":
                return None

            op = items[i][1]
            a = left[1]
            b = right[1]

            if op == "+":
                result = a + b
            elif op == "-":
                result = a - b
            elif op == "*":
                result = a * b
            elif op == "/":
                if b == 0:
                    return None  # Division by zero — don't fold
                result = a / b
            elif op == "%":
                if b == 0:
                    return None
                result = a % b
            else:
                return None

            items = items[:i - 1] + [("num", result)] + items[i + 2:]
            # Don't increment — check same position
        else:
            i += 1
    return items


def try_parse_number(s):
    """Try to parse a string as a number."""
    s = s.strip()
    try:
        if "." in s:
            return float(s)
        return int(s)
    except (ValueError, TypeError):
        return None
