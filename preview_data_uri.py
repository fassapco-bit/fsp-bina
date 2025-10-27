#!/usr/bin/env python3
"""Generate a data URI for the bundled calculator preview image.

This helper makes it easy to embed the preview inside chat tools or
static documentation without relying on an external file host.
"""
from __future__ import annotations

import argparse
import base64
from pathlib import Path
from typing import Iterable


def read_bytes(image_path: Path) -> bytes:
    """Return the raw bytes from ``image_path`` if it exists."""
    try:
        return image_path.read_bytes()
    except FileNotFoundError as exc:  # pragma: no cover - simple error branch
        raise SystemExit(f"Could not find image: {image_path}") from exc


def build_data_uri(raw_bytes: bytes) -> str:
    """Encode ``raw_bytes`` as a PNG data URI."""
    encoded = base64.b64encode(raw_bytes).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def chunk_text(text: str, width: int) -> Iterable[str]:
    """Yield successive ``width`` sized chunks from ``text``."""
    for index in range(0, len(text), width):
        yield text[index : index + width]


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Create a data URI string for ui_preview.png",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "image",
        nargs="?",
        default="ui_preview.png",
        type=Path,
        help="path to the PNG preview",
    )
    parser.add_argument(
        "--wrap",
        type=int,
        default=0,
        metavar="N",
        help="if provided, wrap the output every N characters",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    uri = build_data_uri(read_bytes(args.image))
    if args.wrap:
        for chunk in chunk_text(uri, args.wrap):
            print(chunk)
    else:
        print(uri)


if __name__ == "__main__":
    main()
