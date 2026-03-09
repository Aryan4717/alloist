"""WebSocket revocation listener with reconnect, exponential backoff, verification, heartbeat."""

from __future__ import annotations

import json
import random
import threading
import time
from typing import Callable

import websocket

from . import revocation_verify

HEARTBEAT_INTERVAL = 30.0


def create_revocation_listener(
    api_url: str,
    on_revoked: Callable[[str], None],
) -> object:
    """
    Connect to ws://host/ws/revocations, call on_revoked(token_id) on revocation messages.
    Verifies signed payloads when signature present. Sends heartbeat ping every 30s.
    Returns object with close() method.
    """
    ws_url = api_url.replace("http://", "ws://").replace("https://", "wss://").rstrip("/")
    ws_url = f"{ws_url}/ws/revocations"
    http_base = api_url.rstrip("/").replace("ws://", "http://").replace("wss://", "https://")

    stop_event = threading.Event()
    backoff = 1.0
    max_backoff = 30.0
    backoff_lock = threading.Lock()
    last_heartbeat = [0.0]  # mutable for closure

    def on_message(ws: websocket.WebSocketApp, message: str) -> None:
        try:
            msg = json.loads(message)
            if msg.get("type") == "pong":
                with backoff_lock:
                    last_heartbeat[0] = time.time()
                return
            if msg.get("event") != "revoked" or not msg.get("token_id"):
                return
            token_id = msg["token_id"]
            if "signature" in msg:
                pub_key = revocation_verify.fetch_revocation_public_key(http_base)
                if not revocation_verify.verify_revocation_payload(msg, pub_key):
                    return
            on_revoked(token_id)
        except (json.JSONDecodeError, KeyError):
            pass

    def on_open(_ws: websocket.WebSocketApp) -> None:
        with backoff_lock:
            nonlocal backoff
            backoff = 1.0

    def on_close(ws: websocket.WebSocketApp, close_status_code: int, close_msg: str) -> None:
        with backoff_lock:
            nonlocal backoff
            if stop_event.is_set():
                return
            backoff = min(backoff * 2, max_backoff)

    def heartbeat_loop(app_ref: list) -> None:
        while not stop_event.is_set():
            time.sleep(HEARTBEAT_INTERVAL)
            if stop_event.is_set():
                break
            app = app_ref[0] if app_ref else None
            if app and hasattr(app, "send"):
                try:
                    sock = getattr(app, "sock", None)
                    if sock is not None and getattr(sock, "connected", False):
                        app.send(json.dumps({"type": "ping"}))
                except Exception:
                    pass

    def run_loop() -> None:
        nonlocal backoff
        app_ref: list = []
        while not stop_event.is_set():
            try:
                ws_app = websocket.WebSocketApp(
                    ws_url,
                    on_message=on_message,
                    on_close=on_close,
                    on_open=on_open,
                )
                app_ref[:] = [ws_app]
                hb_thread = threading.Thread(target=heartbeat_loop, args=(app_ref,), daemon=True)
                hb_thread.start()
                ws_app.run_forever()
            except Exception:
                pass
            if stop_event.is_set():
                break
            delay = min(backoff, max_backoff)
            jitter = delay * (0.5 + random.random())
            with backoff_lock:
                backoff = min(backoff * 2, max_backoff)
            for _ in range(int(jitter * 10)):
                if stop_event.is_set():
                    break
                time.sleep(0.1)

    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()

    class Listener:
        def close(self) -> None:
            stop_event.set()

    return Listener()
