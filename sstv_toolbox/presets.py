"""Pure-Python preset defaults and dynamic text substitution.
SPDX-License-Identifier: GPL-3.0-or-later
Copyright (c) 2026 Daisuke JA1UMW / CQAKIBA.TOKYO
"""
from datetime import datetime


def defaults():
    entries = [
        ("コールサイン", "{CALLSIGN}", "bottom", 48),
        ("日付", "{DATE}", "bottom", 34),
        ("時刻", "{TIME}", "bottom", 34),
        ("日時", "{DATETIME}", "bottom", 30),
        ("59", "59", "center", 64),
        ("73", "73", "center", 64),
        ("TNX QSO", "TNX QSO", "bottom", 44),
    ]
    return [dict(label=label, text=text, position=position,
                 size=size, font="Sans Serif", color="#ffffff")
            for label, text, position, size in entries]


def resolve_text(template, callsign, now=None):
    now = now or datetime.now()
    for key, value in (
        ("{CALLSIGN}", callsign),
        ("{DATETIME}", now.strftime("%Y-%m-%d %H:%M")),
        ("{DATE}", now.strftime("%Y-%m-%d")),
        ("{TIME}", now.strftime("%H:%M")),
    ):
        template = template.replace(key, value)
    return template
