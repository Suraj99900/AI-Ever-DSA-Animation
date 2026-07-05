# ⬡ AI-EVER Code Visualizer

An **offline**, debugger-grade Python execution visualizer with educational animations.
Paste Python code → parse → execute line by line → watch every step animate.

## Quick start

```bash
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**

## Project structure

```
Code UI/
├── app.py              # Flask app factory + blueprints + SocketIO
├── config.py           # Environment-aware configuration
├── requirements.txt
├── static/
│   ├── css/            # theme.css (dark/light), editor.css
│   ├── js/             # editor.js (VSCode-like editor), main.js
│   ├── animation/      # animation assets (Phase 2)
│   └── vendor/         # local JS libraries (Phase 2 — no CDN, fully offline)
├── templates/          # base.html, index.html, about.html
├── visualizer/         # parser, tracer, memory, animation, ast_builder,
│                       # flowchart, graph_builder, executor (Phase 2)
├── uploads/  logs/  database/
```

## Phase status

- **Phase 1 (done):** UI shell, navigation, dark/light themes, offline VSCode-like
  editor (syntax highlighting, line numbers, auto-indent, toolbar, console).
- **Phase 2 (next):** `sys.settrace()` execution engine, step streaming over
  SocketIO, memory panel, call stack, line-by-line animations.

## Editor shortcuts

| Key | Action |
|---|---|
| `Ctrl+Enter` | Run |
| `Tab` | Insert 4 spaces |
| `Enter` | Auto-indent (extra level after `:`) |
