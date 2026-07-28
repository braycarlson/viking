from __future__ import annotations

from PIL import ImageFont


FONT_NAMES_BOLD = ('DejaVuSans-Bold.ttf', 'arialbd.ttf')
FONT_NAMES_REGULAR = ('DejaVuSans.ttf', 'arial.ttf')


def font_get(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    if bold:
        names = FONT_NAMES_BOLD
    else:
        names = FONT_NAMES_REGULAR

    for name in names:
        try:
            font = ImageFont.truetype(name, size)
        except OSError:
            continue
        else:
            return font

    return ImageFont.load_default(size=size)
