# PPT 이미지 폴더

이 폴더는 4개 강의 PPT에서 추출한 이미지 파일을 저장하기 위한 폴더입니다.

## 권장 폴더 구조

```text
images/
├── chapter1/
├── chapter2/
├── chapter3/
├── chapter4/
└── manifest.csv
```

## 이미지 추출 방법

대량의 이미지 파일은 GitHub 커넥터에서 직접 바이너리 파일로 일괄 업로드하기 어렵기 때문에, 로컬 PC에서 아래 스크립트를 실행하여 생성하는 방식을 권장합니다.

```bash
python scripts/extract_ppt_images.py
```

스크립트 실행 후 생성되는 `images/` 폴더를 커밋하면 됩니다.

```bash
git add images
git commit -m "[260603-Jenny] Add cropped PPT images => 30m"
git push origin main
```
