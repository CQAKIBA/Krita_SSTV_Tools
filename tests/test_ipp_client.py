# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Daisuke JA1UMW / CQAKIBA.TOKYO
import importlib.util
import os
import struct
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

SRC = os.path.join(os.path.dirname(__file__), "..", "sstv_toolbox", "ipp_client.py")
spec = importlib.util.spec_from_file_location("ipp_client", SRC)
ipp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ipp)
PNG = b"\x89PNG\r\n\x1a\n" + b"sample-content"


class Handler(BaseHTTPRequestHandler):
    last_request = None
    status_code = 0x0000

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        type(self).last_request = (self.path, self.headers.get("Content-Type"), data)
        response = b"\x01\x01" + struct.pack(">H", type(self).status_code) + struct.pack(">I", 1) + b"\x03"
        self.send_response(200)
        self.send_header("Content-Type", "application/ipp")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, *_):
        pass


class Tests(unittest.TestCase):
    def setUp(self):
        Handler.status_code = 0
        Handler.last_request = None
        self.srv = HTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.srv.shutdown()
        self.thread.join(timeout=2)
        self.srv.server_close()

    def test_normalize_url(self):
        self.assertEqual(ipp.normalize_printer_uri("ipp://host:631/printers/sstv"),
                         ("ipp://host:631/printers/sstv", "http://host:631/printers/sstv"))
        self.assertEqual(ipp.normalize_printer_uri("ipps://host/p"),
                         ("ipps://host/p", "https://host/p"))

    def test_reject_invalid_uri(self):
        for value in ("", "file:///tmp/x", "ipp:///path", "ipp://host:bad/path", "ipp://host:99999/p"):
            with self.subTest(value=value):
                with self.assertRaises(ipp.IPPError):
                    ipp.normalize_printer_uri(value)

    def test_print_job_wire_format(self):
        body = ipp.build_print_job("ipp://127.0.0.1/printers/sstv", PNG)
        self.assertEqual(body[:8], b"\x01\x01\x00\x02\x00\x00\x00\x01")
        self.assertEqual(body[8], 1)
        self.assertIn(b"document-format", body)
        self.assertIn(b"image/png", body)
        self.assertTrue(body.endswith(b"\x03" + PNG))

    def test_send_png_to_mock_ipp_server(self):
        url = "ipp://127.0.0.1:{}/printers/sstv".format(self.srv.server_port)
        result = ipp.send_png(url, PNG)
        self.assertIn("0x0000", result)
        path, content_type, data = Handler.last_request
        self.assertEqual(path, "/printers/sstv")
        self.assertEqual(content_type, "application/ipp")
        self.assertIn(b"ipp://127.0.0.1", data)
        self.assertTrue(data.endswith(PNG))

    def test_server_rejects_job(self):
        Handler.status_code = 0x040B  # client-error-document-format-not-supported
        url = "ipp://127.0.0.1:{}/printers/sstv".format(self.srv.server_port)
        with self.assertRaisesRegex(ipp.IPPError, "0x040b"):
            ipp.send_png(url, PNG)

    def test_reject_bad_document_data(self):
        with self.assertRaises(ipp.IPPError):
            ipp.build_print_job("ipp://host/p", b"not a PNG")


if __name__ == "__main__":
    unittest.main()
