#!/usr/bin/env python3
"""Static HTTP server with Range support, to play test videos in Kodi through adb reverse.

Usage: rangeserver.py <dir> [port]   (listens on 127.0.0.1 only)
"""
import http.server
import os
import re
import sys

ROOT = sys.argv[1]
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8766


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def send_head(self):
        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            return super().send_head()
        size = os.path.getsize(path)
        f = open(path, "rb")
        m = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range", ""))
        if m:
            start = int(m.group(1) or 0)
            end = min(int(m.group(2) or size - 1), size - 1)
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            f.seek(start)
            self._remaining = end - start + 1
        else:
            self.send_response(200)
            self._remaining = size
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(self._remaining))
        self.end_headers()
        return f

    def copyfile(self, src, dst):
        rem = self._remaining
        while rem > 0:
            buf = src.read(min(65536, rem))
            if not buf:
                break
            try:
                dst.write(buf)
            except (BrokenPipeError, ConnectionResetError):
                break
            rem -= len(buf)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
