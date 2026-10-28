"""Small standard-library IPP 1.1 client for sending PNG as a Print-Job.

SPDX-License-Identifier: GPL-3.0-or-later
Copyright (c) 2026 Daisuke JA1UMW / CQAKIBA.TOKYO

Only sends user-requested jobs. Does not discover printers or handle authentication
beyond urllib's basic transport capabilities. The printer MUST support image/png.
"""

import struct
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen


class IPPError(Exception):
    pass


def normalize_printer_uri(uri):
    """Return (printer_uri, HTTP transport URL) preserving port, path and query."""
    uri = uri.strip()
    parts = urlsplit(uri)
    if parts.scheme.lower() not in ("ipp", "ipps", "http", "https"):
        raise IPPError("URLは ipp://, ipps://, http://, https:// を指定してください。")
    if not parts.hostname or parts.username or parts.password or parts.fragment:
        raise IPPError("IPP URLが不正です。ホスト名を確認してください。")
    try:
        port = parts.port  # validates integer/valid range
    except ValueError as exc:
        raise IPPError("ポート番号が不正です。") from exc
    if port is not None and not 1 <= port <= 65535:
        raise IPPError("ポート番号が不正です。")
    scheme = parts.scheme.lower()
    # Preserve the printer URI as intended for IPP attributes. Most servers
    # publish ipp(s) URIs, which should be used if known.
    path = parts.path or "/"
    printer_uri = urlunsplit((scheme, parts.netloc, path, parts.query, ""))
    transport = "https" if scheme in ("ipps", "https") else "http"
    transport_url = urlunsplit((transport, parts.netloc, path, parts.query, ""))
    return printer_uri, transport_url


def _attr(tag, name, value):
    n = name.encode("ascii")
    v = value.encode("utf-8")
    if len(n) > 65535 or len(v) > 65535:
        raise IPPError("IPP属性が長すぎます。")
    return struct.pack(">BH", tag, len(n)) + n + struct.pack(">H", len(v)) + v


def build_print_job(printer_uri, png_bytes, job_name="SSTV from Krita"):
    """RFC 8010 Print-Job (0x0002): operation attrs then PNG document bytes."""
    if not png_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        raise IPPError("PNG形式のデータではありません。")
    operation = b"".join((
        _attr(0x47, "attributes-charset", "utf-8"),
        _attr(0x48, "attributes-natural-language", "en"),
        _attr(0x45, "printer-uri", printer_uri),
        _attr(0x42, "requesting-user-name", "Krita"),
        _attr(0x42, "job-name", job_name),
        _attr(0x49, "document-format", "image/png"),
    ))
    header = struct.pack(">BBHI", 1, 1, 2, 1)  # version 1.1, Print-Job, id 1
    return header + b"\x01" + operation + b"\x03" + png_bytes


def send_png(uri, png_bytes, timeout=12):
    printer_uri, transport_url = normalize_printer_uri(uri)
    body = build_print_job(printer_uri, png_bytes)
    request = Request(
        transport_url,
        data=body,
        headers={"Content-Type": "application/ipp", "Accept": "application/ipp"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            data = response.read(8192)
    except Exception as exc:
        raise IPPError("接続または送信に失敗しました: {}".format(exc)) from exc
    if len(data) < 8 or data[0] != 1:
        raise IPPError("サーバから正しいIPP応答が返されませんでした。")
    status = struct.unpack(">H", data[2:4])[0]
    if status >= 0x0100:
        raise IPPError("IPPサーバがジョブを拒否しました (status=0x{:04x})".format(status))
    return "IPPジョブを受け付けました (status=0x{:04x})".format(status)
