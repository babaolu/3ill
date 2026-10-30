#!/usr/bin/env python3
"""3ill aggregator (v0): sessions, photo/pose ingest, capture + viewer pages.

Stdlib only. Run:  python3 server/app.py [port]   (default 8000, binds 0.0.0.0
so phones on the same WiFi can reach it).

API:
  POST /api/sessions                        -> {"id": "<session>"}
  GET  /api/sessions                        -> {"sessions": [...]}
  GET  /api/sessions/<id>                   -> {"id", "photos": [{file, device, ...}]}
  POST /api/sessions/<id>/photos?device=..  (raw image bytes in body)
  GET  /data/<id>/<file>                    -> uploaded file
  GET  /capture/  GET /viewer/              -> phone + laptop pages
"""

import json
import mimetypes
import os
import re
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
MAX_BYTES = 25 * 1024 * 1024


def safe_name(value):
    if value and SAFE.match(value) and "/" not in value and "\\" not in value:
        return value
    return None


def new_session_id():
    return time.strftime("%Y%m%d-%H%M%S")


class Handler(BaseHTTPRequestHandler):
    server_version = "3ill/0.1"

    def log_message(self, *args):
        sys.stderr.write("%s %s\n" % (self.address_string(), args[0] % args[1:]))

    # ---- helpers ----
    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_static(self, path):
        if not os.path.isfile(path):
            self.send_error(404)
            return
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ---- GET ----
    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        parts = [p for p in url.path.split("/") if p]

        if not parts:
            self.send_static(os.path.join(ROOT, "viewer", "index.html"))
        elif parts[0] == "capture":
            self.send_static(os.path.join(ROOT, "capture", "index.html"))
        elif parts[0] == "viewer":
            self.send_static(os.path.join(ROOT, "viewer", "index.html"))
        elif parts[0] == "data" and len(parts) == 3:
            sid, fname = safe_name(parts[1]), safe_name(parts[2])
            if sid and fname:
                self.send_static(os.path.join(DATA, sid, fname))
            else:
                self.send_error(400)
        elif parts[0] == "api" and parts[1:2] == ["sessions"]:
            if len(parts) == 2:
                sessions = sorted(d for d in os.listdir(DATA)) if os.path.isdir(DATA) else []
                self.send_json({"sessions": sessions})
            elif len(parts) == 3 and safe_name(parts[2]):
                self.send_json(session_info(parts[2]))
            else:
                self.send_error(404)
        else:
            self.send_error(404)

    # ---- POST ----
    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        parts = [p for p in url.path.split("/") if p]
        length = int(self.headers.get("Content-Length") or 0)

        if parts[:2] == ["api", "sessions"] and len(parts) == 2 and length == 0:
            os.makedirs(DATA, exist_ok=True)
            sid = new_session_id()
            os.makedirs(os.path.join(DATA, sid), exist_ok=True)
            self.send_json({"id": sid})
            return

        if len(parts) == 4 and parts[:2] == ["api", "sessions"] and parts[3] == "photos":
            sid = safe_name(parts[2])
            if not sid or not os.path.isdir(os.path.join(DATA, sid)):
                self.send_error(404)
                return
            if length <= 0 or length > MAX_BYTES:
                self.send_error(413)
                return
            body = self.rfile.read(length)
            ctype = self.headers.get("Content-Type", "")
            ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(
                ctype.split(";")[0].strip(), "jpg"
            )
            query = urllib.parse.parse_qs(url.query)
            device = safe_name(query.get("device", ["phone"])[0]) or "phone"
            stamp = "%s-%s" % (device, time.strftime("%H%M%S"))
            fname = "%s.%s" % (stamp, ext)
            # Avoid collisions when several phones upload in the same second.
            n = 1
            while os.path.exists(os.path.join(DATA, sid, fname)):
                n += 1
                fname = "%s-%d.%s" % (stamp, n, ext)
            with open(os.path.join(DATA, sid, fname), "wb") as f:
                f.write(body)
            meta = {
                "file": fname,
                "device": device,
                "bytes": len(body),
                "captured_at": time.time(),
            }
            for key in ("heading", "x", "y", "z"):
                if key in query:
                    meta[key] = query[key][0]
            with open(os.path.join(DATA, sid, fname + ".json"), "w") as f:
                json.dump(meta, f)
            self.send_json(meta, status=201)
            return

        self.send_error(404)


def session_info(sid):
    info = {"id": sid, "photos": []}
    sdir = os.path.join(DATA, sid)
    if not os.path.isdir(sdir):
        return info
    for fname in sorted(os.listdir(sdir)):
        if fname.endswith(".json"):
            continue
        meta_path = os.path.join(sdir, fname + ".json")
        if os.path.isfile(meta_path):
            with open(meta_path) as f:
                info["photos"].append(json.load(f))
        else:
            info["photos"].append({"file": fname})
    return info


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print("3ill aggregator on http://0.0.0.0:%d  (capture: /capture/  viewer: /viewer/)" % port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
