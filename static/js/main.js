/**
 * AI-EVER Code Visualizer — global app script.
 * Theme switching, nav highlighting, server health indicator. Fully offline.
 */
"use strict";

const AIEVER = {
    /** Apply and persist theme ("dark" | "light"). */
    setTheme(theme) {
        document.documentElement.setAttribute("data-theme", theme);
        try { localStorage.setItem("aiever-theme", theme); } catch (_) { /* private mode */ }
        const sel = document.getElementById("theme-selector");
        if (sel) sel.value = theme;
    },

    /** Restore saved theme on load. */
    initTheme() {
        let saved = "dark";
        try { saved = localStorage.getItem("aiever-theme") || "dark"; } catch (_) {}
        this.setTheme(saved);
        const sel = document.getElementById("theme-selector");
        if (sel) sel.addEventListener("change", (e) => this.setTheme(e.target.value));
    },

    /** Highlight the nav link matching the current page. */
    initActiveNav() {
        const path = window.location.pathname;
        document.querySelectorAll(".nav-link[href]").forEach((link) => {
            link.classList.toggle("active", link.getAttribute("href") === path);
        });
    },

    /** Ping /api/health and light up the status dot. */
    async initHealthCheck() {
        const dot = document.getElementById("server-status");
        if (!dot) return;
        try {
            const res = await fetch("/api/health");
            if (res.ok) {
                dot.classList.add("online");
                dot.title = "Server: online";
            }
        } catch (_) {
            dot.title = "Server: offline";
        }
    },
};

document.addEventListener("DOMContentLoaded", () => {
    AIEVER.initTheme();
    AIEVER.initActiveNav();
    AIEVER.initHealthCheck();
});
