#!/usr/bin/env python3
from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs/lifecycle-atlas"


class AtlasHandler(SimpleHTTPRequestHandler):
    """Serve the generated Atlas with a small health endpoint."""

    server_version = "LifecycleAtlas"
    sys_version = ""

    def version_string(self) -> str:
        return self.server_version

    def _is_health_request(self) -> bool:
        return urlsplit(self.path).path == "/healthz"

    def _send_health(self, include_body: bool) -> None:
        body = b"ok\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - method name is defined by stdlib
        if self._is_health_request():
            self._send_health(include_body=True)
            return
        super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802 - method name is defined by stdlib
        if self._is_health_request():
            self._send_health(include_body=False)
            return
        super().do_HEAD()

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-cache, must-revalidate")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header(
            "Permissions-Policy", "camera=(), geolocation=(), microphone=()"
        )
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
            "font-src 'self'; connect-src 'none'; object-src 'none'; "
            "base-uri 'self'; form-action 'none'; frame-ancestors 'none'",
        )
        super().end_headers()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the standalone Atlas site.")
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 1 <= args.port <= 65535:
        raise SystemExit("--port must be between 1 and 65535")

    handler = partial(AtlasHandler, directory=str(SITE))
    server = ThreadingHTTPServer((args.bind, args.port), handler)
    print(f"Serving Lifecycle Atlas at http://{args.bind}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
