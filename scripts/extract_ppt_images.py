"""
4개 강의 PPT 파일에서 슬라이드에 표시된 이미지를 추출하여 images/ 폴더에 저장합니다.

사용 방법
1. 레포지토리 루트에 아래 PPT 파일 4개를 둡니다.
   - PART1_파이썬기초와CSV다루기.pptx
   - PART2_엑셀CSV전처리와데이터시각화.pptx
   - PART3_AI머신러닝개념과_회귀_분류모델.pptx
   - PART4_비지도학습_딥러닝맛보기와미니프로젝트.pptx
2. 필요한 패키지를 설치합니다.
   pip install python-pptx pillow pymupdf
3. 실행합니다.
   python scripts/extract_ppt_images.py

참고
- 일반 PNG/JPG 이미지는 PPT 내부 crop 값을 반영하여 저장합니다.
- WMF처럼 Pillow가 직접 읽지 못하는 이미지는 LibreOffice로 슬라이드를 PDF 렌더링한 뒤,
  슬라이드에 표시된 위치 기준으로 잘라 저장합니다.
- WMF 처리까지 하려면 PC에 LibreOffice가 설치되어 있고, soffice/libreoffice 명령이 PATH에 있어야 합니다.
"""

from __future__ import annotations

import csv
import io
import shutil
import subprocess
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

ROOT_DIR = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT_DIR / "images"
RENDER_DIR = ROOT_DIR / "_rendered_pdfs"

PPT_FILES = [
    ("chapter1", ROOT_DIR / "PART1_파이썬기초와CSV다루기.pptx"),
    ("chapter2", ROOT_DIR / "PART2_엑셀CSV전처리와데이터시각화.pptx"),
    ("chapter3", ROOT_DIR / "PART3_AI머신러닝개념과_회귀_분류모델.pptx"),
    ("chapter4", ROOT_DIR / "PART4_비지도학습_딥러닝맛보기와미니프로젝트.pptx"),
]


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def convert_ppt_to_pdf(ppt_path: Path) -> Path:
    RENDER_DIR.mkdir(exist_ok=True)
    pdf_path = RENDER_DIR / f"{ppt_path.stem}.pdf"
    if pdf_path.exists() and pdf_path.stat().st_size > 0:
        return pdf_path

    command = [
        "libreoffice",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(RENDER_DIR),
        str(ppt_path),
    ]

    try:
        subprocess.run(command, check=True)
    except FileNotFoundError:
        command[0] = "soffice"
        subprocess.run(command, check=True)

    return pdf_path


def save_blob_cropped_image(shape, output_path: Path) -> tuple[int, int, str]:
    image = Image.open(io.BytesIO(shape.image.blob)).convert("RGBA")
    width, height = image.size

    left = int(round(clamp(shape.crop_left or 0, 0, 1) * width))
    top = int(round(clamp(shape.crop_top or 0, 0, 1) * height))
    right = int(round(width - clamp(shape.crop_right or 0, 0, 1) * width))
    bottom = int(round(height - clamp(shape.crop_bottom or 0, 0, 1) * height))

    cropped = image if right <= left or bottom <= top else image.crop((left, top, right, bottom))
    cropped.save(output_path, "PNG", optimize=True)
    return cropped.width, cropped.height, "blob-crop"


def save_rendered_cropped_image(shape, output_path: Path, prs, pdf_doc, slide_no: int) -> tuple[int, int, str]:
    slide_width = prs.slide_width
    slide_height = prs.slide_height

    page = pdf_doc[slide_no - 1]
    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    slide_image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)

    left = int(round(shape.left / slide_width * pixmap.width))
    top = int(round(shape.top / slide_height * pixmap.height))
    right = int(round((shape.left + shape.width) / slide_width * pixmap.width))
    bottom = int(round((shape.top + shape.height) / slide_height * pixmap.height))

    left = max(0, min(pixmap.width, left))
    right = max(0, min(pixmap.width, right))
    top = max(0, min(pixmap.height, top))
    bottom = max(0, min(pixmap.height, bottom))

    if right <= left or bottom <= top:
        raise ValueError("이미지 영역을 계산할 수 없습니다.")

    cropped = slide_image.crop((left, top, right, bottom))
    cropped.save(output_path, "PNG", optimize=True)
    return cropped.width, cropped.height, "slide-render-crop"


def main() -> None:
    if IMAGE_DIR.exists():
        shutil.rmtree(IMAGE_DIR)
    IMAGE_DIR.mkdir(parents=True)

    manifest = []

    for chapter_name, ppt_path in PPT_FILES:
        if not ppt_path.exists():
            print(f"[SKIP] PPT 파일 없음: {ppt_path.name}")
            continue

        print(f"[START] {chapter_name}: {ppt_path.name}")
        chapter_dir = IMAGE_DIR / chapter_name
        chapter_dir.mkdir(parents=True, exist_ok=True)

        prs = Presentation(str(ppt_path))
        pdf_doc = None

        for slide_no, slide in enumerate(prs.slides, start=1):
            image_no = 0
            for shape in slide.shapes:
                if shape.shape_type != MSO_SHAPE_TYPE.PICTURE:
                    continue

                image_no += 1
                file_name = f"{chapter_name}_slide{slide_no:03d}_img{image_no:02d}.png"
                output_path = chapter_dir / file_name

                try:
                    width, height, source = save_blob_cropped_image(shape, output_path)
                except Exception:
                    if pdf_doc is None:
                        pdf_path = convert_ppt_to_pdf(ppt_path)
                        pdf_doc = fitz.open(str(pdf_path))
                    width, height, source = save_rendered_cropped_image(shape, output_path, prs, pdf_doc, slide_no)

                manifest.append(
                    {
                        "chapter": chapter_name,
                        "slide_no": slide_no,
                        "image_no": image_no,
                        "path": str(output_path.relative_to(IMAGE_DIR)).replace("\\", "/"),
                        "width": width,
                        "height": height,
                        "source": source,
                    }
                )

        if pdf_doc is not None:
            pdf_doc.close()

        print(f"[DONE] {chapter_name}")

    manifest_path = IMAGE_DIR / "manifest.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as file:
        fieldnames = ["chapter", "slide_no", "image_no", "path", "width", "height", "source"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest)

    print(f"[COMPLETE] 총 {len(manifest)}개 이미지 추출 완료")
    print(f"[MANIFEST] {manifest_path}")


if __name__ == "__main__":
    main()
