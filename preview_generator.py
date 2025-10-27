"""Generate a static preview image of the kid-friendly calculator UI.

The repository contains a Tkinter application that is meant to be playful
and colourful.  Because automated environments often cannot launch a desktop
window, this helper script produces a lightweight PNG mock-up that mirrors the
layout, colour palette, and copy that the real application shows.  The script
does not depend on third-party packages so that it can run anywhere.

Running ``python preview_generator.py`` will write ``ui_preview.png`` to the
repository root.  The generated image is tracked in git so that users can view
the preview without running the script themselves.
"""

from __future__ import annotations

import struct
import zlib
from typing import Dict, Iterable, List, Tuple


Colour = Tuple[int, int, int]


class Canvas:
    """Minimal pixel canvas for composing the preview image.

    The canvas stores pixels as RGB triples.  Only the functionality required
    for the preview (filling rectangles and rendering a tiny bitmap font) is
    implemented so the code stays compact and dependency-free.
    """

    def __init__(self, width: int, height: int, background: Colour) -> None:
        self.width = width
        self.height = height
        self._pixels: List[List[Colour]] = [
            [background for _ in range(width)] for _ in range(height)
        ]

    def set_pixel(self, x: int, y: int, colour: Colour) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self._pixels[y][x] = colour

    def fill_rect(self, x0: int, y0: int, x1: int, y1: int, colour: Colour) -> None:
        for y in range(max(0, y0), min(self.height, y1)):
            row = self._pixels[y]
            for x in range(max(0, x0), min(self.width, x1)):
                row[x] = colour

    def stroke_rect(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        colour: Colour,
        stroke: int = 2,
    ) -> None:
        for offset in range(stroke):
            left = x0 + offset
            right = x1 - offset - 1
            top = y0 + offset
            bottom = y1 - offset - 1
            for x in range(left, right + 1):
                self.set_pixel(x, top, colour)
                self.set_pixel(x, bottom, colour)
            for y in range(top, bottom + 1):
                self.set_pixel(left, y, colour)
                self.set_pixel(right, y, colour)

    def draw_text(
        self,
        x: int,
        y: int,
        text: str,
        colour: Colour,
        scale: int = 3,
        line_spacing: int = 6,
    ) -> None:
        cursor_x = x
        cursor_y = y
        for char in text:
            if char == "\n":
                cursor_x = x
                cursor_y += (FONT_HEIGHT * scale) + line_spacing
                continue
            glyph = FONT.get(char.upper())
            if glyph is None:
                cursor_x += (FONT_WIDTH * scale) + scale
                continue
            for gy, row in enumerate(glyph):
                for gx, pixel in enumerate(row):
                    if pixel == "#":
                        for dx in range(scale):
                            for dy in range(scale):
                                self.set_pixel(
                                    cursor_x + gx * scale + dx,
                                    cursor_y + gy * scale + dy,
                                    colour,
                                )
            cursor_x += (FONT_WIDTH * scale) + scale

    def to_png(self) -> bytes:
        raw_rows = []
        for row in self._pixels:
            packed = bytearray()
            for r, g, b in row:
                packed.extend((r, g, b))
            raw_rows.append(b"\x00" + bytes(packed))
        raw_image = b"".join(raw_rows)
        compressor = zlib.compressobj()
        image_data = compressor.compress(raw_image) + compressor.flush()

        def chunk(kind: bytes, payload: bytes) -> bytes:
            return (
                struct.pack(">I", len(payload))
                + kind
                + payload
                + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
            )

        header = struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0)
        return (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", header)
            + chunk(b"IDAT", image_data)
            + chunk(b"IEND", b"")
        )


def create_preview() -> Canvas:
    width, height = 720, 480
    canvas = Canvas(width, height, (232, 247, 255))

    # Header banner
    canvas.fill_rect(0, 0, width, 120, (103, 155, 240))
    canvas.draw_text(
        40,
        30,
        "KIDDO CALCULATOR\nFRIENDLY PREVIEW",
        (255, 255, 255),
        scale=4,
        line_spacing=10,
    )

    # Instructions panel
    panel_top = 140
    panel_left = 40
    panel_right = 350
    panel_bottom = 420
    canvas.fill_rect(panel_left, panel_top, panel_right, panel_bottom, (255, 255, 255))
    canvas.stroke_rect(panel_left, panel_top, panel_right, panel_bottom, (103, 155, 240))
    canvas.draw_text(
        panel_left + 20,
        panel_top + 20,
        "STEP 1: ENTER\nYOUR NUMBERS",
        (78, 115, 190),
        scale=3,
        line_spacing=10,
    )

    # Input boxes
    canvas.fill_rect(panel_left + 30, panel_top + 120, panel_right - 30, panel_top + 165, (243, 249, 255))
    canvas.stroke_rect(panel_left + 30, panel_top + 120, panel_right - 30, panel_top + 165, (180, 210, 255), stroke=3)
    canvas.fill_rect(panel_left + 30, panel_top + 185, panel_right - 30, panel_top + 230, (243, 249, 255))
    canvas.stroke_rect(panel_left + 30, panel_top + 185, panel_right - 30, panel_top + 230, (180, 210, 255), stroke=3)
    canvas.draw_text(
        panel_left + 40,
        panel_top + 90,
        "NUMBER 1",
        (120, 150, 210),
        scale=2,
    )
    canvas.draw_text(
        panel_left + 40,
        panel_top + 155,
        "NUMBER 2",
        (120, 150, 210),
        scale=2,
    )

    # Buttons
    button_left = 390
    button_top = 160
    button_width = 140
    button_height = 60
    button_gap = 20
    buttons: Iterable[Tuple[str, Colour]] = [
        ("ADD", (255, 203, 107)),
        ("SUBTRACT", (255, 150, 150)),
        ("MULTIPLY", (144, 213, 172)),
        ("DIVIDE", (148, 194, 255)),
    ]
    for idx, (label, colour) in enumerate(buttons):
        top = button_top + idx * (button_height + button_gap)
        bottom = top + button_height
        canvas.fill_rect(button_left, top, button_left + button_width, bottom, colour)
        canvas.stroke_rect(button_left, top, button_left + button_width, bottom, (255, 255, 255), stroke=3)
        canvas.draw_text(
            button_left + 10,
            top + 15,
            label,
            (60, 60, 60),
            scale=2,
        )

    # Result card
    result_left = 550
    result_top = 200
    result_right = width - 40
    result_bottom = 360
    canvas.fill_rect(result_left, result_top, result_right, result_bottom, (255, 255, 255))
    canvas.stroke_rect(result_left, result_top, result_right, result_bottom, (255, 191, 128), stroke=4)
    canvas.draw_text(
        result_left + 20,
        result_top + 20,
        "RESULT",
        (255, 153, 85),
        scale=3,
    )
    canvas.draw_text(
        result_left + 30,
        result_top + 120,
        "2 + 3 = 5",
        (100, 140, 200),
        scale=4,
    )

    return canvas


def save_png(path: str, png_bytes: bytes) -> None:
    with open(path, "wb") as handle:
        handle.write(png_bytes)


# 5x7 bitmap font for the characters needed in the preview.  Each glyph is
# represented by strings where ``#`` denotes a filled pixel.  Glyphs are
# intentionally chunky so that they remain legible after scaling.
FONT_WIDTH = 5
FONT_HEIGHT = 7


FONT: Dict[str, Tuple[str, ...]] = {
    "A": (
        " ## ",
        "#  #",
        "#  #",
        "####",
        "#  #",
        "#  #",
        "#  #",
    ),
    "B": (
        "### ",
        "#  #",
        "#  #",
        "### ",
        "#  #",
        "#  #",
        "### ",
    ),
    "C": (
        " ## ",
        "#  #",
        "#   ",
        "#   ",
        "#   ",
        "#  #",
        " ## ",
    ),
    "D": (
        "### ",
        "#  #",
        "#  #",
        "#  #",
        "#  #",
        "#  #",
        "### ",
    ),
    "E": (
        "####",
        "#   ",
        "#   ",
        "### ",
        "#   ",
        "#   ",
        "####",
    ),
    "F": (
        "####",
        "#   ",
        "#   ",
        "### ",
        "#   ",
        "#   ",
        "#   ",
    ),
    "G": (
        " ## ",
        "#  #",
        "#   ",
        "# ##",
        "#  #",
        "#  #",
        " ###",
    ),
    "I": (
        "###",
        " # ",
        " # ",
        " # ",
        " # ",
        " # ",
        "###",
    ),
    "K": (
        "#  #",
        "# # ",
        "##  ",
        "##  ",
        "# # ",
        "# # ",
        "#  #",
    ),
    "L": (
        "#   ",
        "#   ",
        "#   ",
        "#   ",
        "#   ",
        "#   ",
        "####",
    ),
    "M": (
        "#   #",
        "## ##",
        "# # #",
        "# # #",
        "#   #",
        "#   #",
        "#   #",
    ),
    "N": (
        "#   #",
        "##  #",
        "##  #",
        "# # #",
        "#  ##",
        "#  ##",
        "#   #",
    ),
    "O": (
        " ## ",
        "#  #",
        "#  #",
        "#  #",
        "#  #",
        "#  #",
        " ## ",
    ),
    "P": (
        "### ",
        "#  #",
        "#  #",
        "### ",
        "#   ",
        "#   ",
        "#   ",
    ),
    "R": (
        "### ",
        "#  #",
        "#  #",
        "### ",
        "# # ",
        "#  #",
        "#  #",
    ),
    "S": (
        " ###",
        "#   ",
        "#   ",
        " ## ",
        "   #",
        "   #",
        "### ",
    ),
    "T": (
        "#####",
        "  #  ",
        "  #  ",
        "  #  ",
        "  #  ",
        "  #  ",
        "  #  ",
    ),
    "U": (
        "#  #",
        "#  #",
        "#  #",
        "#  #",
        "#  #",
        "#  #",
        " ## ",
    ),
    "V": (
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        " # # ",
        "  #  ",
    ),
    "W": (
        "#   #",
        "#   #",
        "#   #",
        "# # #",
        "# # #",
        "## ##",
        "#   #",
    ),
    "Y": (
        "#   #",
        "#   #",
        " # # ",
        "  #  ",
        "  #  ",
        "  #  ",
        "  #  ",
    ),
    "Z": (
        "####",
        "   #",
        "  # ",
        "  # ",
        " #  ",
        "#   ",
        "####",
    ),
    "1": (
        "  # ",
        " ## ",
        "  # ",
        "  # ",
        "  # ",
        "  # ",
        " ###",
    ),
    "2": (
        " ## ",
        "#  #",
        "   #",
        "  # ",
        " #  ",
        "#   ",
        "####",
    ),
    "3": (
        " ## ",
        "#  #",
        "   #",
        " ## ",
        "   #",
        "#  #",
        " ## ",
    ),
    "4": (
        "#  #",
        "#  #",
        "#  #",
        "####",
        "   #",
        "   #",
        "   #",
    ),
    "5": (
        "####",
        "#   ",
        "#   ",
        "### ",
        "   #",
        "#  #",
        " ## ",
    ),
    "6": (
        " ## ",
        "#   ",
        "#   ",
        "### ",
        "#  #",
        "#  #",
        " ## ",
    ),
    "7": (
        "####",
        "   #",
        "  # ",
        "  # ",
        " #  ",
        " #  ",
        " #  ",
    ),
    "8": (
        " ## ",
        "#  #",
        "#  #",
        " ## ",
        "#  #",
        "#  #",
        " ## ",
    ),
    "9": (
        " ## ",
        "#  #",
        "#  #",
        " ###",
        "   #",
        "   #",
        " ## ",
    ),
    "0": (
        " ## ",
        "#  #",
        "# ##",
        "## #",
        "#  #",
        "#  #",
        " ## ",
    ),
    "+": (
        "     ",
        "  #  ",
        "  #  ",
        "#####",
        "  #  ",
        "  #  ",
        "     ",
    ),
    "-": (
        "     ",
        "     ",
        "     ",
        "#####",
        "     ",
        "     ",
        "     ",
    ),
    "=": (
        "     ",
        "#####",
        "     ",
        "#####",
        "     ",
        "     ",
        "     ",
    ),
}


def main() -> None:
    canvas = create_preview()
    save_png("ui_preview.png", canvas.to_png())


if __name__ == "__main__":
    main()

