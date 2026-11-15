"""
Intermediate Code Generator
Converts AST statements into Three Address Code (TAC).
"""


def generate_tac(ast_statements):
    """
    Takes a list of AST statement dicts.
    Returns a list of TAC instruction strings.
    """
    tac = []
    temp_counter = [0]  # use list so nested function can modify it

    def new_temp():
        """Generate a new temporary variable name."""
        temp_counter[0] += 1
        return f"t{temp_counter[0]}"

    for stmt in ast_statements:

        if stmt["type"] == "declaration":
            if stmt["value"] is not None:
                # Has an initializer expression
                expr_tokens = stmt.get("expr_tokens", [])
                if needs_decomposition(expr_tokens):
                    # Complex expression — break into TAC steps
                    result_var = decompose_expression(expr_tokens, tac, new_temp)
                    tac.append(f"{stmt['name']} = {result_var}")
                else:
                    # Simple value or single variable
                    tac.append(f"{stmt['name']} = {stmt['value']}")
            else:
                # Declaration without value
                tac.append(f"{stmt['name']} = 0")

        elif stmt["type"] == "assignment":
            expr_tokens = stmt.get("expr_tokens", [])
            if needs_decomposition(expr_tokens):
                result_var = decompose_expression(expr_tokens, tac, new_temp)
                tac.append(f"{stmt['name']} = {result_var}")
            else:
                tac.append(f"{stmt['name']} = {stmt['value']}")

        elif stmt["type"] == "return":
            if stmt["value"]:
                expr_tokens = stmt.get("expr_tokens", [])
                if needs_decomposition(expr_tokens):
                    result_var = decompose_expression(expr_tokens, tac, new_temp)
                    tac.append(f"return {result_var}")
                else:
                    tac.append(f"return {stmt['value']}")
            else:
                tac.append("return")

        elif stmt["type"] == "function_call":
            # Reconstruct the call
            tac.append(f"call {stmt['name']} {stmt['args']}")

    return tac


def needs_decomposition(expr_tokens):
    """
    Check if an expression has operators that need to be broken into TAC steps.
    Simple values (single number or variable) don't need decomposition.
    """
    if not expr_tokens:
        return False
    # Count actual operators in the expression
    operators = [t for t in expr_tokens if t["type"] == "OPERATOR" and t["value"] in ("+", "-", "*", "/", "%")]
    return len(operators) > 0


def decompose_expression(expr_tokens, tac, new_temp):
    """
    Break a complex expression into Three Address Code.
    Handles operator precedence (* / % before + -).
    Returns the name of the variable holding the final result.
    """
    # Convert tokens to a simpler list for processing
    items = []
    for t in expr_tokens:
        items.append(t["value"])

    # Handle parenthesized sub-expressions first (recursively)
    items = resolve_parentheses(items, tac, new_temp)

    # Now handle precedence: first * / %, then + -
    items = process_operators(items, ["*", "/", "%"], tac, new_temp)
    items = process_operators(items, ["+", "-"], tac, new_temp)

    # Should be left with a single item
    if len(items) == 1:
        return items[0]
    else:
        # Fallback: join remaining items
        return " ".join(items)


def resolve_parentheses(items, tac, new_temp):
    """
    Find innermost parenthesized groups, evaluate them, and replace with temp vars.
    """
    while "(" in items:
        # Find the last '(' — this gives us the innermost group
        open_idx = None
        for i, item in enumerate(items):
            if item == "(":
                open_idx = i

        if open_idx is None:
            break

        # Find matching ')'
        close_idx = None
        for i in range(open_idx + 1, len(items)):
            if items[i] == ")":
                close_idx = i
                break

        if close_idx is None:
            break

        # Extract the sub-expression inside parentheses
        sub_items = items[open_idx + 1:close_idx]

        # Process the sub-expression
        sub_items = process_operators(sub_items, ["*", "/", "%"], tac, new_temp)
        sub_items = process_operators(sub_items, ["+", "-"], tac, new_temp)

        if len(sub_items) == 1:
            result = sub_items[0]
        else:
            result = " ".join(sub_items)

        # Replace the parenthesized group with the result
        items = items[:open_idx] + [result] + items[close_idx + 1:]

    return items


def process_operators(items, operators, tac, new_temp):
    """
    Scan left to right for the given operators.
    For each one found, generate a TAC instruction and replace with temp var.
    """
    i = 0
    while i < len(items):
        if items[i] in operators and i > 0 and i < len(items) - 1:
            left = items[i - 1]
            op = items[i]
            right = items[i + 1]
            temp = new_temp()
            tac.append(f"{temp} = {left} {op} {right}")
            # Replace left, op, right with temp
            items = items[:i - 1] + [temp] + items[i + 2:]
            # Don't increment i — check same position again
        else:
            i += 1
    return items
