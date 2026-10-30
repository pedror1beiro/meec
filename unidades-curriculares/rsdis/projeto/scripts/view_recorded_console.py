#!/usr/bin/env python3
"""Inspect a saved ROS console checkpoint on any PC, without ROS or Gazebo."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run", type=Path, required=True, help="Folder containing console_state.json"
    )
    parser.add_argument("--port", type=int, default=8770)
    args = parser.parse_args()
    directory = args.run.resolve()
    state = json.loads((directory / "console_state.json").read_text(encoding="utf-8"))
    state.update(recorded=True, last_command="Recorded checkpoint. Mission controls are disabled.")
    payload = json.dumps(state).encode()
    page = (ROOT / "src/rsdis_lunar/web/mission.html").read_bytes()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/":
                content, mime = page, "text/html; charset=utf-8"
            elif path == "/api/state":
                content, mime = payload, "application/json"
            elif re.fullmatch(r"/camera/[A-Za-z][A-Za-z0-9_]*\.jpg", path):
                name = path.removeprefix("/camera/")
                image = directory / ("camera_" + name)
                if not image.is_file():
                    self.send_error(404)
                    return
                content, mime = image.read_bytes(), "image/jpeg"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_POST(self):
            self.send_error(405, "Recorded checkpoints are read-only")

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Recorded checkpoint: http://localhost:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
