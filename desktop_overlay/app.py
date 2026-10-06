from __future__ import annotations

import argparse
import json
import threading
import time
from pathlib import Path

import httpx
from mss import mss
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QMenu, QPushButton, QVBoxLayout, QWidget


class MentorOverlay(QWidget):
    ready = pyqtSignal(object)

    def __init__(self, server_url: str, session_token: str, language: str, region: dict, interval: float, full_screen: bool, watch: bool) -> None:
        super().__init__()
        self.server_url = server_url.rstrip("/")
        self.session_token = session_token
        self.language = language
        self.region = region
        self.interval = max(1.0, interval)
        self.full_screen = full_screen
        self.watch = watch
        self.busy = False
        self.drag_offset = None
        self.latest: dict = {}
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.build_ui()
        self.ready.connect(self.render_result)
        self.position_window()
        self.clock = QTimer(self)
        self.clock.timeout.connect(self.update_age)
        self.clock.start(1000)
        if self.watch:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.request_read)
            self.timer.start(int(self.interval * 1000))
        else:
            self.timer = None

    def build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setStyleSheet(
            "#card { background: rgba(17,20,28,242); border: 1px solid rgba(255,255,255,30); border-radius: 12px; }"
        )
        card.setObjectName("card")
        self.card = card
        outer.addWidget(card)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 12)

        header = QHBoxLayout()
        title = QLabel("AI CODING MENTOR")
        title.setStyleSheet("color:#94a3b8; font-size:10px; font-weight:700;")
        header.addWidget(title)
        header.addStretch()
        self.status = QLabel("Ready")
        self.status.setStyleSheet("color:#64748b; font-size:10px;")
        header.addWidget(self.status)
        close_button = QPushButton("✕")
        close_button.setFixedSize(22, 22)
        close_button.clicked.connect(self.close)
        header.addWidget(close_button)
        layout.addLayout(header)

        self.finding = QLabel("No finding")
        self.finding.setWordWrap(True)
        self.finding.setStyleSheet("color:#e2e8f0; font-size:13px; font-weight:600;")
        layout.addWidget(self.finding)

        self.location = QLabel("")
        self.location.setStyleSheet("color:#94a3b8; font-size:10px;")
        layout.addWidget(self.location)

        self.hint = QLabel("Press F8 to analyze")
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet("color:#cbd5e1; font-size:12px;")
        layout.addWidget(self.hint)

        actions = QHBoxLayout()
        for label, handler in (("Read", self.request_read), ("H1", lambda: self.request_hint(1)), ("H2", lambda: self.request_hint(2)), ("Hide", self.hide)):
            button = QPushButton(label)
            button.setStyleSheet("color:#e2e8f0; background:#1f2937; border:1px solid #334155; border-radius:7px; padding:5px 8px;")
            button.clicked.connect(handler)
            actions.addWidget(button)
        layout.addLayout(actions)

        self.footer = QLabel("Screen source is processed transiently; no raw frame is stored.")
        self.footer.setStyleSheet("color:#64748b; font-size:9px;")
        self.footer.setWordWrap(True)
        layout.addWidget(self.footer)

    def position_window(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        geometry = screen.availableGeometry()
        self.setFixedWidth(360)
        self.adjustSize()
        self.move(geometry.right() - self.width() - 20, geometry.top() + 20)

    def request_read(self) -> None:
        if self.busy or not self.session_token:
            return
        self.busy = True
        self.status.setText("Reading…")
        threading.Thread(target=self._read_worker, daemon=True).start()

    def _read_worker(self) -> None:
        try:
            with mss() as grabber:
                monitor = (
                    grabber.monitors[1]
                    if self.full_screen
                    else self.region
                )
                raw = grabber.grab(monitor)
                from PIL import Image
                image = Image.frombytes("RGB", raw.size, raw.rgb)
                from io import BytesIO
                buffer = BytesIO()
                image.save(buffer, format="JPEG", quality=65, optimize=True)
                response = httpx.post(
                    self.server_url + "/api/v1/screen/analyze",
                    params={
                        "session_token": self.session_token,
                        "language": self.language,
                    },
                    files={"frame": ("screen.jpg", buffer.getvalue(), "image/jpeg")},
                    timeout=30.0,
                )
                response.raise_for_status()
                self.ready.emit(response.json())
        except Exception as exc:
            self.ready.emit({"error": str(exc)})
        finally:
            self.busy = False

    def request_hint(self, level: int) -> None:
        if self.busy or not self.latest.get("code") or not self.session_token:
            return
        self.busy = True
        self.status.setText("Mentor thinking…")
        payload = {
            "session_token": self.session_token,
            "code": self.latest.get("code", ""),
            "diagnostics": self.latest.get("diagnostics", []),
            "hint_level": level,
            "allow_solution": False,
        }
        if level == 4:
            payload["allow_solution"] = True
        def worker() -> None:
            try:
                response = httpx.post(
                    self.server_url + "/api/v1/mentor/hint",
                    json=payload,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                self.ready.emit({"hint": data, "keep": True})
            except Exception as exc:
                self.ready.emit({"error": str(exc)})
            finally:
                self.busy = False
        threading.Thread(target=worker, daemon=True).start()

    def render_result(self, data: dict) -> None:
        if data.get("keep"):
            hint = data.get("hint", {})
            self.hint.setText("H" + str(hint.get("hint_level", 1)) + ": " + str(hint.get("hint_text", "")))
            self.status.setText(str(hint.get("provider", "template")))
            return
        if data.get("error"):
            self.status.setText("Error")
            self.finding.setText(str(data["error"]))
            return
        self.latest = data
        self.status.setText(str(round(float(data.get("confidence", 0)) * 100)) + "%")
        diagnostics = data.get("diagnostics") or []
        if diagnostics:
            item = diagnostics[0]
            self.finding.setText(str(item.get("message", "Finding")))
            start = item.get("range", {}).get("start", {})
            self.location.setText("Line " + str(start.get("line", 1)) + ":" + str(start.get("column", 1)))
            self.hint.setText("Press H1/H2 or open the mentor in the browser.")
        elif data.get("notice"):
            self.finding.setText(str(data["notice"]))
            self.location.setText("")
            self.hint.setText("No diagnostic was emitted because confidence is below the safety gate.")
        else:
            self.finding.setText("No problems detected.")
            self.location.setText("")
            self.hint.setText("Keep going.")
        self.show()
        self.raise_()

    def update_age(self) -> None:
        if self.latest.get("timestamp"):
            age = max(0, int(time.time() - float(self.latest["timestamp"])))
            self.footer.setText("Last screen read " + str(age) + "s ago · raw frame not stored")

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = (event.globalPosition().x() - self.x(), event.globalPosition().y() - self.y())

    def mouseMoveEvent(self, event) -> None:
        if self.drag_offset and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(
                int(event.globalPosition().x() - self.drag_offset[0]),
                int(event.globalPosition().y() - self.drag_offset[1]),
            )

    def mouseReleaseEvent(self, event) -> None:
        self.drag_offset = None

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        read = menu.addAction("Read now")
        h1 = menu.addAction("H1 hint")
        h2 = menu.addAction("H2 hint")
        hide = menu.addAction("Hide")
        quit_action = menu.addAction("Quit")
        selected = menu.exec(event.globalPos())
        if selected is read:
            self.request_read()
        elif selected is h1:
            self.request_hint(1)
        elif selected is h2:
            self.request_hint(2)
        elif selected is hide:
            self.hide()
        elif selected is quit_action:
            self.close()


def load_options(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def ensure_session(server_url: str, token: str, language: str) -> str:
    if token:
        return token
    response = httpx.post(
        server_url.rstrip("/") + "/api/v1/sessions",
        json={"user_id": "desktop-overlay", "language": language},
        timeout=10.0,
    )
    response.raise_for_status()
    return str(response.json()["session_token"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="desktop_overlay/config.json")
    parser.add_argument("--server", default="")
    parser.add_argument("--session", default="")
    parser.add_argument("--language", default="python")
    parser.add_argument("--watch", action="store_true")
    args = parser.parse_args()

    options = {}
    config_path = Path(args.config)
    if config_path.exists():
        options = load_options(str(config_path))

    server = args.server or options.get("server_url", "http://127.0.0.1:8000")
    session = args.session or options.get("session_token", "")
    language = args.language or options.get("language", "python")
    try:
        session = ensure_session(server, session, language)
    except Exception as exc:
        raise SystemExit(f"Could not create mentor session: {exc}") from exc
    app = QApplication.instance() or QApplication([])
    window = MentorOverlay(
        server,
        session,
        language,
        options.get("region", {"left": 100, "top": 100, "width": 1400, "height": 900}),
        float(options.get("interval_seconds", 2.0)),
        bool(options.get("full_screen", False)),
        args.watch,
    )
    window.show()
    try:
        import keyboard
        keyboard.add_hotkey("f8", lambda: QTimer.singleShot(0, window.request_read))
        keyboard.add_hotkey("f9", lambda: QTimer.singleShot(0, lambda: window.request_hint(1)))
    except Exception:
        pass
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
