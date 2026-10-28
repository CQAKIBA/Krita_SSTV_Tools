"""Find Krita's Undo History docker without relying only on translated text.
SPDX-License-Identifier: GPL-3.0-or-later
Copyright (c) 2026 Daisuke JA1UMW / CQAKIBA.TOKYO
"""


def _normal(value):
    return "".join(ch for ch in str(value or "").casefold() if ch.isalnum())


def history_docker(dockers):
    """Prefer stable Qt object IDs, with a limited title fallback.

    Deliberately avoid Brush Preset History, which is an unrelated docker.
    """
    dockers = list(dockers)
    exact_ids = {"history", "historydock", "historydocker", "undohistory", "undohistorydocker", "kisundohistory"}
    for docker in dockers:
        name = _normal(docker.objectName())
        if name in exact_ids:
            return docker
    for docker in dockers:
        name = _normal(docker.objectName())
        if ("history" in name and "brush" not in name and "preset" not in name
                and "recorder" not in name):
            return docker
    for docker in dockers:
        title = _normal(docker.windowTitle())
        if title in {"undohistory", "編集履歴", "元に戻す履歴", "操作履歴", "履歴"}:
            return docker
    return None
