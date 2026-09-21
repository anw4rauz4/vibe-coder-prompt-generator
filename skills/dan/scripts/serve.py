#!/usr/bin/env python3
"""serve.py — Server web lokal (stdlib) untuk situs hub DAN + artefak deliverables.

Menyajikan /home/user (root workspace) sehingga situs dan tautan unduhan
(zip/pyz di deliverables/) aktif. Tanpa dependensi, tanpa write ke disk.

Pakai:  python3 serve.py [port]     (default 8686)
Buka :  http://localhost:<port>/deliverables/dan-web/
"""
from __future__ import annotations

import functools
import http.server
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAKET = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(PAKET))  # workspace root


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):  # senyap kecuali error
        if args and str(args[1]).startswith(("4", "5")):
            super().log_message(fmt, *args)


def main(argv=None) -> int:
    port = int((argv or sys.argv[1:])[0]) if (argv or sys.argv[1:]) else 8686
    handler = functools.partial(Handler, directory=ROOT)
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as srv:
        print("DAN web hub → http://localhost:%d/deliverables/dan-web/" % port)
        print("Root: %s  (Ctrl+C untuk stop)" % ROOT)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\nstop.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
