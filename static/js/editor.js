/**
 * AI-EVER Code Visualizer — VSCode-like editor (100% offline, zero dependencies).
 *
 * Layout: the highlighted <pre> defines the content size inside ONE scroll
 * container; the transparent <textarea> is absolutely stretched over it.
 * A single scrollbar moves both layers — they can never misalign.
 *
 * Features:
 *   - Python syntax highlighting (custom tokenizer)
 *   - Line numbers with active-line tracking (incremental updates)
 *   - Auto-indent (Enter keeps indent; ":" adds a level)
 *   - Auto-closing brackets/quotes, skip-over, smart backspace
 *   - Tab / Shift+Tab indent / unindent
 *   - Ctrl+Enter = Run
 *   - Execution API for the visualizer: setExecLine(), clearExec(), setReadOnly()
 */
"use strict";

/* ==================================================================
 * Python tokenizer → HTML with token classes
 * ================================================================== */
class PythonHighlighter {
    static KEYWORDS = new Set([
        "False", "None", "True", "and", "as", "assert", "async", "await",
        "break", "class", "continue", "def", "del", "elif", "else", "except",
        "finally", "for", "from", "global", "if", "import", "in", "is",
        "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
        "while", "with", "yield", "match", "case",
    ]);

    static BUILTINS = new Set([
        "print", "len", "range", "int", "str", "float", "bool", "list",
        "dict", "set", "tuple", "input", "sum", "min", "max", "abs", "sorted",
        "enumerate", "zip", "map", "filter", "type", "isinstance", "super",
        "open", "reversed", "round", "any", "all", "id", "hash", "repr",
    ]);

    static TOKEN_RE =
        /(#[^\n]*)|("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')|(\b\d+\.?\d*(?:e[+-]?\d+)?\b)|(\b[A-Za-z_]\w*\b)|([+\-*/%=<>!&|^~@]+)|([\s\S])/g;

    static esc(s) {
        return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    static highlight(source) {
        const out = [];
        const re = new RegExp(this.TOKEN_RE.source, "g");
        let m;
        let prevWord = "";

        while ((m = re.exec(source)) !== null) {
            const [, com, str, num, word, op, other] = m;
            if (com !== undefined) {
                out.push(`<span class="tok-com">${this.esc(com)}</span>`);
                prevWord = "";
            } else if (str !== undefined) {
                out.push(`<span class="tok-str">${this.esc(str)}</span>`);
                prevWord = "";
            } else if (num !== undefined) {
                out.push(`<span class="tok-num">${this.esc(num)}</span>`);
                prevWord = "";
            } else if (word !== undefined) {
                out.push(this.wordSpan(word, prevWord, source, re.lastIndex));
                prevWord = word;
            } else if (op !== undefined) {
                out.push(`<span class="tok-op">${this.esc(op)}</span>`);
                prevWord = "";
            } else {
                out.push(this.esc(other));
                if (other === "\n") prevWord = "";
            }
        }
        return out.join("");
    }

    static wordSpan(word, prevWord, source, idx) {
        const esc = this.esc(word);
        if (this.KEYWORDS.has(word)) return `<span class="tok-kw">${esc}</span>`;
        if (word === "self" || word === "cls") return `<span class="tok-self">${esc}</span>`;
        if (prevWord === "def" || prevWord === "class") return `<span class="tok-def">${esc}</span>`;
        if (this.BUILTINS.has(word)) return `<span class="tok-builtin">${esc}</span>`;
        let i = idx;
        while (source[i] === " " || source[i] === "\t") i++;
        if (source[i] === "(") return `<span class="tok-fn">${esc}</span>`;
        return esc;
    }
}

/* ==================================================================
 * Editor controller
 * ================================================================== */
class CodeEditor {
    static PAIRS = { "(": ")", "[": "]", "{": "}", '"': '"', "'": "'" };

    static SAMPLE = `# Welcome to AI-EVER Code Visualizer!
# Press Run (Ctrl+Enter) and watch every line animate.

def binary_search(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

nums = [5, 7, 7, 8, 8, 10]
target = 8
result = binary_search(nums, target)
print(f"Found {target} at index {result}")
`;

    constructor() {
        this.input = document.getElementById("code-input");
        this.codeEl = document.getElementById("highlight-code");
        this.gutter = document.getElementById("gutter");
        this.scroller = document.getElementById("editor-scroller");
        this.execHl = document.getElementById("exec-highlight");
        this.cursorPos = document.getElementById("cursor-pos");
        this.charCount = document.getElementById("char-count");
        this.INDENT = "    ";

        this._lineCount = 0;
        this._activeLn = null;
        this._execLn = null;
        this._raf = 0;
        this._lineHeight = 22; // matches CSS; measured on first render

        this.ghostText = "";
        this.ghostPos = -1;
        this.ghostReqId = 0;
        this._autoCompleteTimer = null;

        this.bindEvents();
        this.setValue(CodeEditor.SAMPLE);
    }

    /* ---------- Core rendering ---------- */

    getValue() { return this.input.value; }

    setValue(code) {
        this.input.value = code;
        this.render();
    }

    scheduleRender() {
        if (this._raf) return;
        this._raf = requestAnimationFrame(() => {
            this._raf = 0;
            this.render();
        });
    }

    render() {
        let text = this.input.value;
        let html = "";
        const marker = "\u200B"; // zero-width space
        
        if (this.ghostText && this.ghostPos >= 0 && this.ghostPos <= text.length) {
            const before = text.slice(0, this.ghostPos);
            const after = text.slice(this.ghostPos);
            html = PythonHighlighter.highlight(before + marker + after);
            html = html.replace(marker, `<span class="cm-ghost-text">${PythonHighlighter.esc(this.ghostText)}</span>`);
        } else {
            html = PythonHighlighter.highlight(text);
        }
        
        this.codeEl.innerHTML = html + "\n";
        this.measureLineHeight();
        this.updateGutter();
        this.updateStatusBar();
        // Persist for the Flowchart / AST pages
        try { localStorage.setItem("aiever-last-code", this.input.value); } catch (_) {}
    }

    measureLineHeight() {
        const lh = parseFloat(getComputedStyle(this.input).lineHeight);
        if (lh > 0) this._lineHeight = lh;
    }

    updateGutter() {
        const lines = this.input.value.split("\n").length;
        if (lines !== this._lineCount) {
            const frag = [];
            for (let i = 1; i <= lines; i++) {
                frag.push(`<span class="ln" data-line="${i}">${i}</span>`);
            }
            this.gutter.innerHTML = frag.join("");
            this._lineCount = lines;
            this._activeLn = null;
            this._execLn = null;
        }
        this.setActiveLine(this.currentLine());
    }

    setActiveLine(line) {
        if (this._activeLn) this._activeLn.classList.remove("active");
        const el = this.gutter.children[line - 1];
        if (el) {
            el.classList.add("active");
            this._activeLn = el;
        }
    }

    currentLine() {
        return this.input.value
            .slice(0, this.input.selectionStart)
            .split("\n").length;
    }

    updateStatusBar() {
        const pos = this.input.selectionStart;
        const before = this.input.value.slice(0, pos);
        const line = before.split("\n").length;
        const col = pos - before.lastIndexOf("\n");
        this.cursorPos.textContent = `Ln ${line}, Col ${col}`;
        this.charCount.textContent = `${this.input.value.length} chars`;
    }

    /* ---------- Execution visualization API ---------- */

    /** Highlight + glow the currently executing line, auto-scroll to it. */
    setExecLine(line, isError = false) {
        const padTop = 10; // matches CSS padding
        const y = padTop + (line - 1) * this._lineHeight;

        this.execHl.hidden = false;
        this.execHl.style.top = `${y}px`;
        this.execHl.classList.toggle("error-line", isError);
        this.execHl.classList.remove("flash");
        void this.execHl.offsetWidth; // restart CSS animation
        this.execHl.classList.add("flash");

        // gutter marker
        if (this._execLn) this._execLn.classList.remove("exec");
        const g = this.gutter.children[line - 1];
        if (g) { g.classList.add("exec"); this._execLn = g; }

        // auto-scroll: keep the line comfortably in view
        const view = this.scroller;
        if (y < view.scrollTop + 30 || y > view.scrollTop + view.clientHeight - 60) {
            view.scrollTo({ top: Math.max(0, y - view.clientHeight / 2) });
        }
    }

    clearExec() {
        this.execHl.hidden = true;
        this.execHl.classList.remove("error-line");
        if (this._execLn) {
            this._execLn.classList.remove("exec");
            this._execLn = null;
        }
    }

    setReadOnly(readOnly) {
        this.input.readOnly = readOnly;
    }

    /* ---------- Events ---------- */

    bindEvents() {
        this.input.addEventListener("input", () => {
            this.clearGhostText();
            this.scheduleRender();
            this.debounceAutoComplete();
        });
        this.input.addEventListener("keydown", (e) => this.onKeyDown(e));
        // Gutter is inside the scroller now — no scroll sync needed.
        ["keyup", "click"].forEach((ev) =>
            this.input.addEventListener(ev, () => {
                this.updateStatusBar();
                this.setActiveLine(this.currentLine());
            })
        );
    }

    onKeyDown(e) {
        if (this.input.readOnly) return;

        // Ctrl/Cmd+Enter runs — must be checked BEFORE plain Enter
        if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            document.getElementById("btn-run")?.click();
            return;
        }

        // Inline Prompt (Ctrl+I)
        if (e.key === "i" && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            this.showInlinePrompt();
            return;
        }

        const { selectionStart: start, selectionEnd: end, value } = this.input;
        const next = value[start];

        // Tab / Shift+Tab
        if (e.key === "Tab") {
            if (this.ghostText && start === end && start === this.ghostPos) {
                // Accept ghost text
                e.preventDefault();
                this.insertAt(start, start, this.ghostText);
                this.clearGhostText();
                return;
            }
            e.preventDefault();
            if (e.shiftKey) this.unindentLine(start);
            else this.insertAt(start, end, this.INDENT);
            return;
        }

        // Clear ghost text on most keys
        if (e.key !== "Shift" && e.key !== "Control" && e.key !== "Alt") {
            this.clearGhostText();
        }

        // Enter: keep indent, extra level after ":"
        if (e.key === "Enter") {
            e.preventDefault();
            const lineStart = value.lastIndexOf("\n", start - 1) + 1;
            const line = value.slice(lineStart, start);
            const indent = (line.match(/^[ \t]*/) || [""])[0];
            const extra = line.trimEnd().endsWith(":") ? this.INDENT : "";
            this.insertAt(start, end, "\n" + indent + extra);
            return;
        }

        // Auto-close brackets & quotes
        if (CodeEditor.PAIRS[e.key] && start === end) {
            // skip-over: typing a closer that's already there
            if ((e.key === '"' || e.key === "'") && next === e.key) {
                e.preventDefault();
                this.setCaret(start + 1);
                return;
            }
            e.preventDefault();
            this.insertAt(start, end, e.key + CodeEditor.PAIRS[e.key]);
            this.setCaret(start + 1);
            return;
        }

        // skip-over for ) ] }
        if ((e.key === ")" || e.key === "]" || e.key === "}") && next === e.key && start === end) {
            e.preventDefault();
            this.setCaret(start + 1);
            return;
        }

        // Smart backspace: delete empty pair together
        if (e.key === "Backspace" && start === end && start > 0) {
            const prev = value[start - 1];
            if (CodeEditor.PAIRS[prev] === next) {
                e.preventDefault();
                this.deleteRange(start - 1, start + 1);
                this.setCaret(start - 1);
            }
        }
    }

    unindentLine(pos) {
        const v = this.input.value;
        const lineStart = v.lastIndexOf("\n", pos - 1) + 1;
        let removed = 0;
        while (removed < 4 && v[lineStart + removed] === " ") removed++;
        if (removed > 0) {
            this.deleteRange(lineStart, lineStart + removed);
            this.setCaret(Math.max(lineStart, pos - removed));
        }
    }

    setCaret(pos) {
        this.input.selectionStart = this.input.selectionEnd = pos;
    }

    /**
     * Insert text preserving the browser's native undo stack (Ctrl+Z works).
     * execCommand is deprecated but still the only way to keep undo history;
     * falls back to direct value surgery if unavailable.
     */
    insertAt(start, end, text) {
        this.input.focus();
        this.input.setSelectionRange(start, end);
        let done = false;
        try { done = document.execCommand("insertText", false, text); } catch (_) {}
        if (!done) {
            const v = this.input.value;
            this.input.value = v.slice(0, start) + text + v.slice(end);
            this.setCaret(start + text.length);
        }
        this.render();
    }

    /** Delete a range, also undo-friendly. */
    deleteRange(start, end) {
        this.input.focus();
        this.input.setSelectionRange(start, end);
        let done = false;
        try { done = document.execCommand("delete", false); } catch (_) {}
        if (!done) {
            const v = this.input.value;
            this.input.value = v.slice(0, start) + v.slice(end);
        }
        this.render();
    }

    /* ---------- Copilot API ---------- */

    clearGhostText() {
        if (this.ghostText) {
            this.ghostText = "";
            this.ghostPos = -1;
            this.scheduleRender();
        }
    }

    debounceAutoComplete() {
        if (this._autoCompleteTimer) clearTimeout(this._autoCompleteTimer);
        this._autoCompleteTimer = setTimeout(() => {
            const pos = this.input.selectionStart;
            if (pos !== this.input.selectionEnd) return; // don't autocomplete on selection
            
            // Only autocomplete at end of line or before whitespace
            const val = this.input.value;
            if (pos < val.length && !/\s/.test(val[pos])) return;

            const prefix = val.slice(0, pos);
            const suffix = val.slice(pos);
            
            // Skip if last char typed was space and line is mostly spaces
            if (prefix.endsWith(" ") || prefix.endsWith("\n")) {
                if (prefix.trim() === "") return;
            }

            this.ghostReqId++;
            this.ghostPos = pos;
            
            if (window.aieverViz && window.aieverViz.socket) {
                window.aieverViz.socket.emit("ai_autocomplete", {
                    prefix, suffix, req_id: this.ghostReqId
                });
            }
        }, 500); // 500ms debounce
    }

    showGhostText(completion, reqId) {
        if (reqId !== this.ghostReqId) return; // Stale request
        if (!completion) return;
        
        this.ghostText = completion;
        this.scheduleRender();
    }

    showInlinePrompt() {
        if (document.getElementById("ai-inline-prompt")) return;
        
        const overlay = document.createElement("div");
        overlay.id = "ai-inline-prompt";
        overlay.className = "ai-inline-prompt-overlay";
        
        const pos = this.input.selectionStart;
        const line = this.currentLine();
        
        overlay.innerHTML = `
            <div class="ai-inline-prompt-header">
                <span>🤖 AI Generate</span>
            </div>
            <textarea class="ai-inline-prompt-input" id="ai-inline-input" placeholder="E.g. Write a quicksort function"></textarea>
            <div class="ai-inline-prompt-actions">
                <button class="ai-inline-prompt-btn cancel" id="ai-inline-cancel">Cancel</button>
                <button class="ai-inline-prompt-btn" id="ai-inline-submit">Generate</button>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        const input = document.getElementById("ai-inline-input");
        const cancelBtn = document.getElementById("ai-inline-cancel");
        const submitBtn = document.getElementById("ai-inline-submit");
        
        input.focus();
        
        const close = () => {
            if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
            this.input.focus();
        };
        
        cancelBtn.addEventListener("click", close);
        
        input.addEventListener("keydown", (e) => {
            if (e.key === "Escape") { close(); }
            if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); }
        });
        
        const submit = () => {
            const prompt = input.value.trim();
            if (!prompt) return;
            
            submitBtn.textContent = "Generating...";
            submitBtn.disabled = true;
            input.disabled = true;
            
            const reqId = Date.now().toString();
            this.inlineGenReqId = reqId;
            this.inlineGenStartPos = this.input.selectionStart;
            this.inlineGenEndPos = this.input.selectionEnd;
            this.inlineGenBuffer = "";
            
            if (window.aieverViz && window.aieverViz.socket) {
                window.aieverViz.socket.emit("ai_generate_code", {
                    prompt: prompt,
                    context: {
                        code: this.getValue(),
                        line: line
                    },
                    req_id: reqId
                });
            }
        };
        
        submitBtn.addEventListener("click", submit);
    }
    
    handleInlineGenChunk(chunk, reqId) {
        if (reqId !== this.inlineGenReqId) return;
        
        this.inlineGenBuffer += chunk;
        
        // Overwrite the current selection with the buffer
        this.input.focus();
        this.input.setSelectionRange(this.inlineGenStartPos, this.inlineGenEndPos);
        
        let done = false;
        try { done = document.execCommand("insertText", false, this.inlineGenBuffer); } catch (_) {}
        if (!done) {
            const v = this.input.value;
            this.input.value = v.slice(0, this.inlineGenStartPos) + this.inlineGenBuffer + v.slice(this.inlineGenEndPos);
        }
        
        this.inlineGenEndPos = this.inlineGenStartPos + this.inlineGenBuffer.length;
        this.setCaret(this.inlineGenEndPos);
        this.scheduleRender();
    }
    
    handleInlineGenCompleted(reqId) {
        if (reqId !== this.inlineGenReqId) return;
        
        const overlay = document.getElementById("ai-inline-prompt");
        if (overlay) overlay.parentNode.removeChild(overlay);
        this.input.focus();
    }
}

/* Expose a single editor instance for visualizer.js */
window.addEventListener("DOMContentLoaded", () => {
    window.aieverEditor = new CodeEditor();

    // Code handoff from the Sessions page
    try {
        const pending = localStorage.getItem("aiever-load-code");
        if (pending) {
            window.aieverEditor.setValue(pending);
            localStorage.removeItem("aiever-load-code");
        }
    } catch (_) {}
});
