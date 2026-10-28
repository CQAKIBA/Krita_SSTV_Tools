"""Canvas-relative image geometry (no Qt/Krita dependency).
SPDX-License-Identifier: GPL-3.0-or-later
Copyright (c) 2026 Daisuke JA1UMW / CQAKIBA.TOKYO
"""


def fit_dimensions(image_width, image_height, canvas_width, canvas_height, percent=100):
    """Return (w, h) that fit within the canvas at a percentage of maximum fit.

    With percent=100, the first limiting edge reaches the matching canvas edge
    (except at most 1 px of rounding). The input aspect ratio is preserved.
    """
    if min(image_width, image_height, canvas_width, canvas_height) <= 0:
        raise ValueError("画像とキャンバスの幅・高さは正の値にしてください")
    if not 0 < percent <= 100:
        raise ValueError("貼り付け倍率は0より大きく100以下にしてください")
    scale = min(canvas_width / image_width, canvas_height / image_height) * (percent / 100.0)
    return (min(canvas_width, max(1, round(image_width * scale))),
            min(canvas_height, max(1, round(image_height * scale))))


def cover_source_rect(image_width, image_height, canvas_width, canvas_height):
    """Return fractional (x,y,w,h) input crop for center-cropped full-bleed cover."""
    if min(image_width, image_height, canvas_width, canvas_height) <= 0:
        raise ValueError("画像とキャンバスの幅・高さは正の値にしてください")
    target_ratio = canvas_width / canvas_height
    if image_width / image_height > target_ratio:
        source_height = float(image_height)
        source_width = source_height * target_ratio
    else:
        source_width = float(image_width)
        source_height = source_width / target_ratio
    return ((image_width - source_width) / 2.0,
            (image_height - source_height) / 2.0,
            source_width, source_height)
