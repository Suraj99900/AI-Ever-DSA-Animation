/**
 * AI-EVER Code Visualizer — animated data-structure visualization.
 *
 * FIX: cells and pointer markers live in ONE shared track that
 * scrolls together, and every pointer owns a permanent lane —
 * markers can no longer overlap, drift, or get clipped.
 *
 * Draws each step's variables as real graphics:
 *   - Lists/tuples → array cells with index labels
 *   - Pointer ints → labeled ▲ markers sliding between indices
 *   - Changed cells → pulse animation (sorting swaps light up)
 *   - Strings → character cells · Dicts → key:value rows · Sets → badges
 *
 * Pure DOM + CSS transitions. Zero dependencies, fully offline.
 */
"use strict";

class DataViz {
    static CELL_W = 44;   // 40px cell + 4px gap — must match CSS
    static LANE_H = 20;
    static POINTER_COLORS = ["var(--accent)", "var(--green)", "var(--orange)", "var(--purple)", "var(--red)", "var(--cyan)"];
    static MAX_STRING_CELLS = 24;

    constructor() {
        this.el = document.getElementById("viz-panel");
        this.reset();
    }

    reset() {
        this.el.innerHTML =
            '<div class="placeholder">Arrays, pointers &amp; dicts animate here during execution</div>';
        this.prevArrays = {};
        this.pointerColor = {};
        this.lanes = {};      // array name -> {pointer name -> lane index}
        this.blocks = {};
        this._cleared = true;
    }

    static esc(s) {
        return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    /* ------------------------------------------------------------------ */
    update(values) {
        const arrays = [], dicts = [], sets = [], strings = [], ints = [];

        for (const [name, v] of Object.entries(values || {})) {
            if (Array.isArray(v)) arrays.push([name, v]);
            else if (v && typeof v === "object" && Array.isArray(v.__set__)) sets.push([name, v.__set__]);
            else if (v && typeof v === "object") dicts.push([name, v]);
            else if (typeof v === "string" && v.length > 1 && v.length <= DataViz.MAX_STRING_CELLS) strings.push([name, v]);
            else if (typeof v === "number" && Number.isInteger(v)) ints.push([name, v]);
        }

        if (!arrays.length && !dicts.length && !sets.length && !strings.length) {
            if (!this._cleared) this.reset();
            return;
        }

        if (this._cleared) {
            this.el.innerHTML = "";
            this._cleared = false;
            this.blocks = {};
        }

        const seen = new Set();

        arrays.forEach(([name, items]) => {
            const pointers = ints.filter(([, idx]) => idx >= -1 && idx <= items.length);
            this.renderArray(name, items, pointers);
            seen.add(name);
        });

        strings.forEach(([name, s]) => {
            this.renderArray(name, s.split(""), [], true);
            seen.add(name);
        });

        dicts.forEach(([name, obj]) => { this.renderDict(name, obj); seen.add(name); });
        sets.forEach(([name, items]) => { this.renderSet(name, items); seen.add(name); });

        for (const name of Object.keys(this.blocks)) {
            if (!seen.has(name)) {
                this.blocks[name].remove();
                delete this.blocks[name];
                delete this.prevArrays[name];
                delete this.lanes[name];
            }
        }
    }

    /* ------------------------------------------------------------------ */
    block(name, kind) {
        let b = this.blocks[name];
        if (!b || b.dataset.kind !== kind) {
            if (b) b.remove();
            b = document.createElement("div");
            b.className = "viz-block";
            b.dataset.kind = kind;
            b.innerHTML =
                `<div class="viz-name">${DataViz.esc(name)}</div><div class="viz-body"></div>`;
            this.el.appendChild(b);
            this.blocks[name] = b;
        }
        return b.querySelector(".viz-body");
    }

    /* ---------------- Arrays + sliding pointers (shared track) -------- */
    renderArray(name, items, pointers, isString = false) {
        const body = this.block(name, "array");
        const prev = this.prevArrays[name];

        // ----- structure: one scrollable track holds cells AND pointers -----
        let track = body.querySelector(".viz-track");
        if (!track || track.querySelector(".viz-cells").childElementCount !== items.length) {
            body.innerHTML =
                `<div class="viz-scroll"><div class="viz-track">
                    <div class="viz-cells">${items.map((v, i) =>
                        `<div class="viz-cell${isString ? " str" : ""}" data-i="${i}">
                            <span class="viz-val"></span><span class="viz-idx">${i}</span>
                        </div>`).join("")}
                    </div>
                    <div class="viz-pointers"></div>
                </div></div>`;
            track = body.querySelector(".viz-track");
        }

        // ----- cell values + change pulses -----
        const cells = track.querySelector(".viz-cells");
        items.forEach((v, i) => {
            const cell = cells.children[i];
            const valEl = cell.firstElementChild;
            const text = v === null ? "·" : String(v);
            if (valEl.textContent !== text) {
                valEl.textContent = text;
                if (prev && prev[i] !== undefined && String(prev[i]) !== text) {
                    cell.classList.remove("changed");
                    void cell.offsetWidth;
                    cell.classList.add("changed");
                }
            }
        });
        this.prevArrays[name] = items.slice();

        // ----- pointers: permanent lane per name, slide via CSS left -----
        const laneMap = this.lanes[name] || (this.lanes[name] = {});
        const laneArea = track.querySelector(".viz-pointers");
        const active = new Set();

        pointers.forEach(([pname, idx]) => {
            active.add(pname);
            if (!(pname in laneMap)) laneMap[pname] = Object.keys(laneMap).length;
            if (!(pname in this.pointerColor)) {
                this.pointerColor[pname] =
                    DataViz.POINTER_COLORS[Object.keys(this.pointerColor).length % DataViz.POINTER_COLORS.length];
            }

            let marker = laneArea.querySelector(`[data-ptr="${CSS.escape(pname)}"]`);
            if (!marker) {
                marker = document.createElement("div");
                marker.className = "viz-pointer";
                marker.dataset.ptr = pname;
                marker.innerHTML = `<span class="viz-ptr-arrow">▲</span><span class="viz-ptr-name"></span>`;
                laneArea.appendChild(marker);
            }
            const clamped = Math.max(-1, Math.min(idx, items.length));
            marker.style.color = this.pointerColor[pname];
            marker.style.left = `${clamped * DataViz.CELL_W + 8}px`;
            marker.style.top = `${laneMap[pname] * DataViz.LANE_H}px`;
            marker.querySelector(".viz-ptr-name").textContent = `${pname}=${idx}`;
        });

        laneArea.querySelectorAll(".viz-pointer").forEach((m) => {
            if (!active.has(m.dataset.ptr)) m.remove();
        });

        const laneCount = Math.max(1, Object.keys(laneMap).length);
        laneArea.style.height = `${laneCount * DataViz.LANE_H + 2}px`;
        // Track width covers all cells so pointers scroll WITH the cells
        track.style.minWidth = `${items.length * DataViz.CELL_W}px`;
    }

    /* ---------------- Dicts ---------------- */
    renderDict(name, obj) {
        const body = this.block(name, "dict");
        const rows = Object.entries(obj).map(([k, v]) =>
            `<div class="viz-kv"><span class="viz-k">${DataViz.esc(k)}</span><span class="viz-v">${DataViz.esc(v === null ? "…" : JSON.stringify(v))}</span></div>`
        );
        const html = `<div class="viz-dict">${rows.join("") || '<span class="viz-empty">{ }</span>'}</div>`;
        if (body.innerHTML !== html) body.innerHTML = html;
    }

    /* ---------------- Sets ---------------- */
    renderSet(name, items) {
        const body = this.block(name, "set");
        const html = `<div class="viz-set">${
            items.map((v) => `<span class="viz-badge">${DataViz.esc(v)}</span>`).join("") ||
            '<span class="viz-empty">∅</span>'
        }</div>`;
        if (body.innerHTML !== html) body.innerHTML = html;
    }
}

window.AIEVERDataViz = DataViz;
