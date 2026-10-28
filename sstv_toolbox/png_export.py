"""Non-interactive, reproducible PNG export for IPP Print-Job.

SPDX-License-Identifier: GPL-3.0-or-later
Copyright (c) 2026 Daisuke JA1UMW / CQAKIBA.TOKYO
"""


def export_png_for_ipp(document, filename, info_object_type):
    """Export the full document projection to a PNG without Krita's PNG options dialog.

    Only switch batch mode for the duration of the export; Krita should behave
    normally again for subsequent saves/exports. The return value mirrors
    Document.exportImage (True on success, False on failure).
    """
    options = info_object_type()
    for name, value in (
        ("compression", 3),
        ("indexed", False),
        ("interlaced", False),
        ("alpha", False),
        ("transparencyFillcolor", [255, 255, 255]),
        ("forceSRGB", True),
        ("saveSRGBProfile", True),
    ):
        options.setProperty(name, value)

    was_batchmode = document.batchmode()
    try:
        document.setBatchmode(True)
        return document.exportImage(filename, options)
    finally:
        document.setBatchmode(was_batchmode)
