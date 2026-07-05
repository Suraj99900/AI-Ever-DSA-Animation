# // visualizer/events.py
"""
Event name constants used for Socket.IO communication between backend and frontend.
All events are emitted from the server side and listened to on the client side.
"""

# Core execution lifecycle
EXECUTION_STARTED = "execution_started"
EXECUTION_FINISHED = "execution_finished"
EXECUTION_ABORTED = "execution_aborted"

# Per‑step event – contains detailed snapshot of the interpreter state
EXECUTION_STEP = "execution_step"

# Granular sub‑events (payloads are included in EXECUTION_STEP but also emitted separately for convenience)
LINE_CHANGED = "line_changed"
VARIABLE_CHANGED = "variable_changed"
FUNCTION_CALLED = "function_called"
FUNCTION_RETURNED = "function_returned"
LOOP_ITERATION = "loop_iteration"
CONDITION_EVALUATED = "condition_evaluated"
EXCEPTION_OCCURRED = "exception"

# UI control acknowledgements
RUN_ACK = "run_ack"
PAUSE_ACK = "pause_ack"
RESUME_ACK = "resume_ack"
STEP_ACK = "step_ack"
RESTART_ACK = "restart_ack"
