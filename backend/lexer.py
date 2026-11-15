"""
Lexer Module - Lexical Analysis
Breaks C source code into tokens (keywords, identifiers, operators, etc.)
"""

# All C keywords we support
KEYWORDS = {
    "int", "float", "double", "char", "void",
    "if", "else", "while", "for", "do",
    "return", "break", "continue",
    "printf", "scanf",
    "main", "include", "stdio"
}

# Operators (multi-char first so we match them before single-char)
OPERATORS = [
    "==", "!=", "<=", ">=", "&&", "||",
    "++", "--", "+=", "-=", "*=", "/=",
    "+", "-", "*", "/", "%",
    "=", "<", ">", "!", "&", "|"
]

# Separators
SEPARATORS = {";", ",", "(", ")", "{", "}", "[", "]"}


def tokenize(source_code):
    """
    Takes C source code as a string.
    Returns a list of token dictionaries: {type, value, line}
    """
    tokens = []
    errors = []
    lines = source_code.split("\n")

    for line_num, line in enumerate(lines, start=1):
        i = 0
        while i < len(line):
            ch = line[i]

            # ---- Skip whitespace ----
            if ch in " \t\r":
                i += 1
                continue

            # ---- Single-line comment: // ----
            if ch == "/" and i + 1 < len(line) and line[i + 1] == "/":
                comment_text = line[i:]
                tokens.append({"type": "COMMENT", "value": comment_text, "line": line_num})
                break  # rest of line is comment

            # ---- Multi-line comment start: /* (collect until */) ----
            if ch == "/" and i + 1 < len(line) and line[i + 1] == "*":
                comment_text = "/*"
                i += 2
                closed = False
                while i < len(line):
                    if line[i] == "*" and i + 1 < len(line) and line[i + 1] == "/":
                        comment_text += "*/"
                        i += 2
                        closed = True
                        break
                    comment_text += line[i]
                    i += 1
                tokens.append({"type": "COMMENT", "value": comment_text, "line": line_num})
                if not closed:
                    # For simplicity, treat unclosed multi-line comments on same line
                    pass
                continue

            # ---- Preprocessor directive: #include ----
            if ch == "#":
                directive = ""
                while i < len(line):
                    directive += line[i]
                    i += 1
                tokens.append({"type": "PREPROCESSOR", "value": directive.strip(), "line": line_num})
                break

            # ---- String literal: "..." ----
            if ch == '"':
                string_val = '"'
                i += 1
                while i < len(line) and line[i] != '"':
                    if line[i] == '\\' and i + 1 < len(line):
                        string_val += line[i] + line[i + 1]
                        i += 2
                    else:
                        string_val += line[i]
                        i += 1
                if i < len(line):
                    string_val += '"'
                    i += 1
                else:
                    errors.append({"message": "Unterminated string literal", "line": line_num})
                tokens.append({"type": "STRING", "value": string_val, "line": line_num})
                continue

            # ---- Character literal: '...' ----
            if ch == "'":
                char_val = "'"
                i += 1
                while i < len(line) and line[i] != "'":
                    char_val += line[i]
                    i += 1
                if i < len(line):
                    char_val += "'"
                    i += 1
                tokens.append({"type": "CONSTANT", "value": char_val, "line": line_num})
                continue

            # ---- Number (integer or float) ----
            if ch.isdigit():
                num_str = ""
                has_dot = False
                while i < len(line) and (line[i].isdigit() or line[i] == "."):
                    if line[i] == ".":
                        if has_dot:
                            break
                        has_dot = True
                    num_str += line[i]
                    i += 1
                tokens.append({"type": "CONSTANT", "value": num_str, "line": line_num})
                continue

            # ---- Identifier or Keyword ----
            if ch.isalpha() or ch == "_":
                ident = ""
                while i < len(line) and (line[i].isalnum() or line[i] == "_"):
                    ident += line[i]
                    i += 1
                if ident in KEYWORDS:
                    tokens.append({"type": "KEYWORD", "value": ident, "line": line_num})
                else:
                    tokens.append({"type": "IDENTIFIER", "value": ident, "line": line_num})
                continue

            # ---- Operators (try multi-char first) ----
            matched_op = False
            for op in OPERATORS:
                if line[i:i + len(op)] == op:
                    tokens.append({"type": "OPERATOR", "value": op, "line": line_num})
                    i += len(op)
                    matched_op = True
                    break
            if matched_op:
                continue

            # ---- Separators ----
            if ch in SEPARATORS:
                tokens.append({"type": "SEPARATOR", "value": ch, "line": line_num})
                i += 1
                continue

            # ---- Unknown character ----
            errors.append({"message": f"Unknown character '{ch}'", "line": line_num})
            i += 1

    return {"tokens": tokens, "errors": errors}


def format_tokens(token_list):
    """
    Returns a human-readable string of tokens.
    """
    result = []
    for tok in token_list:
        result.append(f"{tok['type']}: {tok['value']}")
    return "\n".join(result)
