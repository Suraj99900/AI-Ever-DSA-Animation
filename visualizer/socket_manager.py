# // visualizer/socket_manager.py
"""
Singleton wrapper around the Flask‑SocketIO instance.
Allows emitting events from any thread (e.g., the tracer thread).
"""

from __future__ import annotations

from typing import Any

from flask_socketio import SocketIO

# This will be set during application creation (see app.py)
_socketio: SocketIO | None = None


def init_socketio(sock: SocketIO) -> None:
    """Initialize the global SocketIO reference.

    Called from ``app.create_app`` after the ``SocketIO`` instance is created.
    """
    global _socketio
    _socketio = sock


def emit(event: str, data: Any, broadcast: bool = True) -> None:
    """Emit a Socket.IO event safely.

    If the SocketIO instance is not yet initialised this becomes a no‑op.
    ``broadcast=True`` sends the payload to all connected clients.
    """
    if _socketio is None:
        # During early import this can happen – we just ignore.
        return
    _socketio.emit(event, data, broadcast=broadcast)
