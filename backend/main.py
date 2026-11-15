"""
Main FastAPI Application
Connects all compiler modules and exposes API endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import compiler modules
from lexer import tokenize, format_tokens
from parser import parse
from intermediate import generate_tac
from constant_folding import fold_constants
from dead_code import eliminate_dead_code
from code_generator import generate_code, generate_comparison

# ---- Create the FastAPI app ----
app = FastAPI(title="Mini Compiler API", version="1.0.0")

# Allow frontend (running on a different port) to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Request model ----
class SourceCode(BaseModel):
    code: str


# ---- Health check ----
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Mini Compiler backend is running"}


# ---- Full compilation pipeline ----
@app.post("/compile")
def compile_code(source: SourceCode):
    code = source.code

    if not code or not code.strip():
        raise HTTPException(status_code=400, detail="No source code provided")

    result = {}

    try:
        # Stage 1: Lexical Analysis
        lex_result = tokenize(code)
        tokens = lex_result["tokens"]
        lex_errors = lex_result["errors"]

        result["lexical"] = {
            "tokens": tokens,
            "formatted": format_tokens(tokens),
            "token_count": len(tokens),
            "errors": lex_errors
        }

        if lex_errors:
            result["success"] = False
            result["error_stage"] = "lexical"
            result["errors"] = lex_errors
            return result

        # Stage 2: Syntax Analysis
        parse_result = parse(tokens)
        ast = parse_result["ast"]
        parse_errors = parse_result["errors"]
        parse_warnings = parse_result["warnings"]

        result["syntax"] = {
            "ast": make_serializable(ast),
            "statement_count": len(ast),
            "errors": parse_errors,
            "warnings": parse_warnings,
            "valid": len(parse_errors) == 0
        }

        if parse_errors:
            result["success"] = False
            result["error_stage"] = "syntax"
            result["errors"] = parse_errors
            return result

        # Stage 3: Intermediate Code Generation
        tac = generate_tac(ast)

        result["intermediate"] = {
            "tac": tac,
            "instruction_count": len(tac)
        }

        # Stage 4: Constant Folding
        fold_result = fold_constants(ast)
        folded_ast = fold_result["folded_ast"]
        fold_changes = fold_result["changes"]

        result["constant_folding"] = {
            "changes": fold_changes,
            "constants_folded": len(fold_changes),
            "folded_statements": make_serializable(folded_ast)
        }

        # Stage 5: Dead Code Elimination
        dce_result = eliminate_dead_code(folded_ast)
        live_ast = dce_result["live_ast"]
        removed = dce_result["removed"]

        result["dead_code"] = {
            "removed": removed,
            "dead_count": len(removed),
            "live_statements": make_serializable(live_ast)
        }

        # Stage 6: Code Generation
        optimized_code = generate_code(live_ast, code)

        result["code_generation"] = {
            "optimized_code": optimized_code
        }

        # Generate TAC for optimized code too
        optimized_tac = generate_tac(live_ast)
        result["optimized_intermediate"] = {
            "tac": optimized_tac,
            "instruction_count": len(optimized_tac)
        }

        # Statistics
        stats = generate_comparison(code, optimized_code, fold_changes, removed)
        result["statistics"] = stats

        result["success"] = True

    except Exception as e:
        result["success"] = False
        result["error_stage"] = "internal"
        result["errors"] = [{"message": str(e), "line": 0}]

    return result


# ---- Individual stage endpoints ----
@app.post("/lexical-analysis")
def lexical_analysis(source: SourceCode):
    if not source.code or not source.code.strip():
        raise HTTPException(status_code=400, detail="No source code provided")

    lex_result = tokenize(source.code)
    return {
        "tokens": lex_result["tokens"],
        "formatted": format_tokens(lex_result["tokens"]),
        "errors": lex_result["errors"]
    }


@app.post("/syntax-analysis")
def syntax_analysis(source: SourceCode):
    if not source.code or not source.code.strip():
        raise HTTPException(status_code=400, detail="No source code provided")

    lex_result = tokenize(source.code)
    if lex_result["errors"]:
        return {"valid": False, "errors": lex_result["errors"]}

    parse_result = parse(lex_result["tokens"])
    return {
        "valid": len(parse_result["errors"]) == 0,
        "ast": make_serializable(parse_result["ast"]),
        "errors": parse_result["errors"],
        "warnings": parse_result["warnings"]
    }


def make_serializable(ast):
    """
    Make AST serializable by removing token objects from statements.
    (Token objects are used internally but aren't needed in JSON output.)
    """
    clean = []
    for stmt in ast:
        s = dict(stmt)
        # Remove internal token lists — they clutter the JSON response
        s.pop("expr_tokens", None)
        s.pop("arg_tokens", None)
        clean.append(s)
    return clean


# ---- Run the server ----
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
