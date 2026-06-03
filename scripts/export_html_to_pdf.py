"""Export course HTML files to one merged PDF.

Usage:
    pip install playwright pypdf
    playwright install chromium
    python scripts/export_html_to_pdf.py

Default behavior:
- If an ./html directory exists, it is used as the HTML source directory.
- Otherwise, the project root is used because this repository stores chapter HTML files
  at the root level.
- HTML files are converted to temporary PDFs with Chromium via Playwright.
- Temporary PDFs are merged into output/python_ai_beginners_full.pdf.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from pypdf import PdfWriter


COURSE_ORDER = [
    "index.html",
    "chapter1.html",
    "chapter1-expanded-guide.html",
    "chapter1-orientation.html",
    "chapter1-jupyter.html",
    "chapter1-python-basic1.html",
    "chapter1-python-basic2.html",
    "chapter1-numpy.html",
    "chapter1-file-io.html",
    "chapter1-csv-read-write.html",
    "chapter1-csv-practice.html",
    "chapter1-semi-project.html",
    "chapter2.html",
    "chapter2-expanded-guide.html",
    "chapter2-csv-automation.html",
    "chapter2-excel-basic1.html",
    "chapter2-excel-basic2.html",
    "chapter2-dataframe.html",
    "chapter2-preprocessing.html",
    "chapter2-graph-basic.html",
    "chapter2-graph-advanced.html",
    "chapter2-eda-practice.html",
    "chapter2-semi-project.html",
    "chapter3.html",
    "chapter3-expanded-guide.html",
    "chapter3-ml-concept.html",
    "chapter3-ml-math.html",
    "chapter3-regression-concept.html",
    "chapter3-regression-practice.html",
    "chapter3-model-evaluation.html",
    "chapter3-classification-concept.html",
    "chapter3-classification-practice.html",
    "chapter3-combined-practice.html",
    "chapter3-semi-project.html",
    "chapter4.html",
    "chapter4-expanded-guide.html",
    "chapter4-unsupervised.html",
    "chapter4-deep-learning-concept.html",
    "chapter4-deep-learning-demo.html",
    "chapter4-database-intro.html",
    "chapter4-project-planning.html",
    "chapter4-project-preprocessing.html",
    "chapter4-project-modeling.html",
    "chapter4-roadmap.html",
    "chapter4-final-project.html",
]


def project_root() -> Path:
    """Return the repository root when this script lives in scripts/."""
    return Path(__file__).resolve().parents[1]


def default_html_dir(root: Path) -> Path:
    """Prefer ./html if present; otherwise use repository root."""
    html_dir = root / "html"
    return html_dir if html_dir.exists() else root


def build_html_file_list(html_dir: Path, pattern: str, use_course_order: bool) -> List[Path]:
    """Build an ordered HTML file list.

    If use_course_order is True, known course pages are placed first in the intended
    lecture order. Any remaining HTML files are appended alphabetically so that newly
    added pages are not silently omitted.
    """
    all_files = sorted(path for path in html_dir.glob(pattern) if path.is_file())

    if not use_course_order:
        return all_files

    by_name = {path.name: path for path in all_files}
    ordered = [by_name[name] for name in COURSE_ORDER if name in by_name]
    ordered_names = {path.name for path in ordered}
    remaining = [path for path in all_files if path.name not in ordered_names]

    return ordered + remaining


def clear_temp_dir(temp_dir: Path) -> None:
    """Remove old temporary PDF files to avoid merging stale output."""
    temp_dir.mkdir(parents=True, exist_ok=True)
    for pdf_file in temp_dir.glob("*.pdf"):
        pdf_file.unlink()


def render_html_files_to_pdf(
    html_files: Iterable[Path],
    temp_dir: Path,
    page_format: str,
    margin_top: str,
    margin_bottom: str,
    margin_left: str,
    margin_right: str,
    timeout_ms: int,
) -> List[Path]:
    """Render each HTML file to a temporary PDF using Chromium."""
    pdf_files: List[Path] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(timeout_ms)

        for index, html_file in enumerate(html_files, start=1):
            pdf_path = temp_dir / f"{index:03d}_{html_file.stem}.pdf"
            file_url = html_file.resolve().as_uri()

            print(f"[{index}] HTML -> PDF: {html_file.name}")

            try:
                page.goto(file_url, wait_until="networkidle", timeout=timeout_ms)
            except PlaywrightTimeoutError:
                print(
                    f"  - networkidle 대기 시간이 초과되어 load 상태로 재시도합니다: {html_file.name}",
                    file=sys.stderr,
                )
                page.goto(file_url, wait_until="load", timeout=timeout_ms)

            page.emulate_media(media="print")
            page.pdf(
                path=str(pdf_path),
                format=page_format,
                print_background=True,
                margin={
                    "top": margin_top,
                    "bottom": margin_bottom,
                    "left": margin_left,
                    "right": margin_right,
                },
            )
            pdf_files.append(pdf_path)

        browser.close()

    return pdf_files


def merge_pdfs(pdf_files: Iterable[Path], output_pdf: Path) -> None:
    """Merge temporary PDFs into one final PDF."""
    writer = PdfWriter()

    for pdf_file in pdf_files:
        writer.append(str(pdf_file))

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    with output_pdf.open("wb") as file:
        writer.write(file)


def parse_args() -> argparse.Namespace:
    root = project_root()
    html_dir = default_html_dir(root)

    parser = argparse.ArgumentParser(
        description="Convert HTML course pages to individual PDFs and merge them into one PDF."
    )
    parser.add_argument(
        "--html-dir",
        type=Path,
        default=html_dir,
        help="HTML source directory. Default: ./html if it exists, otherwise project root.",
    )
    parser.add_argument(
        "--pattern",
        default="*.html",
        help="HTML glob pattern. Default: *.html",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "output" / "python_ai_beginners_full.pdf",
        help="Final merged PDF path.",
    )
    parser.add_argument(
        "--temp-dir",
        type=Path,
        default=root / "output" / "temp_pdf",
        help="Temporary PDF output directory.",
    )
    parser.add_argument(
        "--format",
        default="A4",
        help="PDF page format for Playwright. Default: A4",
    )
    parser.add_argument("--margin-top", default="15mm")
    parser.add_argument("--margin-bottom", default="15mm")
    parser.add_argument("--margin-left", default="12mm")
    parser.add_argument("--margin-right", default="12mm")
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=60_000,
        help="Page load timeout in milliseconds. Default: 60000",
    )
    parser.add_argument(
        "--alphabetical",
        action="store_true",
        help="Ignore predefined course order and merge files alphabetically.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep old temporary PDFs instead of clearing temp dir first. Usually not recommended.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    html_dir = args.html_dir.resolve()
    temp_dir = args.temp_dir.resolve()
    output_pdf = args.output.resolve()

    if not html_dir.exists():
        print(f"HTML 디렉터리를 찾을 수 없습니다: {html_dir}", file=sys.stderr)
        return 1

    if not args.keep_temp:
        clear_temp_dir(temp_dir)
    else:
        temp_dir.mkdir(parents=True, exist_ok=True)

    html_files = build_html_file_list(
        html_dir=html_dir,
        pattern=args.pattern,
        use_course_order=not args.alphabetical,
    )

    if not html_files:
        print(f"변환할 HTML 파일이 없습니다: {html_dir / args.pattern}", file=sys.stderr)
        return 1

    print(f"HTML 디렉터리: {html_dir}")
    print(f"HTML 파일 수: {len(html_files)}")
    print(f"임시 PDF 폴더: {temp_dir}")
    print(f"최종 PDF: {output_pdf}")

    pdf_files = render_html_files_to_pdf(
        html_files=html_files,
        temp_dir=temp_dir,
        page_format=args.format,
        margin_top=args.margin_top,
        margin_bottom=args.margin_bottom,
        margin_left=args.margin_left,
        margin_right=args.margin_right,
        timeout_ms=args.timeout_ms,
    )

    merge_pdfs(pdf_files, output_pdf)

    print(f"완료: {output_pdf}")
    print(f"병합된 PDF 수: {len(pdf_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
