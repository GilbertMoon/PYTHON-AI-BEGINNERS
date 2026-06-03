"""Export course HTML files to one editable Word document (.docx).

Usage:
    # 1) Install Pandoc first.
    #    Windows: https://pandoc.org/installing.html
    #    macOS:   brew install pandoc
    #    Ubuntu:  sudo apt-get install pandoc
    #
    # 2) Run:
    #    python scripts/export_html_to_docx.py

Default behavior:
- If an ./html directory exists, it is used as the HTML source directory.
- Otherwise, the project root is used because this repository stores chapter HTML files
  at the root level.
- Known course pages are merged in lecture order.
- Any remaining HTML files are appended alphabetically.
- A temporary merged HTML file is created at output/temp_docx/merged_course.html.
- The final Word file is created at output/python_ai_beginners_full.docx.

Notes:
- This script uses Pandoc through subprocess, so Pandoc must be installed and
  available on PATH.
- Word output is editable, but browser CSS layout will not be reproduced exactly.
- Images referenced by relative paths are preserved when the paths are valid.
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional


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


DEFAULT_CSS = """
body {
  font-family: 'Noto Sans KR', 'Malgun Gothic', Arial, sans-serif;
  line-height: 1.65;
  font-size: 11pt;
  color: #1f2937;
}
h1 {
  font-size: 24pt;
  margin: 0 0 14pt 0;
  color: #111827;
}
h2 {
  font-size: 18pt;
  margin-top: 22pt;
  margin-bottom: 10pt;
  color: #1f2937;
}
h3 {
  font-size: 14pt;
  margin-top: 16pt;
  margin-bottom: 8pt;
  color: #1f2937;
}
p {
  margin: 6pt 0;
}
ul, ol {
  margin-top: 6pt;
  margin-bottom: 6pt;
}
li {
  margin: 3pt 0;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin: 10pt 0;
}
th, td {
  border: 1px solid #d1d5db;
  padding: 6pt;
  vertical-align: top;
}
th {
  background: #eef2ff;
  font-weight: bold;
}
pre, code {
  font-family: Consolas, 'Courier New', monospace;
}
pre {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  padding: 8pt;
  white-space: pre-wrap;
}
blockquote {
  border-left: 4px solid #f97316;
  padding-left: 10pt;
  color: #374151;
}
img {
  max-width: 100%;
}
.page-break {
  page-break-before: always;
}
.source-note {
  color: #6b7280;
  font-size: 9pt;
  margin-bottom: 12pt;
}
"""


MAIN_RE = re.compile(r"<main[^>]*>(.*?)</main>", flags=re.IGNORECASE | re.DOTALL)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", flags=re.IGNORECASE | re.DOTALL)
BODY_RE = re.compile(r"<body[^>]*>(.*?)</body>", flags=re.IGNORECASE | re.DOTALL)
SCRIPT_RE = re.compile(r"<script[^>]*>.*?</script>", flags=re.IGNORECASE | re.DOTALL)
STYLE_RE = re.compile(r"<style[^>]*>.*?</style>", flags=re.IGNORECASE | re.DOTALL)
NAV_RE = re.compile(r"<nav[^>]*>.*?</nav>", flags=re.IGNORECASE | re.DOTALL)
HEADER_RE = re.compile(r"<header[^>]*>.*?</header>", flags=re.IGNORECASE | re.DOTALL)


def project_root() -> Path:
    """Return the repository root when this script lives in scripts/."""
    return Path(__file__).resolve().parents[1]


def default_html_dir(root: Path) -> Path:
    """Prefer ./html if present; otherwise use repository root."""
    html_dir = root / "html"
    return html_dir if html_dir.exists() else root


def build_html_file_list(html_dir: Path, pattern: str, use_course_order: bool) -> List[Path]:
    """Build an ordered HTML file list.

    Known course pages are placed first in the intended lecture order. Any remaining
    HTML files are appended alphabetically so that newly added pages are not silently
    omitted.
    """
    all_files = sorted(path for path in html_dir.glob(pattern) if path.is_file())

    if not use_course_order:
        return all_files

    by_name = {path.name: path for path in all_files}
    ordered = [by_name[name] for name in COURSE_ORDER if name in by_name]
    ordered_names = {path.name for path in ordered}
    remaining = [path for path in all_files if path.name not in ordered_names]

    return ordered + remaining


def read_html_text(path: Path) -> str:
    """Read HTML with a few common Korean encodings as fallback."""
    for encoding in ("utf-8", "utf-8-sig", "cp949", "euc-kr"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def extract_title(html_text: str, fallback: str) -> str:
    match = TITLE_RE.search(html_text)
    if not match:
        return fallback
    title = re.sub(r"<[^>]+>", "", match.group(1)).strip()
    return html.unescape(title) or fallback


def extract_content(html_text: str) -> str:
    """Extract the most useful body content for Word conversion.

    The repository pages contain large header/nav sections optimized for web browsing.
    For a Word handout, the main content is usually cleaner and more editable.
    """
    cleaned = SCRIPT_RE.sub("", html_text)
    cleaned = STYLE_RE.sub("", cleaned)

    main_match = MAIN_RE.search(cleaned)
    if main_match:
        content = main_match.group(1)
    else:
        body_match = BODY_RE.search(cleaned)
        content = body_match.group(1) if body_match else cleaned
        content = HEADER_RE.sub("", content)
        content = NAV_RE.sub("", content)

    return content.strip()


def make_merged_html(html_files: Iterable[Path], merged_html: Path, title: str) -> None:
    """Create a single merged HTML file for Pandoc conversion."""
    sections: List[str] = []

    for index, html_file in enumerate(html_files, start=1):
        raw_html = read_html_text(html_file)
        page_title = extract_title(raw_html, fallback=html_file.stem)
        content = extract_content(raw_html)
        page_break_class = "" if index == 1 else " class=\"page-break\""

        section = f"""
<section{page_break_class}>
  <h1>{html.escape(page_title)}</h1>
  <p class="source-note">원본 HTML: {html.escape(html_file.name)}</p>
  {content}
</section>
"""
        sections.append(section)

    merged_html.parent.mkdir(parents=True, exist_ok=True)
    merged_html.write_text(
        f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(title)}</title>
  <style>{DEFAULT_CSS}</style>
</head>
<body>
  <h1>{html.escape(title)}</h1>
  <p class="source-note">이 문서는 HTML 강의안을 편집 가능한 Word 문서로 변환하기 위해 자동 생성되었습니다.</p>
  {''.join(sections)}
</body>
</html>
""",
        encoding="utf-8",
    )


def ensure_pandoc() -> str:
    """Return pandoc executable path or exit with a helpful error."""
    pandoc = shutil.which("pandoc")
    if pandoc:
        return pandoc

    print(
        "Pandoc을 찾을 수 없습니다. 먼저 Pandoc을 설치하고 PATH에 등록해 주세요.\n"
        "- Windows: https://pandoc.org/installing.html\n"
        "- macOS: brew install pandoc\n"
        "- Ubuntu: sudo apt-get install pandoc",
        file=sys.stderr,
    )
    raise SystemExit(1)


def run_pandoc(
    pandoc: str,
    merged_html: Path,
    output_docx: Path,
    resource_path: Path,
    reference_doc: Optional[Path],
    toc: bool,
) -> None:
    """Run Pandoc to convert merged HTML to DOCX."""
    output_docx.parent.mkdir(parents=True, exist_ok=True)

    command = [
        pandoc,
        str(merged_html),
        "--from=html",
        "--to=docx",
        f"--resource-path={resource_path}",
        "--standalone",
        "-o",
        str(output_docx),
    ]

    if toc:
        command.insert(-2, "--toc")

    if reference_doc:
        command.insert(-2, f"--reference-doc={reference_doc}")

    print("Pandoc 실행:")
    print(" ".join(command))

    result = subprocess.run(command, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        raise RuntimeError(f"Pandoc 변환 실패: exit code {result.returncode}")


def parse_args() -> argparse.Namespace:
    root = project_root()
    html_dir = default_html_dir(root)

    parser = argparse.ArgumentParser(
        description="Merge HTML course pages and convert them to an editable DOCX with Pandoc."
    )
    parser.add_argument(
        "--html-dir",
        type=Path,
        default=html_dir,
        help="HTML source directory. Default: ./html if it exists, otherwise project root.",
    )
    parser.add_argument("--pattern", default="*.html", help="HTML glob pattern. Default: *.html")
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "output" / "python_ai_beginners_full.docx",
        help="Final DOCX path.",
    )
    parser.add_argument(
        "--temp-dir",
        type=Path,
        default=root / "output" / "temp_docx",
        help="Temporary working directory for merged HTML.",
    )
    parser.add_argument(
        "--title",
        default="데이터분석을 위한 파이썬 & AI 입문 강의안",
        help="Document title used in the merged DOCX.",
    )
    parser.add_argument(
        "--alphabetical",
        action="store_true",
        help="Ignore predefined course order and merge files alphabetically.",
    )
    parser.add_argument(
        "--reference-doc",
        type=Path,
        default=None,
        help="Optional Pandoc reference DOCX for custom Word styles.",
    )
    parser.add_argument(
        "--toc",
        action="store_true",
        help="Ask Pandoc to generate a table of contents.",
    )
    parser.add_argument(
        "--keep-merged-html",
        action="store_true",
        help="Keep output/temp_docx/merged_course.html after conversion.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = project_root()
    html_dir = args.html_dir.resolve()
    temp_dir = args.temp_dir.resolve()
    output_docx = args.output.resolve()
    merged_html = temp_dir / "merged_course.html"

    if not html_dir.exists():
        print(f"HTML 디렉터리를 찾을 수 없습니다: {html_dir}", file=sys.stderr)
        return 1

    html_files = build_html_file_list(
        html_dir=html_dir,
        pattern=args.pattern,
        use_course_order=not args.alphabetical,
    )

    if not html_files:
        print(f"변환할 HTML 파일이 없습니다: {html_dir / args.pattern}", file=sys.stderr)
        return 1

    pandoc = ensure_pandoc()

    print(f"HTML 디렉터리: {html_dir}")
    print(f"HTML 파일 수: {len(html_files)}")
    print(f"임시 HTML: {merged_html}")
    print(f"최종 DOCX: {output_docx}")

    make_merged_html(html_files=html_files, merged_html=merged_html, title=args.title)

    try:
        run_pandoc(
            pandoc=pandoc,
            merged_html=merged_html,
            output_docx=output_docx,
            resource_path=root,
            reference_doc=args.reference_doc.resolve() if args.reference_doc else None,
            toc=args.toc,
        )
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1

    if not args.keep_merged_html:
        try:
            merged_html.unlink()
        except FileNotFoundError:
            pass

    print(f"완료: {output_docx}")
    print("참고: Word 문서는 편집 가능하지만, HTML/CSS 화면 디자인이 100% 동일하게 유지되지는 않습니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
