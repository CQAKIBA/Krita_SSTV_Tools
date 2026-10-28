"""Calculate visible popup positions without a Qt runtime.
SPDX-License-Identifier: GPL-3.0-or-later
Copyright (c) 2026 Daisuke JA1UMW / CQAKIBA.TOKYO
"""


def floating_window_position(anchor_x, anchor_y, width, height,
                             area_x, area_y, area_width, area_height):
    """Place window top-left at anchor, constrained to screen work area."""
    max_x = area_x + max(0, area_width - width)
    max_y = area_y + max(0, area_height - height)
    return (max(area_x, min(anchor_x, max_x)),
            max(area_y, min(anchor_y, max_y)))
