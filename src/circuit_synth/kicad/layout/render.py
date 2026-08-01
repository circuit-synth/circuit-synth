# -*- coding: utf-8 -*-
"""Render schematic sheets to images.

Laying a schematic out is a visual judgement, so the result has to be looked
at. KiCad plots the project to PDF and each page is rasterised from there.
"""

import logging
import subprocess
from pathlib import Path
from typing import List, Optional

from .validate import find_kicad_cli

logger = logging.getLogger(__name__)


def render_sheets(root_schematic: Path, output_dir: Path, dpi: int = 110) -> List[Path]:
    """Render every sheet of a project to a PNG.

    Args:
        root_schematic: The project's root .kicad_sch.
        output_dir: Directory the images are written to.
        dpi: Raster resolution. 110 keeps an A3 sheet readable without being
            unwieldy.

    Returns:
        The rendered image paths, one per sheet, in page order.

    Raises:
        RuntimeError: If kicad-cli or PyMuPDF is unavailable, or the plot fails.
    """
    cli = find_kicad_cli()
    if cli is None:
        raise RuntimeError("kicad-cli is not installed")

    try:
        import fitz
    except ImportError as error:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "rendering needs PyMuPDF; install it with 'pip install pymupdf'"
        ) from error

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{root_schematic.stem}.pdf"

    result = subprocess.run(
        [cli, "sch", "export", "pdf", "-o", str(pdf_path), str(root_schematic)],
        capture_output=True,
        text=True,
        timeout=900,
    )
    if not pdf_path.exists():
        raise RuntimeError(f"schematic plot failed: {result.stderr[-500:]}")

    images: List[Path] = []
    with fitz.open(pdf_path) as document:
        for index, page in enumerate(document):
            image_path = output_dir / f"sheet{index:02d}.png"
            page.get_pixmap(dpi=dpi).save(image_path)
            images.append(image_path)

    logger.info("Rendered %d sheet(s) to %s", len(images), output_dir)
    return images
