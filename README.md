# Mini Compiler — Dead Code Elimination & Constant Folding

A web-based educational compiler that demonstrates two important optimization techniques on C source code:

1. **Constant Folding** — evaluates constant expressions at compile time
2. **Dead Code Elimination** — removes unused variables and assignments

Built as a Compiler Design course project.

---

## Project Objectives

- Implement a real compilation pipeline (lexer → parser → intermediate code → optimizations → code generation)
- Demonstrate constant folding and dead code elimination on C programs
- Provide a professional, IDE-like web interface
- Keep the code simple and readable for students

---

## Technologies Used

| Component | Technology |
|-----------|-----------|
| Frontend  | HTML5, CSS3, Vanilla JavaScript |
| Backend   | Python, FastAPI, Uvicorn |
| Input Language | C (supported subset) |

---

## Folder Structure

```
MINI-COMPILER/
│
├── frontend/
│   ├── index.html          # Main UI page
│   ├── style.css           # Dark theme styling
│   └── script.js           # Frontend logic & API calls
│
├── backend/
│   ├── main.py             # FastAPI app & endpoints
│   ├── lexer.py            # Tokenizer (lexical analysis)
│   ├── parser.py           # Syntax checker & AST builder
│   ├── intermediate.py     # Three Address Code generator
│   ├── constant_folding.py # Constant folding optimizer
│   ├── dead_code.py        # Dead code eliminator
│   ├── code_generator.py   # Optimized C code generator
│   └── requirements.txt    # Python dependencies
│
├── examples/
│   └── test_cases.c        # Sample C programs for testing
│
└── README.md
```

---

## Compiler Workflow

```
C Source Code
      │
      ▼
Lexical Analysis (lexer.py)
      │  → Breaks code into tokens
      ▼
Syntax Analysis (parser.py)
      │  → Checks grammar, builds AST
      ▼
Intermediate Code (intermediate.py)
      │  → Generates Three Address Code
      ▼
Constant Folding (constant_folding.py)
      │  → Evaluates compile-time constants
      ▼
Dead Code Elimination (dead_code.py)
      │  → Removes unused variables
      ▼
Code Generation (code_generator.py)
      │  → Produces optimized C source
      ▼
Display Results
```

---

## Supported C Subset

The compiler handles the following C constructs:

- `#include <stdio.h>`
- `int main() { ... }`
- Variable declarations: `int x = expr;`
- Assignments: `x = expr;`
- Arithmetic: `+`, `-`, `*`, `/`, `%`, parentheses
- `printf(...)` and `scanf(...)` calls
- `return` statements
- Single-line (`//`) and multi-line (`/* */`) comments

---

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A modern web browser (Chrome, Firefox, Edge)

### Step 1: Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Start the Python backend

```bash
cd backend
python main.py
```

The server starts at **http://localhost:8000**.

### Step 3: Open the frontend

Open `frontend/index.html` in your web browser. You can:

- Double-click the file, OR
- Use a simple HTTP server:

```bash
cd frontend
python -m http.server 3000
```

Then open **http://localhost:3000** in your browser.

### Step 4: Verify connection

The header shows a green **"Backend Connected"** badge when the frontend can reach the backend.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/health` | Backend health check |
| POST   | `/compile` | Run full compilation pipeline |
| POST   | `/lexical-analysis` | Run only lexical analysis |
| POST   | `/syntax-analysis` | Run only syntax analysis |

### Request format (POST endpoints)

```json
{
    "code": "#include <stdio.h>\nint main() {\n    int a = 5 + 3;\n    printf(\"%d\", a);\n    return 0;\n}"
}
```

### Response format (`/compile`)

```json
{
    "success": true,
    "lexical": { "tokens": [...], "token_count": 25 },
    "syntax": { "ast": [...], "valid": true },
    "intermediate": { "tac": [...] },
    "constant_folding": { "changes": [...], "constants_folded": 1 },
    "dead_code": { "removed": [...], "dead_count": 0 },
    "code_generation": { "optimized_code": "..." },
    "statistics": {
        "original_statements": 4,
        "optimized_statements": 4,
        "constants_folded": 1,
        "dead_code_removed": 0,
        "optimization_percentage": 0.0
    }
}
```

---

## Sample Input & Output

### Input

```c
#include <stdio.h>

int main() {
    int a = 5 + 3;
    int b = 10 * 2;
    int unused = 99;
    int c = a + b;
    printf("%d %d %d", a, b, c);
    return 0;
}
```

### Optimized Output

```c
#include <stdio.h>

int main() {
    int a = 8;
    int b = 20;
    int c = 28;
    printf("%d %d %d", a, b, c);
    return 0;
}
```

**What happened:**
- `5 + 3` → folded to `8` (constant folding)
- `10 * 2` → folded to `20` (constant folding)
- `a + b` → folded to `28` (constant propagation)
- `int unused = 99;` → removed (dead code elimination)

---

## How Each File Works

### lexer.py
Scans the source code character by character and groups characters into tokens (keywords, identifiers, operators, constants, separators, strings, comments).

### parser.py
Reads the token stream and checks for syntax errors (missing semicolons, unmatched braces, invalid declarations). Produces an AST — a list of statement dictionaries.

### intermediate.py
Converts AST statements into Three Address Code (TAC), where each instruction has at most one operator. Complex expressions are broken into steps using temporary variables.

### constant_folding.py
Walks through the AST and evaluates arithmetic expressions made entirely of constants. Also propagates known constant values through variable references.

### dead_code.py
Identifies which variables are actually used in program output (printf, return, etc.) and traces their dependencies. Any variable not reachable from output is dead code and gets removed.

### code_generator.py
Takes the final optimized AST and reconstructs clean, properly formatted C source code with correct indentation and structure.

### main.py
The FastAPI application that ties all modules together. Receives source code via HTTP POST, runs the full pipeline, and returns structured JSON results.

---

## Testing the Optimizations

1. **Constant Folding**: Enter code with arithmetic like `int x = 5 + 3 * 4;` — the result should show `int x = 17;`
2. **Dead Code Elimination**: Declare variables that are never used in printf or return — they should be removed
3. **Combined**: Use both patterns together and check the statistics panel
4. **Dependencies**: Make sure variables used indirectly (e.g., `c = a + b` where `c` is printed) are NOT removed
5. **Errors**: Enter code with missing semicolons — the parser should report clear errors

---

## License

Educational project — free to use and modify.
