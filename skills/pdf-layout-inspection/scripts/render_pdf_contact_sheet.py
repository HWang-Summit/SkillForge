#!/usr/bin/env python3
"""Render a PDF to page PNGs and generate a labelled contact sheet."""

from __future__ import annotations

import argparse
import math
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def natural_page_key(path: Path) -> int:
    match = re.search(r"-(\d+)\.png$", path.name)
    if not match:
        raise ValueError(f"cannot parse page number from {path.name}")
    return int(match.group(1))


def clean_output(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for pattern in ("page-*.png", "pdftoppm-page-*.png", "contact.png"):
        for path in out_dir.glob(pattern):
            path.unlink()


def run_pdftoppm(pdf: Path, out_dir: Path, dpi: int, pdftoppm: str) -> list[Path]:
    if not pdf.exists():
        raise SystemExit(f"PDF not found: {pdf}")
    if shutil.which(pdftoppm) is None and not Path(pdftoppm).exists():
        raise SystemExit(
            "pdftoppm not found. Install Poppler in the active environment "
            "or pass --pdftoppm /path/to/pdftoppm."
        )

    prefix = out_dir / "pdftoppm-page"
    cmd = [pdftoppm, "-r", str(dpi), "-png", str(pdf), str(prefix)]
    subprocess.run(cmd, check=True)

    raw_pages = sorted(out_dir.glob("pdftoppm-page-*.png"), key=natural_page_key)
    if not raw_pages:
        raise SystemExit("pdftoppm produced no PNG pages")

    pages: list[Path] = []
    for idx, path in enumerate(raw_pages, start=1):
        target = out_dir / f"page-{idx:02d}.png"
        path.rename(target)
        pages.append(target)
    return pages


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_contact_sheet(
    pages: list[Path],
    out_path: Path,
    thumb_width: int,
    cols: int,
    label_height: int,
    padding: int,
) -> None:
    if not pages:
        raise SystemExit("no pages to place in contact sheet")

    font = load_font(max(12, min(20, label_height - 8)))
    thumbs: list[tuple[str, Image.Image]] = []
    for page in pages:
        with Image.open(page) as im:
            rgb = im.convert("RGB")
            ratio = thumb_width / rgb.width
            thumb_height = int(rgb.height * ratio)
            thumb = rgb.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        thumbs.append((page.name, thumb))

    cell_w = thumb_width + padding * 2
    cell_h = max(thumb.height for _, thumb in thumbs) + label_height + padding * 2
    rows = math.ceil(len(thumbs) / cols)
    canvas = Image.new("RGB", (cols * cell_w, rows * cell_h), (245, 245, 245))
    draw = ImageDraw.Draw(canvas)

    for idx, (name, thumb) in enumerate(thumbs):
        row, col = divmod(idx, cols)
        x0 = col * cell_w
        y0 = row * cell_h
        draw.rectangle(
            [x0 + 6, y0 + 6, x0 + cell_w - 6, y0 + cell_h - 6],
            fill=(255, 255, 255),
            outline=(210, 210, 210),
        )
        bbox = draw.textbbox((0, 0), name, font=font)
        text_w = bbox[2] - bbox[0]
        draw.text(
            (x0 + (cell_w - text_w) // 2, y0 + padding // 2),
            name,
            fill=(20, 20, 20),
            font=font,
        )
        canvas.paste(thumb, (x0 + padding, y0 + label_height + padding))

    canvas.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", required=True, type=Path, help="Input PDF")
    parser.add_argument("--out", default=Path("rendered_pdf_pages"), type=Path)
    parser.add_argument("--dpi", default=150, type=int)
    parser.add_argument("--pdftoppm", default="pdftoppm")
    parser.add_argument("--thumb-width", default=300, type=int)
    parser.add_argument("--cols", default=3, type=int)
    parser.add_argument("--label-height", default=28, type=int)
    parser.add_argument("--padding", default=18, type=int)
    args = parser.parse_args()

    clean_output(args.out)
    pages = run_pdftoppm(args.pdf, args.out, args.dpi, args.pdftoppm)
    contact = args.out / "contact.png"
    make_contact_sheet(
        pages,
        contact,
        thumb_width=args.thumb_width,
        cols=args.cols,
        label_height=args.label_height,
        padding=args.padding,
    )

    print(f"output_dir={args.out.resolve()}")
    for path in [contact, *pages]:
        print(path)


if __name__ == "__main__":
    main()
