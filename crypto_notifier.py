#!/usr/bin/env python3
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
APP_DIR = HERE


def _find_hanauta_src() -> Path | None:
    env_candidate = str(os.environ.get("HANAUTA_SRC", "")).strip()
    candidates: list[Path] = []
    if env_candidate:
        candidates.append(Path(env_candidate).expanduser())
    candidates.extend(
        [
            Path.home() / ".config" / "i3" / "hanauta" / "src",
            Path.home() / ".local" / "share" / "hanauta" / "src",
        ]
    )
    for parent in [HERE, *HERE.parents]:
        candidates.append(parent / "hanauta" / "src")
        candidates.append(parent / "src")
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if (candidate / "pyqt" / "shared" / "runtime.py").exists():
            return candidate
    return None


HANAUTA_SRC = _find_hanauta_src()
if HANAUTA_SRC is not None and str(HANAUTA_SRC) not in sys.path:
    sys.path.append(str(HANAUTA_SRC))

from pyqt.shared.crypto import build_price_alerts, load_settings_state, load_tracker_state, save_tracker_state
from pyqt.shared.runtime import entry_command


ACTION_NOTIFICATION_SCRIPT = (
    HANAUTA_SRC / "pyqt" / "shared" / "action_notification.py"
    if HANAUTA_SRC is not None
    else HERE / "action_notification.py"
)
RUNNING = True


def _handle_exit(_signum, _frame) -> None:
    global RUNNING
    RUNNING = False


def send_notification(summary: str, body: str, open_url: str, replace_id: int) -> None:
    if not ACTION_NOTIFICATION_SCRIPT.exists() or not open_url.strip():
        return
    command = entry_command(
        ACTION_NOTIFICATION_SCRIPT,
        "--app-name",
        "Hanauta Crypto",
        "--summary",
        summary,
        "--body",
        body,
        "--action-label",
        "Open",
        "--open-url",
        open_url,
        "--replace-id",
        str(replace_id),
    )
    if not command:
        return
    try:
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception:
        pass


def main() -> int:
    signal.signal(signal.SIGTERM, _handle_exit)
    signal.signal(signal.SIGINT, _handle_exit)

    while RUNNING:
        settings = load_settings_state()
        state = load_tracker_state()
        try:
            alerts, next_state = build_price_alerts(settings, state)
        except Exception:
            alerts, next_state = [], state
        for alert in alerts:
            send_notification(
                str(alert.get("summary", "Crypto alert")),
                str(alert.get("body", "")),
                str(alert.get("url", "")),
                int(alert.get("replace_id", 0) or 0),
            )
        if next_state != state:
            save_tracker_state(next_state)
        for _ in range(60):
            if not RUNNING:
                break
            time.sleep(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
