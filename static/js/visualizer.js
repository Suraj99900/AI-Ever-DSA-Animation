/**
 * AI-EVER Code Visualizer — playback engine + workspace UI.
 *
 * - Debugger-style playback of the traced timeline (Python)
 * - JavaScript execution in a sandboxed Web Worker (output console)
 * - LeetCode-style tabs with floating, draggable, resizable windows
 * - Resizable editor/sidebar splitter (persisted)
 * - Explain tab: per-line explanation + time/space complexity
 */
"use strict";

/* ==================================================================
 * Tab manager — with floating window support
 * ================================================================== */
/* Tabs class removed for permanent grid layout */

/* ==================================================================
 * Console panel
 * ================================================================== */
class ConsolePanel {
    constructor() {
        this.el = document.getElementById("console-output");
        this.progEl = null;
        this.onWrite = null;
        document.getElementById("btn-clear-console")
            ?.addEventListener("click", () => this.clear());
    }

    clear() {
        this.el.innerHTML = "";
        this.progEl = null;
    }

    write(text, type = "stdout") {
        const div = document.createElement("div");
        div.className = `line ${type}`;
        div.textContent = text;
        this.el.appendChild(div);
        this.scrollDown();
        this.onWrite?.(type);
    }

    setProgramOutput(text) {
        if (!this.progEl) {
            this.progEl = document.createElement("div");
            this.progEl.className = "line prog-out";
            this.el.appendChild(this.progEl);
        }
        if (this.progEl.textContent !== text) {
            this.progEl.textContent = text;
            this.scrollDown();
            if (text) this.onWrite?.("stdout");
        }
    }

    scrollDown() { this.el.scrollTop = this.el.scrollHeight; }
}

/* ==================================================================
 * Memory panel
 * ================================================================== */
class MemoryPanel {
    constructor() {
        this.el = document.getElementById("memory-panel");
        this.prev = {};
        this.prevFunc = null;
    }

    reset() {
        this.el.innerHTML = '<div class="placeholder">Run code to watch variables live</div>';
        this.prev = {};
        this.prevFunc = null;
    }

    update(vars, funcName) {
        const scope = funcName === "<module>" ? "Global scope" : `${funcName}() — local scope`;
        const scopeChanged = funcName !== this.prevFunc;

        const rows = Object.entries(vars).map(([name, val]) => {
            const changed = !scopeChanged && this.prev[name] !== undefined && this.prev[name] !== val;
            const isNew = !scopeChanged && this.prev[name] === undefined;
            return `<div class="var-row${changed || isNew ? " changed" : ""}">
                <span class="var-name">${esc(name)}</span>
                <span class="var-eq">=</span>
                <span class="var-val">${esc(val)}</span>
            </div>`;
        });

        this.el.innerHTML =
            `<div class="scope-label">${esc(scope)}</div>` +
            (rows.length ? rows.join("") : '<div class="placeholder">No variables yet</div>');

        this.prev = { ...vars };
        this.prevFunc = funcName;
    }
}

/* ==================================================================
 * Call stack panel
 * ================================================================== */
class StackPanel {
    constructor() {
        this.el = document.getElementById("stack-panel");
        this.prevDepth = 0;
    }

    reset() {
        this.el.innerHTML = '<div class="placeholder">Call stack appears during execution</div>';
        this.prevDepth = 0;
    }

    update(stack, retValue) {
        const pushed = stack.length > this.prevDepth;
        const frames = stack.map((fr, i) => {
            const isTop = i === stack.length - 1;
            const cls = `stack-frame${isTop ? " top" : ""}${isTop && pushed ? " pushed" : ""}`;
            const ret = isTop && retValue !== undefined
                ? `<span class="ret-badge">→ ${esc(retValue)}</span>` : "";
            return `<div class="${cls}">
                <span>${esc(fr.func)}${ret}</span>
                <span class="frame-line">line ${fr.line}</span>
            </div>`;
        });

        this.el.innerHTML =
            `<div class="stack-frames">${frames.join('<div class="stack-arrow">↓</div>')}</div>`;
        this.prevDepth = stack.length;
    }
}

/* ==================================================================
 * Explain panel — per-line explanation + complexity analysis
 * ================================================================== */
class ExplainPanel {
    constructor() {
        this.el = document.getElementById("explain-panel");
    }

    reset() {
        this.el.innerHTML =
            '<div class="placeholder">Run code to see line-by-line explanations and complexity analysis</div>';
    }

    setAnalysis(analysis, callGraph) {
        this.analysis = analysis;
        this.callGraph = callGraph;
        this.renderShell();
    }

    renderShell() {
        const a = this.analysis || {};
        const cg = this.callGraph || { edges: [] };
        const edges = cg.edges.slice(0, 6).map((e) =>
            `<div class="cg-edge">${esc(e.from)} → ${esc(e.to)} <span class="cg-count">×${e.count}</span></div>`
        ).join("");

        this.el.innerHTML = `
            <div class="cx-summary">
                <div class="cx-card"><div class="cx-label">Time</div><div class="cx-big">${esc(a.time || "—")}</div></div>
                <div class="cx-card"><div class="cx-label">Space</div><div class="cx-big">${esc(a.space || "—")}</div></div>
            </div>
            <div class="cx-note">${esc(a.note || "")}</div>
            ${a.recursive?.length ? `<div class="cx-note">↻ Recursive: ${esc(a.recursive.join(", "))}</div>` : ""}
            ${edges ? `<div class="scope-label" style="margin-top:10px;">Call graph</div>${edges}` : ""}
            <div class="scope-label" style="margin-top:12px;">Current line</div>
            <div id="explain-current" class="explain-current">
                <div class="placeholder">Step through the code…</div>
            </div>`;
    }

    updateStep(step, sourceLine, pseudoLine) {
        const box = document.getElementById("explain-current");
        if (!box) return;

        let pseudoHtml = "";
        if (pseudoLine) {
            pseudoHtml = `<div class="explain-code" style="color: #61afef;"><i>pseudocode:</i> <code>${esc(pseudoLine.trim())}</code></div>`;
        }

        box.innerHTML = `
            <div class="explain-code">ln ${step.line}: <code>${esc((sourceLine || "").trim())}</code></div>
            ${pseudoHtml}
            <div class="explain-text" style="color: #98c379;">${esc(step.explain || "Executing this line.")}</div>
            ${step.cx ? `<span class="cx-chip">${esc(step.cx)}</span>` : ""}`;
    }
}

/* ==================================================================
 * Sandboxed JavaScript runner (Web Worker, offline)
 * ================================================================== */
class JSRunner {
    static WORKER_SRC = `
        const send = (t, d) => postMessage({ t, d });
        self.console = {
            log:   (...a) => send("log",  a.map(String).join(" ")),
            error: (...a) => send("err",  a.map(String).join(" ")),
            warn:  (...a) => send("warn", a.map(String).join(" ")),
            info:  (...a) => send("log",  a.map(String).join(" ")),
        };
        onmessage = (e) => {
            try {
                const result = new Function(e.data)();
                if (result !== undefined) send("log", String(result));
                send("done");
            } catch (err) {
                send("err", String(err));
                send("done");
            }
        };`;

    run(code, consolePanel, onDone) {
        const blob = new Blob([JSRunner.WORKER_SRC], { type: "application/javascript" });
        const worker = new Worker(URL.createObjectURL(blob));
        const kill = setTimeout(() => {
            worker.terminate();
            consolePanel.write("⚠ JavaScript timed out (5s) — possible infinite loop.", "warn");
            onDone();
        }, 5000);

        worker.onmessage = (e) => {
            const { t, d } = e.data;
            if (t === "log") consolePanel.write(d, "stdout");
            else if (t === "warn") consolePanel.write(d, "warn");
            else if (t === "err") consolePanel.write(`✖ ${d}`, "error");
            else if (t === "done") {
                clearTimeout(kill);
                worker.terminate();
                onDone();
            }
        };
        worker.postMessage(code);
    }
}

/* ==================================================================
 * Resizable splitter between editor and sidebar
 * ================================================================== */
class Splitter {
    constructor() {
        this.ws = document.getElementById("workspace");
        this.leftPane = document.getElementById("left-pane");
        this.vSplitter = document.getElementById("v-splitter");
        this.hSplitter = document.getElementById("h-splitter");

        // AI Tutor UI Elements
        this.tutorPanel = document.getElementById("ai-tutor-panel");
        this.tutorSplitter = document.getElementById("tutor-splitter");
        this.btnToggleTutor = document.getElementById("toggle-tutor-btn");
        this.btnCloseTutor = document.getElementById("close-tutor-btn");
        this.tutorWidth = 300; // Default width

        if (this.ws && this.vSplitter) {
            this.initV();
        }
        if (this.leftPane && this.hSplitter) {
            this.initH();
        }

        // AI Tutor Listeners
        if (this.btnToggleTutor) {
            this.btnToggleTutor.addEventListener("click", () => this.toggleTutorPanel());
        }
        if (this.btnCloseTutor) {
            this.btnCloseTutor.addEventListener("click", () => this.toggleTutorPanel(false));
        }

        this.initDashboardSplitters();
    }

    toggleTutorPanel(forceState = null) {
            if (!this.tutorPanel) return;
            const isActive = this.tutorPanel.classList.contains("active");
            const nextState = forceState !== null ? forceState : !isActive;

            const ws = document.getElementById("workspace");
            if (nextState) {
                this.tutorPanel.classList.add("active");
                if (this.tutorSplitter) this.tutorSplitter.style.display = "flex";
                ws.style.setProperty("--tutor-width", `${this.tutorWidth}px`);
            } else {
                this.tutorPanel.classList.remove("active");
                if (this.tutorSplitter) this.tutorSplitter.style.display = "none";
                ws.style.setProperty("--tutor-width", `0px`);
            }
        }

        initTutorSplitter() {
            if (!this.tutorSplitter) return;
            this.tutorSplitter.addEventListener("mousedown", (e) => {
                e.preventDefault();
                const ws = document.getElementById("workspace");
                const move = (ev) => {
                    // Width = distance from right edge of window
                    const w = Math.min(
                        Math.max(window.innerWidth - ev.clientX, 200),
                        window.innerWidth * 0.5
                    );
                    this.tutorWidth = w;
                    ws.style.setProperty("--tutor-width", `${w}px`);
                };
                const up = () => {
                    document.removeEventListener("mousemove", move);
                    document.removeEventListener("mouseup", up);
                    document.body.style.cursor = "";
                };
                document.body.style.cursor = "col-resize";
                document.addEventListener("mousemove", move);
                document.addEventListener("mouseup", up);
            });
        }

        initV() {
            try {
                const saved = localStorage.getItem("aiever-v-w");
                if (saved) this.ws.style.setProperty("--right-width", `${saved}px`);
            } catch (_) { }

            this.vSplitter.addEventListener("mousedown", (e) => {
                e.preventDefault();
                const move = (ev) => {
                    const w = Math.min(
                        Math.max(this.ws.getBoundingClientRect().right - ev.clientX, 280),
                        window.innerWidth * 0.7
                    );
                    this.ws.style.setProperty("--right-width", `${w}px`);
                    try { localStorage.setItem("aiever-v-w", String(w)); } catch (_) { }
                };
                const up = () => {
                    document.removeEventListener("mousemove", move);
                    document.removeEventListener("mouseup", up);
                    document.body.style.cursor = "";
                };
                document.body.style.cursor = "col-resize";
                document.addEventListener("mousemove", move);
                document.addEventListener("mouseup", up);
            });
        }

        initH() {
            try {
                const saved = localStorage.getItem("aiever-h-h");
                if (saved) this.leftPane.style.setProperty("--console-height", `${saved}px`);
            } catch (_) { }

            this.hSplitter.addEventListener("mousedown", (e) => {
                e.preventDefault();
                const move = (ev) => {
                    const h = Math.min(
                        Math.max(this.leftPane.getBoundingClientRect().bottom - ev.clientY, 100),
                        this.leftPane.clientHeight * 0.8
                    );
                    this.leftPane.style.setProperty("--console-height", `${h}px`);
                    try { localStorage.setItem("aiever-h-h", String(h)); } catch (_) { }
                };
                const up = () => {
                    document.removeEventListener("mousemove", move);
                    document.removeEventListener("mouseup", up);
                    document.body.style.cursor = "";
                };
                document.body.style.cursor = "row-resize";
                document.addEventListener("mousemove", move);
                document.addEventListener("mouseup", up);
            });
        }

        initDashboardSplitters() {
            const splitters = document.querySelectorAll('.dashboard-splitter');
            splitters.forEach(splitter => {
                splitter.addEventListener('mousedown', (e) => {
                    e.preventDefault();
                    const prev = splitter.previousElementSibling;
                    const next = splitter.nextElementSibling;
                    if (!prev || !next) return;

                    // Turn off flex:1 to allow absolute height control during drag
                    const startPrevHeight = prev.getBoundingClientRect().height;
                    const startNextHeight = next.getBoundingClientRect().height;
                    const startY = e.clientY;

                    prev.style.flex = 'none';
                    next.style.flex = 'none';

                    const move = (ev) => {
                        const delta = ev.clientY - startY;
                        const newPrevHeight = Math.max(startPrevHeight + delta, 50);
                        const newNextHeight = Math.max(startNextHeight - delta, 50);
                        prev.style.height = `${newPrevHeight}px`;
                        next.style.height = `${newNextHeight}px`;
                    };

                    const up = () => {
                        document.removeEventListener('mousemove', move);
                        document.removeEventListener('mouseup', up);
                        document.body.style.cursor = '';
                    };

                    document.body.style.cursor = 'row-resize';
                    document.addEventListener('mousemove', move);
                    document.addEventListener('mouseup', up);
                });
            });
        }
    }

/* ==================================================================
 * Helpers
 * ================================================================== */
function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/* ==================================================================
 * Playback engine
 * ================================================================== */
class Visualizer {
    static SPEEDS = [0.25, 0.5, 1, 2, 5, 10];
    static BASE_DELAY = 700;

    constructor(editor) {
        this.editor = editor;
        this.console = new ConsolePanel();
        this.memory = new MemoryPanel();
        this.stack = new StackPanel();
        this.explain = new ExplainPanel();
        this.dataviz = new window.AIEVERDataViz();
        this.jsRunner = new JSRunner();
        new Splitter();

        // Phase 4 - Visualization Engine
        if (window.AIEVERVisualizationManager) {
            this.vizManager = new window.AIEVERVisualizationManager("viz-panel");
            this.vizManager.registerRenderer("ArrayVisualizer", new window.AIEVERArrayRenderer(document.getElementById("viz-panel")));
            this.vizManager.registerRenderer("GraphVisualizer", new window.AIEVERGraphRenderer(document.getElementById("viz-panel")));
            this.animController = new window.AIEVERAnimationController(this.vizManager);
        }

        this.steps = [];
        this.stdout = "";
        this.error = null;
        this.index = -1;
        this.playing = false;
        this.timer = null;
        this.speed = 1;
        this.sourceLines = [];

        this.btn = {};
        ["run", "pause", "resume", "prev", "next", "restart", "analyze"].forEach((id) => {
            this.btn[id] = document.getElementById(`btn-${id}`);
        });
        this.execStatus = document.getElementById("exec-status");
        this.stepCounter = document.getElementById("step-counter");
        this.langSelect = document.getElementById("lang-select");

        try {
            const savedLang = localStorage.getItem("aiever-lang");
            if (savedLang) this.langSelect.value = savedLang;
        } catch (_) { }
        this.langSelect.addEventListener("change", () => {
            try { localStorage.setItem("aiever-lang", this.langSelect.value); } catch (_) { }
        });

        this.socket = io(); // Initialize Socket.IO connection
        this.initTutorChat();

        this.bind();
        this.console.write("[AI-EVER] Ready. Press ▶ Run or Ctrl+Enter.", "info");
    }

    /* ---------- Controls ---------- */

    bind() {
        this.btn.run.addEventListener("click", () => this.run());
        if (this.btn.analyze) this.btn.analyze.addEventListener("click", () => this.analyze());
        this.btn.pause.addEventListener("click", () => this.pause());
        this.btn.resume.addEventListener("click", () => this.resume());
        this.btn.prev.addEventListener("click", () => this.stepPrev());
        this.btn.next.addEventListener("click", () => this.stepNext());
        this.btn.restart.addEventListener("click", () => this.restart());

        const slider = document.getElementById("speed-slider");
        const label = document.getElementById("speed-label");
        slider.addEventListener("input", () => {
            this.speed = Visualizer.SPEEDS[slider.value];
            label.textContent = `${this.speed}x`;
        });
    }

    initTutorChat() {
        this.tutorInput = document.getElementById("tutor-input");
        this.tutorSendBtn = document.getElementById("tutor-send-btn");
        this.tutorMessages = document.getElementById("tutor-messages");

        if (!this.tutorInput || !this.tutorSendBtn) return;

        const sendMessage = () => {
            const msg = this.tutorInput.value.trim();
            if (!msg) return;

            this.appendChatMessage(msg, "user");
            this.tutorInput.value = "";

            // Gather context
            let code = this.editor.getValue();
            let currentLine = 0;
            let locals = {};
            if (this.index >= 0 && this.index < this.steps.length) {
                const step = this.steps[this.index];
                currentLine = step.line || 0;
                locals = step.locals || {};
            }

            this.socket.emit("ai_chat", {
                message: msg,
                context: {
                    code: code,
                    line: currentLine,
                    locals: locals
                }
            });

            this.currentAiMsgDiv = null;
        };

        this.tutorSendBtn.addEventListener("click", sendMessage);
        this.tutorInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        this.socket.on("ai_started", () => {
            this.currentAiMsgDiv = document.createElement("div");
            this.currentAiMsgDiv.className = "tutor-msg ai";
            this.tutorMessages.appendChild(this.currentAiMsgDiv);
            this.scrollToBottom(this.tutorMessages);
        });

        this.socket.on("ai_stream_chunk", (data) => {
            if (this.currentAiMsgDiv) {
                // Simple append, in real usage we'd parse markdown
                this.currentAiMsgDiv.textContent += data.chunk;
                this.scrollToBottom(this.tutorMessages);
            }
        });

        this.socket.on("ai_completed", () => {
            // Done
        });
        
        // Copilot Events
        this.socket.on("ai_autocomplete_result", (data) => {
            this.editor.showGhostText(data.completion, data.req_id);
        });
        
        this.socket.on("ai_gen_started", (data) => {
            // handled in editor directly if we want to show a spinner
        });
        
        this.socket.on("ai_gen_chunk", (data) => {
            this.editor.handleInlineGenChunk(data.chunk, data.req_id);
        });
        
        this.socket.on("ai_gen_completed", (data) => {
            this.editor.handleInlineGenCompleted(data.req_id);
        });
    }

    appendChatMessage(text, role) {
        const div = document.createElement("div");
        div.className = `tutor-msg ${role}`;
        div.textContent = text;
        this.tutorMessages.appendChild(div);
        this.scrollToBottom(this.tutorMessages);
    }

    scrollToBottom(el) {
        el.scrollTop = el.scrollHeight;
    }

    setButtons(state) {
        const b = this.btn;
        const on = (el, enabled) => { el.disabled = !enabled; };
        on(b.run, state !== "loading");
        on(b.pause, state === "playing");
        on(b.resume, state === "paused");
        on(b.prev, (state === "paused" || state === "done") && this.index > 0);
        on(b.next, (state === "paused" || state === "done") && this.index < this.steps.length - 1);
        on(b.restart, this.steps.length > 0 && state !== "loading");
        if (b.analyze) on(b.analyze, state !== "loading");
    }

    /* ---------- Analyze ---------- */

    async analyze() {
        const code = this.editor.getValue();
        if (!code.trim()) {
            this.console.write("[AI-EVER] Nothing to analyze — the editor is empty.", "warn");
            return;
        }

        this.setButtons("loading");
        this.execStatus.textContent = "⏳ analyzing…";
        this.console.clear();
        this.console.write("[AI-EVER] Running full static analysis...", "info");

        try {
            const res = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code }),
            });
            const data = await res.json();

            this.execStatus.textContent = "✓ analyzed";
            this.setButtons("done");

            if (!data.ok) {
                const e = data.error || {};
                this.console.write(`✖ Syntax Error: ${e.message} (line ${e.line})`, "error");
                return;
            }

            // Print summary
            const m = data.metrics.metrics || {};
            const c = data.complexity.complexity || {};
            const v = data.variables.smells || {};

            let summary = `\n[Analysis Report]\n`;
            summary += `Lines of code: ${m.code_lines} (Total: ${m.total_lines})\n`;
            summary += `Cyclomatic Complexity: ${m.cyclomatic_complexity}\n`;
            summary += `Estimated Time Complexity: ${c.estimated_time_complexity}\n`;

            if (v.unused_variables && v.unused_variables.length > 0) {
                summary += `⚠ Unused variables: ${v.unused_variables.join(", ")}\n`;
            }
            if (v.magic_numbers && v.magic_numbers.length > 0) {
                const nums = v.magic_numbers.map(n => n.value).join(", ");
                summary += `⚠ Magic numbers found: ${nums}\n`;
            }

            this.console.write(summary, "info");

            // Log full data to browser console for Cytoscape/Mermaid debugging
            console.log("Full Analysis Data:", data);

        } catch (err) {
            this.execStatus.textContent = "";
            this.setButtons("done");
            this.console.write("[AI-EVER] Analysis failed. Is app.py running?", "error");
        }
    }

    /* ---------- Run ---------- */

    async run() {
        const code = this.editor.getValue();
        if (!code.trim()) {
            this.console.write("[AI-EVER] Nothing to run — the editor is empty.", "warn");
            return;
        }

        this.stop();
        this.console.clear();
        this.memory.reset();
        this.stack.reset();
        this.explain.reset();
        this.dataviz.reset();
        if (this.vizManager) this.vizManager.reset();
        this.editor.clearExec();
        this.saveSession(code);

        // JavaScript path: sandboxed worker, output-only
        if (this.langSelect.value === "javascript") {
            this.steps = [];
            this.setButtons("loading");
            this.console.write("[AI-EVER] Running JavaScript (output mode — step animation is Python-only).", "info");
            this.jsRunner.run(code, this.console, () => {
                this.execStatus.textContent = "✓ finished";
                this.setButtons("done");
            });
            return;
        }

        this.setButtons("loading");
        this.execStatus.textContent = "⏳ tracing…";

        let data;
        try {
            const res = await fetch("/api/run", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code }),
            });
            data = await res.json();
        } catch (err) {
            this.execStatus.textContent = "";
            this.setButtons("done");
            this.console.write("[AI-EVER] Server unreachable. Is app.py running?", "error");
            return;
        }

        if (!data.ok) {
            this.execStatus.textContent = "";
            this.setButtons("done");
            const e = data.error || {};
            this.console.write(`✖ ${e.type}: ${e.message} (line ${e.line})`, "error");
            if (e.line) this.editor.setExecLine(e.line, true);
            return;
        }

        this.steps = data.steps || [];
        this.stdout = data.stdout || "";
        this.error = data.error;
        this.aborted = data.aborted;
        this.index = -1;
        this.sourceLines = code.split("\n");
        this.pseudocode = data.pseudocode || [];
        this.explain.setAnalysis(data.analysis, data.call_graph);

        // Phase 5: Algorithm Detection
        const algoDiv = document.getElementById("algo-stats");
        if (algoDiv && data.algorithm) {
            algoDiv.style.display = "flex";
            document.getElementById("stat-algo").textContent = `Algo: ${data.algorithm.algorithm} (${Math.round(data.algorithm.confidence * 100)}%)`;
            document.getElementById("stat-swaps").textContent = `Swaps: 0`;
            document.getElementById("stat-comps").textContent = `Comparisons: 0`;
        }

        if (!this.steps.length) {
            this.setButtons("done");
            this.execStatus.textContent = "";
            this.console.write("[AI-EVER] Nothing was executed.", "warn");
            return;
        }

        this.console.write(`[AI-EVER] Traced ${this.steps.length} steps. Playing…`, "info");
        this.editor.setReadOnly(true);
        this.play();
    }

    /* ---------- Playback ---------- */

    play() {
        this.playing = true;
        this.execStatus.textContent = "▶ running";
        this.setButtons("playing");
        this.tick();
    }

    async tick() {
        if (!this.playing) return;
        if (this.index >= this.steps.length - 1) {
            this.finish();
            return;
        }
        await this.stepNext(true);
        if (this.playing) {
            this.timer = setTimeout(() => this.tick(), Visualizer.BASE_DELAY / this.speed);
        }
    }

    pause() {
        this.playing = false;
        clearTimeout(this.timer);
        this.execStatus.textContent = "⏸ paused";
        this.setButtons("paused");
    }

    resume() {
        if (this.index >= this.steps.length - 1) return this.finish();
        this.play();
    }

    async stepNext(auto = false) {
        if (!auto) this.pause();
        if (this.index < this.steps.length - 1) {
            this.index++;
            await this.renderStep();
        }
        if (!auto) this.setButtons("paused");
        if (this.index >= this.steps.length - 1 && !auto) this.finish(true);
    }

    async stepPrev() {
        this.pause();
        if (this.index > 0) {
            this.index--;
            await this.renderStep();
        }
        this.setButtons("paused");
    }

    restart() {
        this.stop();
        this.index = -1;
        this.console.clear();
        this.memory.reset();
        this.stack.reset();
        this.dataviz.reset();
        this.explain.renderShell();
        this.editor.clearExec();
        this.editor.setReadOnly(true);
        this.console.write("[AI-EVER] Replaying…", "info");
        this.play();
    }

    stop() {
        this.playing = false;
        clearTimeout(this.timer);
    }

    finish(silent = false) {
        this.stop();
        this.index = this.steps.length - 1;
        if (!silent) this.renderStep();

        this.editor.setReadOnly(false);
        this.setButtons("done");

        if (this.error) {
            this.execStatus.textContent = "✖ error";
            this.editor.setExecLine(this.error.line, true);
            this.console.write(`✖ ${this.error.traceback}`, "error");
            this.console.write(this.suggestFix(this.error), "warn");
        } else if (this.aborted) {
            this.execStatus.textContent = "⚠ aborted";
            this.console.write(`⚠ ${this.aborted}`, "warn");
        } else {
            this.execStatus.textContent = "✓ finished";
            this.console.write("[AI-EVER] Execution finished.", "info");
        }
    }

    /* ---------- Rendering one step ---------- */

    async renderStep() {
        const step = this.steps[this.index];
        if (!step) return;

        this.editor.setExecLine(step.line);
        this.memory.update(step.locals, step.func);
        this.stack.update(step.stack, step.ret);
        this.dataviz.update(step.values || {});

        const sourceLine = this.sourceLines[step.line - 1];
        const pseudoLine = this.pseudocode[step.line - 1];
        this.explain.updateStep(step, sourceLine, pseudoLine);

        this.console.setProgramOutput(this.stdout.slice(0, step.out));

        // Phase 5: Update Live Stats
        if (step.stats) {
            const swapsEl = document.getElementById("stat-swaps");
            const compsEl = document.getElementById("stat-comps");
            if (swapsEl) swapsEl.textContent = `Swaps: ${step.stats.swaps}`;
            if (compsEl) compsEl.textContent = `Comparisons: ${step.stats.comparisons}`;
        }

        // Phase 4: Play GSAP animations for this step
        if (this.animController) {
            await this.animController.playStep(step);
        }

        const ev = { call: "→ call", line: "line", return: "← return", exception: "⚠ exception" }[step.event] || step.event;
        this.stepCounter.textContent =
            `step ${this.index + 1}/${this.steps.length} · ${ev} · ln ${step.line}`;
    }

    /* ---------- Session save ---------- */

    saveSession(code) {
        try {
            const sessions = JSON.parse(localStorage.getItem("aiever-sessions") || "[]");
            sessions.unshift({
                ts: Date.now(),
                code,
                lines: code.split("\n").length,
                preview: (code.split("\n").find((l) => l.trim() && !l.trim().startsWith("#") && !l.trim().startsWith("//")) || "").slice(0, 60),
            });
            localStorage.setItem("aiever-sessions", JSON.stringify(sessions.slice(0, 20)));
        } catch (_) { }
    }

    /* ---------- Error hints ---------- */

    suggestFix(err) {
        const hints = {
            NameError: "Hint: a variable or function is used before it is defined. Check spelling.",
            TypeError: "Hint: an operation got a value of the wrong type. Check your arguments.",
            IndexError: "Hint: a list index is out of range. Check loop bounds and len().",
            KeyError: "Hint: that dictionary key does not exist. Use .get() or check membership.",
            ZeroDivisionError: "Hint: a divisor is 0. Guard the division with a condition.",
            ValueError: "Hint: a value has the right type but an invalid content.",
            AttributeError: "Hint: that object has no such attribute/method. Check its type.",
            RecursionError: "Hint: missing or unreachable base case in the recursion.",
            TimeoutError: "Hint: possible infinite loop — check your while condition.",
        };
        return hints[err.type] || "Hint: read the traceback above — it points to the failing line.";
    }
}

/* ==================================================================
 * Boot
 * ================================================================== */
window.addEventListener("DOMContentLoaded", () => {
    if (window.aieverEditor) {
        window.aieverViz = new Visualizer(window.aieverEditor);
    }
});
