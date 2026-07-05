"""
AI-EVER Code Visualizer — application entry point.

Blueprint-based Flask application with Flask-SocketIO.
Phase 1: UI shell, navigation, and VSCode-like editor.
Phase 2+: tracing engine, animations, memory panel, etc.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from flask import Blueprint, Flask, Response, jsonify, render_template, request
from flask_socketio import SocketIO

from config import BaseConfig, get_config

from visualizer.analysis.ast_builder import build_ast
from visualizer.executor import CodeExecutor
from visualizer.analysis.flowchart import build_flow
from visualizer.analysis.cfg_builder import build_cfg
from visualizer.analysis.dfg_builder import build_dfg
from visualizer.analysis.call_graph import build_call_graph
from visualizer.analysis.dependency_graph import build_dependency_graph
from visualizer.analysis.import_graph import build_import_graph
from visualizer.analysis.metrics import calculate_metrics
from visualizer.analysis.complexity import analyze_complexity
from visualizer.analysis.class_diagram import build_class_diagram
from visualizer.analysis.object_graph import build_object_graph
from visualizer.algorithms.detector import detect_algorithm
from visualizer.analysis.variable_tracker import analyze_variables
from visualizer.tutor.engine import TutorEngine
from visualizer.tutor.copilot import CopilotEngine

tutor_engine = TutorEngine()
copilot_engine = CopilotEngine()

# ---------------------------------------------------------------------------
# SocketIO instance (initialised inside the app factory)
# ---------------------------------------------------------------------------
socketio: SocketIO = SocketIO()

# ---------------------------------------------------------------------------
# Main blueprint — pages
# ---------------------------------------------------------------------------
main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index() -> str:
    """Render the main visualizer workspace (editor + panels)."""
    return render_template("index.html")


@main_bp.route("/flowchart")
def flowchart() -> str:
    """Render the automatic flowchart page."""
    return render_template("flowchart.html")


@main_bp.route("/ast")
def ast_page() -> str:
    """Render the AST viewer page."""
    return render_template("ast.html")


@main_bp.route("/sessions")
def sessions() -> str:
    """Render the saved sessions page."""
    return render_template("sessions.html")


@main_bp.route("/about")
def about() -> str:
    """Render the about page."""
    return render_template("about.html")


# ---------------------------------------------------------------------------
# API blueprint — JSON endpoints (execution endpoints arrive in Phase 2)
# ---------------------------------------------------------------------------
api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/health")
def health() -> Response:
    """Simple health check used by the frontend status indicator."""
    return jsonify(
        status="ok",
        app=BaseConfig.APP_NAME,
        version=BaseConfig.APP_VERSION,
    )


@api_bp.route("/speeds")
def speeds() -> Response:
    """Expose available playback speeds to the frontend."""
    return jsonify(speeds=list(BaseConfig.PLAYBACK_SPEEDS))


@api_bp.route("/run", methods=["POST"])
def run_code() -> Response | tuple:
    """Trace user code with sys.settrace() and return the step timeline."""
    payload = request.get_json(silent=True) or {}
    code: str = payload.get("code", "")

    if not code.strip():
        return jsonify(ok=False, error={"type": "EmptyCode", "message": "No code provided.", "line": 1}), 400
    if len(code.encode("utf-8")) > BaseConfig.MAX_CODE_SIZE_BYTES:
        return jsonify(ok=False, error={"type": "TooLarge", "message": "Code exceeds size limit.", "line": 1}), 413

    executor = CodeExecutor(
        max_steps=3000,
        timeout_sec=BaseConfig.EXECUTION_TIMEOUT_SEC,
    )
    result = executor.run(code)

    # Friendly hint when the pasted code is clearly not Python
    if not result["ok"] and result.get("error", {}).get("type") == "SyntaxError":
        markers = ("console.log", "#include", "public static void", "func main(", "<?php", "System.out")
        if any(m in code for m in markers):
            result["error"]["message"] += (
                " — this looks like non-Python code. AI-EVER executes Python offline; "
                "other languages would need their own runtimes."
            )
    return jsonify(result)


@api_bp.route("/ast", methods=["POST"])
def ast_api() -> Response:
    """Parse code → AST tree JSON for the AST viewer."""
    code: str = (request.get_json(silent=True) or {}).get("code", "")
    return jsonify(build_ast(code))


@api_bp.route("/flowchart", methods=["POST"])
def flowchart_api() -> Response:
    """Parse code → flowchart structure JSON."""
    code: str = (request.get_json(silent=True) or {}).get("code", "")
    return jsonify(build_flow(code))

@api_bp.route("/cfg", methods=["POST"])
def cfg_api() -> Response:
    code: str = (request.get_json(silent=True) or {}).get("code", "")
    return jsonify(build_cfg(code))

@api_bp.route("/dfg", methods=["POST"])
def dfg_api() -> Response:
    code: str = (request.get_json(silent=True) or {}).get("code", "")
    return jsonify(build_dfg(code))

@api_bp.route("/callgraph", methods=["POST"])
def callgraph_api() -> Response:
    code: str = (request.get_json(silent=True) or {}).get("code", "")
    return jsonify(build_call_graph(code))

@api_bp.route("/dependency", methods=["POST"])
def dependency_api() -> Response:
    code: str = (request.get_json(silent=True) or {}).get("code", "")
    return jsonify(build_dependency_graph(code))

@api_bp.route("/metrics", methods=["POST"])
def metrics_api() -> Response:
    code: str = (request.get_json(silent=True) or {}).get("code", "")
    return jsonify(calculate_metrics(code))

@api_bp.route("/complexity", methods=["POST"])
def complexity_api() -> Response:
    code: str = (request.get_json(silent=True) or {}).get("code", "")
    return jsonify(analyze_complexity(code))

@api_bp.route("/variables", methods=["POST"])
def variables_api() -> Response:
    code: str = (request.get_json(silent=True) or {}).get("code", "")
    return jsonify(analyze_variables(code))

@api_bp.route("/classdiagram", methods=["POST"])
def classdiagram_api() -> Response:
    code: str = (request.get_json(silent=True) or {}).get("code", "")
    return jsonify(build_class_diagram(code))

@api_bp.route("/objectgraph", methods=["POST"])
def objectgraph_api() -> Response:
    code: str = (request.get_json(silent=True) or {}).get("code", "")
    return jsonify(build_object_graph(code))

@api_bp.route("/analyze", methods=["POST"])
def analyze_all_api() -> Response:
    """Run all analyses at once and return a comprehensive report."""
    code: str = (request.get_json(silent=True) or {}).get("code", "")
    socketio.emit("analysis_started", {"status": "starting"})
    
    report = {
        "ok": True,
        "ast": build_ast(code),
        "cfg": build_cfg(code),
        "dfg": build_dfg(code),
        "call_graph": build_call_graph(code),
        "dependency_graph": build_dependency_graph(code),
        "metrics": calculate_metrics(code),
        "complexity": analyze_complexity(code),
        "variables": analyze_variables(code),
        "class_diagram": build_class_diagram(code),
        "object_graph": build_object_graph(code),
    }
    
    socketio.emit("analysis_finished", {"status": "complete"})
    return jsonify(report)
# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
def configure_logging(app: Flask) -> None:
    """Attach a rotating file handler so all requests/errors are logged."""
    log_path = app.config["LOG_FOLDER"] / "aiever.log"
    handler = RotatingFileHandler(
        log_path, maxBytes=1_000_000, backupCount=5, encoding="utf-8"
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application."""
    config_cls = get_config(config_name)
    config_cls.ensure_directories()

    app = Flask(__name__)
    app.config.from_object(config_cls)
    # Keep Path objects accessible in config
    app.config["LOG_FOLDER"] = config_cls.LOG_FOLDER

    configure_logging(app)

    # Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    # SocketIO (threading mode = fully offline, no extra server needed)
    socketio.init_app(
        app,
        async_mode=config_cls.SOCKETIO_ASYNC_MODE,
        cors_allowed_origins="*",
    )

    register_socket_events()
    app.logger.info("%s started (Phase 1)", config_cls.APP_NAME)
    return app


# ---------------------------------------------------------------------------
# Socket events — Phase 1 stubs (real tracer wiring lands in Phase 2)
# ---------------------------------------------------------------------------
def register_socket_events() -> None:
    """Register SocketIO event handlers."""

    @socketio.on("connect")
    def on_connect() -> None:
        socketio.emit("server_status", {"status": "connected", "phase": 1})

    @socketio.on("run_code")
    def on_run_code(data: dict) -> None:
        """Phase 1 stub — acknowledges the run request.

        Phase 2 will parse + trace the code and stream execution steps.
        """
        code: str = (data or {}).get("code", "")
        socketio.emit(
            "run_ack",
            {
                "received_chars": len(code),
                "message": "Execution engine arrives in Phase 2.",
            },
        )

    @socketio.on("ai_chat")
    def on_ai_chat(data: dict) -> None:
        """Handle AI Tutor chat streaming."""
        user_msg = data.get("message", "")
        context = data.get("context", {})
        
        socketio.emit("ai_started", {})
        
        try:
            for chunk in tutor_engine.stream_chat(user_msg, context):
                socketio.emit("ai_stream_chunk", {"chunk": chunk})
        except Exception as e:
            socketio.emit("ai_stream_chunk", {"chunk": f"\n[Error: {str(e)}]"})
            
        socketio.emit("ai_completed", {})

    @socketio.on("ai_autocomplete")
    def on_ai_autocomplete(data: dict) -> None:
        """Handle inline AI code completion."""
        prefix = data.get("prefix", "")
        suffix = data.get("suffix", "")
        req_id = data.get("req_id", "")
        
        try:
            completion = copilot_engine.generate_completion(prefix, suffix)
            socketio.emit("ai_autocomplete_result", {"req_id": req_id, "completion": completion})
        except Exception as e:
            pass # Fail silently for autocomplete so we don't disrupt typing

    @socketio.on("ai_generate_code")
    def on_ai_generate_code(data: dict) -> None:
        """Handle inline code generation prompt streaming."""
        prompt = data.get("prompt", "")
        context = data.get("context", {})
        req_id = data.get("req_id", "")
        
        socketio.emit("ai_gen_started", {"req_id": req_id})
        
        try:
            for chunk in copilot_engine.generate_inline_code(prompt, context):
                socketio.emit("ai_gen_chunk", {"req_id": req_id, "chunk": chunk})
        except Exception as e:
            socketio.emit("ai_gen_chunk", {"req_id": req_id, "chunk": f"\n# Error: {str(e)}"})
            
        socketio.emit("ai_gen_completed", {"req_id": req_id})


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
@api_bp.route("/algorithm/detect", methods=["POST"])
def api_algorithm_detect():
    data = request.get_json()
    code = data.get("code", "")
    if not code:
        return jsonify({"error": "No code provided"}), 400
    try:
        detection = detect_algorithm(code)
        return jsonify({"ok": True, "detection": detection})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------------------------
# Module-level app instance — required by gunicorn (gunicorn app:app)
# ---------------------------------------------------------------------------
app = create_app()

if __name__ == "__main__":
    socketio.run(
        app,
        host="127.0.0.1",
        port=5000,
        debug=app.config["DEBUG"],
        allow_unsafe_werkzeug=True,  # local dev server; use gunicorn in prod
    )

