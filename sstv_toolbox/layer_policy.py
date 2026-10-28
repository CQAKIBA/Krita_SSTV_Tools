"""Conservative background placement decisions without a Krita dependency.

The caller only inspects the bottom-level layer stack.  A white/transparent
paint layer is not proof that it is an untouched Krita default layer; it is
only a hint that lets us choose a useful *non-destructive* insertion point.
SPDX-License-Identifier: GPL-3.0-or-later
Copyright (c) 2026 Daisuke JA1UMW / CQAKIBA.TOKYO
"""


def choose_background_placement(layers):
    """Return (mode, reason), for layers in bottom-to-top order.

    Each layer has ``type``, ``blank`` (True/False/None), and ``nested``.
    The plugin's own managed background should have been removed from this
    analysis already.  Unknown or complex stacks require user confirmation.
    """
    if not layers:
        return "bottom", "empty"
    if any(layer.get("type") != "paintlayer" or layer.get("nested")
           for layer in layers):
        return "ask", "complex"
    if layers[0].get("blank") is True:
        return "above_bottom", "blank"
    return "ask", "content_or_unknown"


def is_blank_bgra(raw, width, height):
    """Check every BGRA/U8 pixel; no sampling or language-specific names.

    White or transparent pixels (even mixed together) are accepted.  Fully
    transparent pixels may have arbitrary RGB channels.  Any nonwhite visible
    pixel or semitransparent pixel is treated as content, conservatively.
    """
    if width < 1 or height < 1 or len(raw) != width * height * 4:
        return False
    pixels = memoryview(raw)
    for i in range(0, len(pixels), 4):
        alpha = pixels[i + 3]
        if alpha == 0:
            continue
        if alpha != 255 or any(pixels[i + j] != 255 for j in range(3)):
            return False
    return True
