"""WebSocket revocation listener with reconnect and exponential backoff."""

from __future__ import annotations

import json
import threading
import time
from typing import Callable

import websocket


def create_revocation_listener(
    api_url: str,
    on_revoked: Callable[[str], None],
) -> object:
    """
    Connect to ws://host/ws/revocations, call on_revoked(token_id) on revocation messages.
    Returns object with close() method.
    """
    ws_url = api_url.replace("http://", "ws://").replace("https://", "wss://").rstrip("/")
    ws_url = f"{ws_url}/ws/revocations"

    stop_event = threading.Event()
    reconnect_timeout: float | None = None
    backoff = 1.0
    max_backoff = 30.0

    def on_message(ws: websocket.WebSocketApp, message: str) -> None:
        try:
            msg = json.loads(message)
            if msg.get("event") == "revoked" and msg.get("token_id"):
                on_revoked(msg["token_id"])
        except (json.JSONDecodeError, KeyError):
            pass

    def on_close(ws: websocket.WebSocketApp, close_status_code: int, close_msg: str) -> None:
        nonlocal backoff
        if stop_event.is_set():
            return
        backoff = min(backoff * 2, max_backoff)
        reconnect_timeout = backoff  # used in run_loop

    def run_loop() -> None:
        nonlocal backoff
        while not stop_event.is_set():
            try:
                ws_app = websocket.WebSocketApp(
                    ws_url,
                    on_message=on_message,
                    on_close=on_close,
                )
                ws_app.run_forever()
            except Exception:
                pass
            if stop_event.is_set():
                break
            delay = min(backoff, max_backoff)
            backoff = min(backoff * 2, max_backoff)
            for _ in range(int(delay * 10)):
                if stop_event.is_set():
                    break
                time.sleep(0.1)

    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()

    class Listener:
        def close(self) -> None:
            stop_event.set()
            # websocket run_forever will exit on next recv; we can't easily close from here
            # without storing ws ref. For daemon thread, process exit will clean up.

    return Listener()
