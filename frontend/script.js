/* ═══════════════════════════════════════════════
   Mini Compiler — Frontend JavaScript
   Handles UI interactions and backend communication
   ═══════════════════════════════════════════════ */

// ──── Configuration ────
const API_URL = "https://mini-compiler-p4uz.onrender.com";

// ──── Example programs ────
const EXAMPLES = {
    1: {
        name: "Constant Folding",
        code: `#include <stdio.h>

int main() {
    int a = 5 + 3;
    int b = 10 * 2;
    int c = (4 + 6) * 3;
    printf("%d %d %d", a, b, c);
    return 0;
}`
    },
    2: {
        name: "Dead Code Elimination",
        code: `#include <stdio.h>

int main() {
    int x = 10;
    int unused1 = 20;
    int unused2 = 30;
    int y = x + 5;
    printf("%d %d", x, y);
    return 0;
}`
    },
    3: {
        name: "Combined Optimization",
        code: `#include <stdio.h>

int main() {
    int a = 2 + 3 * 4;
    int dead = 100;
    int b = a + 1;
    int waste = 50 + 50;
    printf("%d", b);
    return 0;
}`
    },
    4: {
        name: "Variable Dependencies",
        code: `#include <stdio.h>

int main() {
    int a = 10;
    int b = 20;
    int c = a + b;
    int unused = 50;
    int d = 7 * 8;
    printf("%d %d", c, d);
    return 0;
}`
    },
    5: {
        name: "Syntax Error",
        code: `#include <stdio.h>

int main() {
    int x = 10
    printf("%d", x);
    return 0;
}`
    }
};

// ──── State ────
let isCompiling = false;
let lastResult = null;

// ══════════════════════════════
//  INITIALIZATION
// ══════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
    updateLineNumbers();
    checkBackend();

    const editor = document.getElementById("codeEditor");

    // Update line numbers on every change
    editor.addEventListener("input", updateLineNumbers);
    editor.addEventListener("scroll", syncScroll);
    editor.addEventListener("keydown", handleTab);

    // Periodic backend health check
    setInterval(checkBackend, 15000);

    // Close dropdown when clicking elsewhere
    document.addEventListener("click", (e) => {
        if (!e.target.closest("#exampleDropdown")) {
            document.getElementById("exampleMenu").classList.remove("show");
        }
    });
});


// ══════════════════════════════
//  LINE NUMBERS
// ══════════════════════════════

function updateLineNumbers() {
    const editor = document.getElementById("codeEditor");
    const lineNums = document.getElementById("lineNumbers");
    const lines = editor.value.split("\n");
    let html = "";
    for (let i = 1; i <= lines.length; i++) {
        html += i + "\n";
    }
    lineNums.textContent = html;
}

function syncScroll() {
    const editor = document.getElementById("codeEditor");
    const lineNums = document.getElementById("lineNumbers");
    lineNums.scrollTop = editor.scrollTop;
}

function handleTab(e) {
    if (e.key === "Tab") {
        e.preventDefault();
        const editor = e.target;
        const start = editor.selectionStart;
        const end = editor.selectionEnd;
        editor.value = editor.value.substring(0, start) + "    " + editor.value.substring(end);
        editor.selectionStart = editor.selectionEnd = start + 4;
        updateLineNumbers();
    }
}


// ══════════════════════════════
//  BACKEND HEALTH CHECK
// ══════════════════════════════

async function checkBackend() {
    const badge = document.getElementById("backendStatus");
    const dot = badge.querySelector(".status-dot");
    const text = badge.querySelector(".status-text");
    try {
        const res = await fetch(API_URL + "/health", { signal: AbortSignal.timeout(3000) });
        if (res.ok) {
            badge.className = "status-badge connected";
            text.textContent = "Backend Connected";
        } else {
            throw new Error("Not OK");
        }
    } catch {
        badge.className = "status-badge disconnected";
        text.textContent = "Backend Offline";
    }
}


// ══════════════════════════════
//  RUN COMPILER
// ══════════════════════════════

async function runCompiler() {
    if (isCompiling) return;

    const code = document.getElementById("codeEditor").value;
    if (!code.trim()) {
        showToast("Please enter some C source code", "error");
        return;
    }

    isCompiling = true;
    document.getElementById("btnRun").disabled = true;
    document.getElementById("btnRun").innerHTML = '<span class="btn-icon">⏳</span> Compiling…';

    // Reset pipeline and outputs
    resetPipeline();
    clearOutputs();

    const stages = ["lexical", "syntax", "intermediate", "folding", "deadcode", "codegen"];

    try {
        // Animate stages sequentially
        for (const stage of stages) {
            setStage(stage, "processing");
            await sleep(200); // Small delay for visual effect
        }

        const res = await fetch(API_URL + "/compile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code: code })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Server error");
        }

        const data = await res.json();
        lastResult = data;

        if (data.success) {
            // Mark all stages as completed
            for (const stage of stages) {
                setStage(stage, "completed");
            }
            displayResults(data, code);
            showToast("Compilation successful!", "success");
        } else {
            // Mark stages up to the error
            const errorStage = data.error_stage;
            let hitError = false;
            for (const stage of stages) {
                if (hitError) {
                    setStage(stage, "pending");
                } else if (mapErrorStage(errorStage) === stage) {
                    setStage(stage, "error");
                    hitError = true;
                } else {
                    setStage(stage, "completed");
                }
            }
            displayErrors(data);
            showToast("Compilation failed — see errors", "error");
        }

    } catch (err) {
        for (const stage of stages) {
            setStage(stage, "error");
        }
        showToast("Connection error: " + err.message, "error");
        displayConnectionError(err.message);
    } finally {
        isCompiling = false;
        document.getElementById("btnRun").disabled = false;
        document.getElementById("btnRun").innerHTML = '<span class="btn-icon">▶</span> Run Compiler';
    }
}

function mapErrorStage(stage) {
    const map = {
        "lexical": "lexical",
        "syntax": "syntax",
        "intermediate": "intermediate",
        "constant_folding": "folding",
        "dead_code": "deadcode",
        "code_generation": "codegen",
        "internal": "lexical"
    };
    return map[stage] || "lexical";
}


// ══════════════════════════════
//  DISPLAY RESULTS
// ══════════════════════════════

function displayResults(data, originalCode) {

    // ── Tokens ──
    if (data.lexical) {
        let html = "";
        data.lexical.tokens.forEach(tok => {
            const cls = tokenClass(tok.type);
            html += `<span class="${cls}">${escHtml(tok.type)}</span>: ${escHtml(tok.value)}   <span style="color:var(--text-muted)">[line ${tok.line}]</span>\n`;
        });
        html += `\n── ${data.lexical.token_count} tokens identified ──`;
        setOutput("tokens", html);
    }

    // ── Syntax ──
    if (data.syntax) {
        let html = "";
        if (data.syntax.valid) {
            html += `<span class="highlight-kept">✓ Syntax analysis passed</span>\n\n`;
            html += `Statements found: ${data.syntax.statement_count}\n\n`;
            data.syntax.ast.forEach(s => {
                html += formatAstNode(s) + "\n";
            });
        } else {
            html += `<span class="highlight-removed">✗ Syntax errors found</span>\n\n`;
            data.syntax.errors.forEach(e => {
                html += `<span class="highlight-removed">Line ${e.line}: ${escHtml(e.message)}</span>\n`;
            });
        }
        setOutput("syntax", html);
    }

    // ── TAC ──
    if (data.intermediate) {
        let html = "── Three Address Code ──\n\n";
        data.intermediate.tac.forEach((inst, i) => {
            html += `${String(i + 1).padStart(3, " ")}  ${escHtml(inst)}\n`;
        });
        html += `\n── ${data.intermediate.instruction_count} instructions ──`;
        setOutput("tac", html);
    }

    // ── Constant Folding ──
    if (data.constant_folding) {
        let html = "";
        if (data.constant_folding.constants_folded > 0) {
            html += `<span class="highlight-kept">✓ ${data.constant_folding.constants_folded} constant(s) folded</span>\n\n`;
            data.constant_folding.changes.forEach(c => {
                html += `<span class="highlight-folded">Line ${c.line}:</span> ${escHtml(c.description)}\n`;
                html += `  Before: ${escHtml(c.original)}\n`;
                html += `  After:  ${escHtml(c.optimized)}\n\n`;
            });
        } else {
            html += `<span style="color:var(--text-secondary)">No constant expressions to fold.</span>\n`;
        }
        setOutput("folding", html);
    }

    // ── Dead Code ──
    if (data.dead_code) {
        let html = "";
        if (data.dead_code.dead_count > 0) {
            html += `<span class="highlight-kept">✓ ${data.dead_code.dead_count} dead statement(s) removed</span>\n\n`;
            data.dead_code.removed.forEach(r => {
                html += `<span class="highlight-removed">Line ${r.line}: ${escHtml(r.statement)}</span>\n`;
                html += `  Reason: ${escHtml(r.reason)}\n\n`;
            });
        } else {
            html += `<span style="color:var(--text-secondary)">No dead code detected.</span>\n`;
        }
        setOutput("deadcode", html);
    }

    // ── Optimized Code ──
    if (data.code_generation) {
        const optCode = data.code_generation.optimized_code;
        setOutput("optimized", highlightC(optCode));
        document.getElementById("optimized-header").style.display = "flex";
    }

    // ── Comparison ──
    if (data.code_generation) {
        document.getElementById("placeholder-comparison").style.display = "none";
        document.getElementById("comparison-view").style.display = "grid";
        document.getElementById("compare-original").innerHTML = highlightC(originalCode);
        document.getElementById("compare-optimized").innerHTML = highlightC(data.code_generation.optimized_code);
    }

    // ── Statistics ──
    if (data.statistics) {
        const s = data.statistics;
        document.getElementById("statOriginal").textContent = s.original_statements;
        document.getElementById("statOptimized").textContent = s.optimized_statements;
        document.getElementById("statFolded").textContent = s.constants_folded;
        document.getElementById("statDead").textContent = s.dead_code_removed;
        document.getElementById("statPercent").textContent = s.optimization_percentage + "%";
        document.getElementById("statsBar").style.display = "flex";
    }

    // Switch to optimized tab
    switchTab("optimized");
}

function displayErrors(data) {
    if (data.errors && data.errors.length > 0) {
        let html = `<span class="highlight-removed">✗ Compilation Error (stage: ${data.error_stage || "unknown"})</span>\n\n`;
        data.errors.forEach(e => {
            html += `<span class="highlight-removed">`;
            if (e.line) html += `Line ${e.line}: `;
            html += `${escHtml(e.message)}</span>\n`;
        });
        setOutput("syntax", html);
        switchTab("syntax");
    }

    // Still show tokens if available
    if (data.lexical) {
        let html = "";
        data.lexical.tokens.forEach(tok => {
            const cls = tokenClass(tok.type);
            html += `<span class="${cls}">${escHtml(tok.type)}</span>: ${escHtml(tok.value)}   <span style="color:var(--text-muted)">[line ${tok.line}]</span>\n`;
        });
        setOutput("tokens", html);
    }
}

function displayConnectionError(msg) {
    let html = `<span class="highlight-removed">✗ Cannot connect to backend</span>\n\n`;
    html += `Error: ${escHtml(msg)}\n\n`;
    html += `Make sure the Python backend is running:\n`;
    html += `  cd backend\n`;
    html += `  pip install -r requirements.txt\n`;
    html += `  python main.py\n`;
    setOutput("syntax", html);
    switchTab("syntax");
}


// ══════════════════════════════
//  UI HELPERS
// ══════════════════════════════

function setOutput(pane, html) {
    document.getElementById("placeholder-" + pane).style.display = "none";
    document.getElementById("output-" + pane).innerHTML = html;
}

function clearOutputs() {
    const panes = ["tokens", "syntax", "tac", "folding", "deadcode", "optimized"];
    panes.forEach(p => {
        const placeholder = document.getElementById("placeholder-" + p);
        if (placeholder) placeholder.style.display = "flex";
        const output = document.getElementById("output-" + p);
        if (output) output.innerHTML = "";
    });
    document.getElementById("optimized-header").style.display = "none";
    document.getElementById("placeholder-comparison").style.display = "flex";
    document.getElementById("comparison-view").style.display = "none";
    document.getElementById("compare-original").innerHTML = "";
    document.getElementById("compare-optimized").innerHTML = "";
    document.getElementById("statsBar").style.display = "none";
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll(".tab").forEach(t => {
        t.classList.toggle("active", t.dataset.tab === tabName);
    });
    // Update tab panes
    document.querySelectorAll(".tab-pane").forEach(p => {
        p.classList.toggle("active", p.id === "pane-" + tabName);
    });
}

function setStage(stage, state) {
    const el = document.querySelector(`.pipeline-stage[data-stage="${stage}"]`);
    if (el) {
        el.className = "pipeline-stage " + state;
    }
}

function resetPipeline() {
    document.querySelectorAll(".pipeline-stage").forEach(el => {
        el.className = "pipeline-stage";
    });
}


// ══════════════════════════════
//  BUTTON HANDLERS
// ══════════════════════════════

function resetAll() {
    document.getElementById("codeEditor").value = "";
    updateLineNumbers();
    clearOutputs();
    resetPipeline();
    switchTab("tokens");
    lastResult = null;
    showToast("Editor and results cleared", "success");
}

function clearEditor() {
    document.getElementById("codeEditor").value = "";
    updateLineNumbers();
}

function copySource() {
    const code = document.getElementById("codeEditor").value;
    navigator.clipboard.writeText(code).then(() => {
        showToast("Source code copied!", "success");
    }).catch(() => {
        showToast("Failed to copy", "error");
    });
}

function copyOptimized() {
    if (lastResult && lastResult.code_generation) {
        navigator.clipboard.writeText(lastResult.code_generation.optimized_code).then(() => {
            showToast("Optimized code copied!", "success");
        }).catch(() => {
            showToast("Failed to copy", "error");
        });
    }
}

function toggleExamples() {
    document.getElementById("exampleMenu").classList.toggle("show");
}

function loadExample(num) {
    const ex = EXAMPLES[num];
    if (ex) {
        document.getElementById("codeEditor").value = ex.code;
        updateLineNumbers();
        document.getElementById("exampleMenu").classList.remove("show");
        showToast(`Loaded: ${ex.name}`, "success");
    }
}


// ══════════════════════════════
//  TOAST NOTIFICATIONS
// ══════════════════════════════

function showToast(msg, type) {
    const toast = document.getElementById("toast");
    toast.textContent = msg;
    toast.className = "toast show " + (type || "");
    setTimeout(() => {
        toast.className = "toast";
    }, 3000);
}


// ══════════════════════════════
//  FORMATTING HELPERS
// ══════════════════════════════

function escHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function tokenClass(type) {
    const map = {
        "KEYWORD": "token-keyword",
        "IDENTIFIER": "token-type",
        "CONSTANT": "token-number",
        "STRING": "token-string",
        "COMMENT": "token-comment",
        "OPERATOR": "token-operator",
        "PREPROCESSOR": "token-func",
        "SEPARATOR": "token-operator"
    };
    return map[type] || "";
}

function formatAstNode(node) {
    if (node.type === "declaration") {
        const val = node.value !== null ? ` = ${node.value}` : "";
        return `  [declaration] ${node.data_type} ${node.name}${val};`;
    }
    if (node.type === "assignment") {
        return `  [assignment]  ${node.name} = ${node.value};`;
    }
    if (node.type === "function_call") {
        return `  [call]        ${node.name}${node.args};`;
    }
    if (node.type === "return") {
        return `  [return]      ${node.value};`;
    }
    return `  [${node.type}]`;
}

function highlightC(code) {
    // Simple syntax highlighting for C code in output
    const keywords = ["int", "float", "double", "char", "void", "return", "if", "else", "while", "for", "do", "break", "continue", "main", "include"];
    const funcs = ["printf", "scanf", "puts", "gets"];

    let lines = code.split("\n");
    let result = [];

    for (let line of lines) {
        // Escape HTML first
        let escaped = escHtml(line);

        // Highlight preprocessor
        if (escaped.trim().startsWith("#")) {
            result.push(`<span class="token-func">${escaped}</span>`);
            continue;
        }

        // Highlight comments
        if (escaped.trim().startsWith("//")) {
            result.push(`<span class="token-comment">${escaped}</span>`);
            continue;
        }

        // Highlight strings
        escaped = escaped.replace(/(&quot;[^&]*?&quot;)/g, '<span class="token-string">$1</span>');

        // Highlight numbers (standalone)
        escaped = escaped.replace(/\b(\d+\.?\d*)\b/g, '<span class="token-number">$1</span>');

        // Highlight keywords
        for (const kw of keywords) {
            const re = new RegExp("\\b(" + kw + ")\\b", "g");
            escaped = escaped.replace(re, '<span class="token-keyword">$1</span>');
        }

        // Highlight function names
        for (const fn of funcs) {
            const re = new RegExp("\\b(" + fn + ")\\b", "g");
            escaped = escaped.replace(re, '<span class="token-func">$1</span>');
        }

        result.push(escaped);
    }

    return result.join("\n");
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
