"""
Code Generator Module
Generates readable, optimized C source code from the final AST.
"""


def generate_code(live_ast, original_source):
    """
    Takes the list of live AST statements and the original source code.
    Returns the optimized C source code as a string.
    """
    lines = []
    indent = "    "  # 4 spaces for indentation

    # Check if original source had includes
    has_include = False
    has_main = False
    for src_line in original_source.split("\n"):
        stripped = src_line.strip()
        if stripped.startswith("#include"):
            has_include = True
        if "main" in stripped and ("int" in stripped or "void" in stripped):
            has_main = True

    # Add #include if the original had it
    if has_include:
        lines.append("#include <stdio.h>")
        lines.append("")

    # Add main function wrapper if original had it
    if has_main:
        lines.append("int main() {")

    # Generate each statement
    for stmt in live_ast:
        code_line = format_statement(stmt)
        if has_main:
            lines.append(indent + code_line)
        else:
            lines.append(code_line)

    # Close main function
    if has_main:
        # Check if there's already a return statement
        has_return = any(s["type"] == "return" for s in live_ast)
        if not has_return:
            lines.append(indent + "return 0;")
        lines.append("}")

    return "\n".join(lines)


def format_statement(stmt):
    """Convert an AST statement dict back to C code."""
    if stmt["type"] == "declaration":
        if stmt["value"] is not None:
            return f"{stmt['data_type']} {stmt['name']} = {stmt['value']};"
        else:
            return f"{stmt['data_type']} {stmt['name']};"

    elif stmt["type"] == "assignment":
        return f"{stmt['name']} = {stmt['value']};"

    elif stmt["type"] == "return":
        if stmt["value"]:
            return f"return {stmt['value']};"
        else:
            return "return;"

    elif stmt["type"] == "function_call":
        args = stmt["args"]
        # Clean up spacing around punctuation in arguments
        args = clean_args(args)
        # Remove outer parentheses if present, then re-add them
        if args.startswith("(") and args.endswith(")"):
            return f"{stmt['name']}{args};"
        else:
            return f"{stmt['name']}({args});"

    return "// unknown statement"


def clean_args(args):
    """
    Clean up token-joined argument strings.
    Removes extra spaces around parentheses and commas.
    e.g. '( "%d %d" , a , b )' -> '("%d %d", a, b)'
    """
    # Remove space after '(' and before ')'
    result = args.strip()
    if result.startswith("("):
        result = "(" + result[1:].lstrip()
    if result.endswith(")"):
        result = result[:-1].rstrip() + ")"
    # Fix spacing around commas: ' , ' -> ', '
    import re
    result = re.sub(r'\s*,\s*', ', ', result)
    return result


def generate_comparison(original_source, optimized_code, folding_changes, dead_removed):
    """
    Generate a comparison summary between original and optimized code.
    """
    original_lines = [l.strip() for l in original_source.split("\n") if l.strip()]
    optimized_lines = [l.strip() for l in optimized_code.split("\n") if l.strip()]

    # Count meaningful statements (not includes, braces, empty lines)
    def count_statements(lines):
        count = 0
        for line in lines:
            line = line.strip()
            if line and line != "{" and line != "}" and not line.startswith("#") and not line.startswith("//"):
                count += 1
        return count

    orig_count = count_statements(original_lines)
    opt_count = count_statements(optimized_lines)
    constants_folded = len(folding_changes)
    dead_eliminated = len(dead_removed)
    total_removed = orig_count - opt_count

    if orig_count > 0:
        optimization_pct = round((total_removed / orig_count) * 100, 1)
    else:
        optimization_pct = 0

    return {
        "original_statements": orig_count,
        "optimized_statements": opt_count,
        "constants_folded": constants_folded,
        "dead_code_removed": dead_eliminated,
        "total_removed": total_removed,
        "optimization_percentage": optimization_pct
    }
