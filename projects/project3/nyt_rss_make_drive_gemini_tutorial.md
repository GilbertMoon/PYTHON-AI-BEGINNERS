# NYTimes RSS 뉴스 자동 번역·워드클라우드 보고서 자동화 실습

## 프로젝트 개요

이 문서는 초보자가 그대로 따라 할 수 있도록 작성한 실습 가이드입니다.

최종 목표는 다음 자동화 흐름을 구현하는 것입니다.

```text
Make가 NYTimes RSS를 주기적으로 확인
↓
새 뉴스 1건을 JSON 파일로 Google Drive inbox 폴더에 저장
↓
Google Drive for desktop이 내 PC로 자동 동기화
↓
로컬 Jupyter Notebook이 inbox의 JSON 파일을 읽음
↓
Gemini API로 제목/요약을 한국어로 번역
↓
주요 키워드 워드클라우드 이미지 생성
↓
HTML 보고서 생성
↓
Google Drive outbox 폴더에 보고서 저장
↓
Make가 outbox의 새 보고서를 감지
↓
Gmail로 보고서 발송
↓
Google Sheets에 발송 이력 기록
```

---

## 0. 이 실습에서 배우는 것

| 구분 | 학습 내용 |
|---|---|
| 데이터 수집 | Make RSS 모듈로 NYTimes RSS 수집 |
| 데이터 적재 | Google Drive에 JSON 파일 저장 |
| 로컬 자동 처리 | Jupyter Notebook으로 Drive 동기화 폴더 읽기 |
| AI 활용 | Gemini API로 영어 뉴스 제목/요약을 한국어 번역 |
| 텍스트 시각화 | WordCloud 이미지 생성 |
| 보고서 작성 | HTML 자동 보고서 생성 |
| 자동 발송 | Make + Gmail로 보고서 발송 |
| 로그 관리 | Google Sheets에 발송 이력 저장 |

---

## 1. 전체 아키텍처

```text
┌────────────────────┐
│ NYTimes RSS Feed    │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Make Scenario 1     │
│ RSS 수집            │
└─────────┬──────────┘
          │ JSON 파일 생성
          ▼
┌────────────────────┐
│ Google Drive        │
│ /nyt_news_project   │
│   /inbox            │
└─────────┬──────────┘
          │ Drive for desktop 동기화
          ▼
┌────────────────────┐
│ Local Notebook      │
│ 번역/워드클라우드/보고서 │
└─────────┬──────────┘
          │ HTML 보고서 저장
          ▼
┌────────────────────┐
│ Google Drive        │
│ /nyt_news_project   │
│   /outbox           │
└─────────┬──────────┘
          │ 새 보고서 감지
          ▼
┌────────────────────┐
│ Make Scenario 2     │
│ Gmail 발송 + 로그 저장 │
└────────────────────┘
```

---

## 2. 준비물

### 2.1 필수 계정

1. Google 계정
2. Make 계정
3. Gemini API Key
4. Gmail 계정

### 2.2 PC 설치 프로그램

1. Python 3.10 이상
2. VS Code
3. Google Drive for desktop

### 2.3 Python 패키지

이 실습에서는 아래 패키지를 사용합니다.

```text
jupyter
pandas
google-genai
wordcloud
matplotlib
```

---

## 3. Google Drive 동기화 폴더 준비

이 실습은 Google Drive API를 직접 코딩하지 않습니다.

대신 **Google Drive for desktop**을 설치해서 Google Drive를 PC 폴더처럼 사용합니다.

### 3.1 Google Drive for desktop 설치

1. 브라우저에서 `Google Drive for desktop` 검색
2. Google 공식 다운로드 페이지에서 설치 파일 다운로드
3. Windows에서는 `GoogleDriveSetup.exe` 실행
4. Google 계정으로 로그인
5. 파일 탐색기에 `Google Drive` 또는 `G:\내 드라이브`가 보이는지 확인

### 3.2 Google Drive에 실습 폴더 만들기

Google Drive의 `내 드라이브` 아래에 다음 폴더를 만듭니다.

```text
내 드라이브
└── nyt_news_project
    ├── inbox
    ├── outbox
    ├── archive
    └── logs
```

각 폴더의 역할은 다음과 같습니다.

| 폴더 | 역할 |
|---|---|
| inbox | Make가 RSS 뉴스 JSON 파일을 저장하는 곳 |
| outbox | Notebook이 만든 보고서를 저장하는 곳 |
| archive | Notebook 처리 완료 후 원본 JSON을 옮기는 곳 |
| logs | 실행 로그 저장용 |

### 3.3 Windows 경로 예시

PC마다 Google Drive 경로가 다를 수 있습니다.

가장 흔한 예시는 다음과 같습니다.

```text
G:\내 드라이브\nyt_news_project
```

또는 다음처럼 보일 수도 있습니다.

```text
C:\Users\사용자명\Google Drive\내 드라이브\nyt_news_project
```

이 경로는 뒤에서 **노트북 설정 셀에 직접 입력**합니다.

---

## 4. Make 시나리오 1 만들기: RSS → Google Drive inbox 저장

첫 번째 Make 시나리오는 NYTimes RSS를 주기적으로 확인하고, 새 뉴스가 있으면 Google Drive `inbox` 폴더에 JSON 파일로 저장합니다.

### 4.1 시나리오 이름

```text
NYTimes RSS Collector
```

### 4.2 사용할 RSS 주소

초보 실습에서는 Technology RSS를 추천합니다.

```text
https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml
```

다른 카테고리로 바꾸고 싶으면 아래처럼 변경할 수 있습니다.

```text
https://rss.nytimes.com/services/xml/rss/nyt/World.xml
https://rss.nytimes.com/services/xml/rss/nyt/Business.xml
https://rss.nytimes.com/services/xml/rss/nyt/Science.xml
https://rss.nytimes.com/services/xml/rss/nyt/Health.xml
```

### 4.3 Make 모듈 구성

```text
Scheduler
↓
RSS - Watch RSS feed items
↓
JSON - Create JSON
↓
Google Drive - Upload a file
```

### 4.4 Scheduler 설정

처음 실습할 때는 너무 자주 실행하지 않아도 됩니다.

추천 설정:

```text
Every day at 09:00
```

테스트할 때는 수동으로 `Run once`를 누르면 됩니다.

### 4.5 RSS 모듈 설정

모듈:

```text
RSS > Watch RSS feed items
```

설정:

```text
URL: https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml
Limit: 5
```

### 4.6 JSON 모듈 설정

모듈:

```text
JSON > Create JSON
```

JSON 구조 예시:

```json
{
  "source": "NYTimes Technology RSS",
  "title": "RSS 모듈의 title 값을 매핑",
  "description": "RSS 모듈의 description 값을 매핑",
  "link": "RSS 모듈의 link 값을 매핑",
  "published_at": "RSS 모듈의 pubDate 또는 date 값을 매핑",
  "collected_at": "Make 실행 시각 now 값을 매핑"
}
```

Make 화면에서는 위 값을 직접 입력하지 않고, 오른쪽 매핑 패널에서 RSS 결과값을 클릭해서 넣습니다.

예시:

```text
source       : NYTimes Technology RSS
title        : RSS title
description  : RSS description
link         : RSS link
published_at : RSS pubDate
collected_at : now
```

### 4.7 Google Drive 업로드 설정

모듈:

```text
Google Drive > Upload a file
```

설정:

```text
Folder: 내 드라이브 / nyt_news_project / inbox
File name: nyt_{{formatDate(now; "YYYYMMDD_HHmmss")}}.json
Data: JSON 모듈의 결과값
Mime type: application/json
```

Make에서 파일명이 중복될 수 있으면 뒤에 뉴스 제목 일부나 RSS item ID를 붙여도 됩니다.

예시:

```text
nyt_{{formatDate(now; "YYYYMMDD_HHmmss")}}_{{replace(1.title; "/"; "-")}}.json
```

초보 실습에서는 파일명이 너무 복잡해지지 않도록 시간 기반 파일명만 사용해도 충분합니다.

### 4.8 테스트

1. Make에서 `Run once` 클릭
2. RSS 새 항목이 잡히는지 확인
3. Google Drive `inbox` 폴더에 JSON 파일이 생성되는지 확인
4. 내 PC의 Google Drive 동기화 폴더에도 같은 파일이 보이는지 확인

---

## 5. 로컬 Jupyter Notebook 실습 폴더 만들기

이제 로컬 PC에서 **주피터 노트북 1개로 전체 흐름을 실행하는 방식**으로 구성합니다.

### 5.1 프로젝트 폴더 만들기

예를 들어 바탕화면 또는 작업 폴더에서 다음 폴더를 만듭니다.

```text
nyt_rss_local_processor
```

VS Code에서 이 폴더를 엽니다.

### 5.2 최종 폴더 구조

아래처럼 최대한 단순하게 구성합니다.

```text
nyt_rss_local_processor/
│
├── nyt_rss_make_drive_gemini.ipynb
└── requirements.txt
```

> 이번 실습은 **수업용/테스트용** 기준으로 단순화합니다.
> 따라서 API Key, Drive 경로 같은 값도 노트북 안에 직접 적는 방식으로 설명합니다.

---

## 6. 가상환경 생성 및 패키지 설치

### 6.1 Windows PowerShell 기준

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install jupyter pandas google-genai wordcloud matplotlib
```

### 6.2 macOS / Linux 기준

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install jupyter pandas google-genai wordcloud matplotlib
```

VS Code에서 새 Jupyter Notebook 파일을 만들고 이름을 다음처럼 저장합니다.

```text
nyt_rss_make_drive_gemini.ipynb
```

---

## 7. 파일 1: requirements.txt

프로젝트 루트에 `requirements.txt` 파일을 만들고 아래 내용을 붙여넣습니다.

```txt
jupyter
pandas
google-genai
wordcloud
matplotlib
```

노트북 안에서 바로 설치하고 싶다면 첫 번째 셀에 아래처럼 입력해도 됩니다.

```python
%pip install pandas google-genai wordcloud matplotlib
```

---

## 8. 파일 2: `nyt_rss_make_drive_gemini.ipynb` 만들기

이제부터는 `.py` 파일이 아니라 **노트북 셀 단위로 실행**합니다.

추천 셀 구성은 다음과 같습니다.

```text
선택 셀: 패키지 설치
셀 1: 설정값 하드코딩
셀 2: 공통 함수 정의
셀 3: 샘플 JSON 생성(선택)
셀 4: 전체 실행
```

---

## 9. 노트북 셀 1: 설정값 하드코딩

테스트용이므로 `.env` 파일 없이 아래처럼 **노트북 안에 직접 값 입력** 방식으로 진행합니다.

```python
from pathlib import Path
from datetime import datetime
from html import unescape
import base64
import json
import re
import shutil
import time

import pandas as pd
from wordcloud import WordCloud, STOPWORDS

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    from google import genai
except ImportError:
    genai = None


# =============================
# 테스트용 설정값 직접 입력
# =============================
GEMINI_API_KEY = "여기에_테스트용_Gemini_API_Key_직접입력"
DRIVE_BASE_DIR = r"G:\내 드라이브\nyt_news_project"
USE_GEMINI = True
MAX_ITEMS_PER_RUN = 20
FONT_PATH = r""   # 예: r"C:\Windows\Fonts\malgun.ttf"


BASE_DIR = Path(DRIVE_BASE_DIR)
INBOX_DIR = BASE_DIR / "inbox"
OUTBOX_DIR = BASE_DIR / "outbox"
ARCHIVE_DIR = BASE_DIR / "archive"
LOGS_DIR = BASE_DIR / "logs"

for path in [BASE_DIR, INBOX_DIR, OUTBOX_DIR, ARCHIVE_DIR, LOGS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

print("설정 완료")
print("Google Drive 기준 폴더:", BASE_DIR)
print("Gemini 사용 여부:", USE_GEMINI)
```

Gemini 없이 먼저 테스트하려면 아래처럼 바꾸면 됩니다.

```python
GEMINI_API_KEY = ""
USE_GEMINI = False
```

> 수업용으로는 하드코딩이 가장 단순하지만, 실무에서는 키를 코드에 직접 넣지 않는 것이 좋습니다.

---

## 10. 노트북 셀 2: 공통 함수 정의

아래 셀 하나에 핵심 함수들을 넣습니다.

```python
def clean_html(text):
    if text is None:
        return ""

    text = unescape(str(text))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def read_news_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "items" in data and isinstance(data["items"], list):
        items = data["items"]
    elif isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = [data]
    else:
        items = []

    cleaned_items = []

    for item in items:
        title = clean_html(item.get("title", ""))
        description = clean_html(item.get("description", ""))
        link = str(item.get("link", "")).strip()
        published_at = str(item.get("published_at", item.get("pubDate", item.get("date", "")))).strip()
        collected_at = str(item.get("collected_at", "")).strip()
        source = str(item.get("source", "NYTimes RSS")).strip()

        if not title and not link:
            continue

        cleaned_items.append({
            "source_file": file_path.name,
            "source": source,
            "title_en": title,
            "summary_en": description,
            "link": link,
            "published_at": published_at,
            "collected_at": collected_at,
        })

    return cleaned_items


def load_all_inbox_items(inbox_dir, max_items):
    json_files = sorted(inbox_dir.glob("*.json"))
    all_items = []
    used_files = []
    seen_links = set()

    for file_path in json_files:
        try:
            items = read_news_json(file_path)
            used_files.append(file_path)
        except Exception as e:
            print(f"[경고] JSON 읽기 실패: {file_path.name} / {e}")
            continue

        for item in items:
            link = item.get("link", "")

            if link and link in seen_links:
                continue

            if link:
                seen_links.add(link)

            all_items.append(item)

            if len(all_items) >= max_items:
                break

        if len(all_items) >= max_items:
            break

    return all_items, used_files


def parse_json_from_gemini_text(text):
    if not text:
        return {}

    cleaned = text.strip()
    cleaned = re.sub(r"^```json", "", cleaned).strip()
    cleaned = re.sub(r"^```", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return {}

    return {}


def translate_with_gemini(client, title_en, summary_en):
    prompt = f"""
다음은 NYTimes RSS 뉴스의 제목과 요약입니다.

[영문 제목]
{title_en}

[영문 요약]
{summary_en}

작업:
1. 제목을 자연스러운 한국어로 번역하세요.
2. 요약을 자연스러운 한국어로 번역하세요.
3. 핵심 키워드 5개를 한국어로 추출하세요.

반드시 아래 JSON 형식으로만 답하세요.

{{
  "title_ko": "한국어 제목",
  "summary_ko": "한국어 요약",
  "keywords_ko": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"]
}}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    result = parse_json_from_gemini_text(response.text)

    return {
        "title_ko": result.get("title_ko", title_en),
        "summary_ko": result.get("summary_ko", summary_en),
        "keywords_ko": result.get("keywords_ko", []),
    }


def translate_items(items, use_gemini, api_key):
    if not use_gemini:
        print("Gemini 번역 비활성화: 원문을 그대로 사용합니다.")
        for item in items:
            item["title_ko"] = item["title_en"]
            item["summary_ko"] = item["summary_en"]
            item["keywords_ko"] = []
        return items

    if not api_key:
        print("[경고] API Key가 비어 있습니다. 원문을 그대로 사용합니다.")
        for item in items:
            item["title_ko"] = item["title_en"]
            item["summary_ko"] = item["summary_en"]
            item["keywords_ko"] = []
        return items

    if genai is None:
        print("[경고] google-genai 패키지를 불러올 수 없습니다. 원문을 그대로 사용합니다.")
        for item in items:
            item["title_ko"] = item["title_en"]
            item["summary_ko"] = item["summary_en"]
            item["keywords_ko"] = []
        return items

    client = genai.Client(api_key=api_key)

    for index, item in enumerate(items, start=1):
        print(f"Gemini 번역 중... ({index}/{len(items)}) {item['title_en'][:40]}")
        try:
            result = translate_with_gemini(client, item["title_en"], item["summary_en"])
            item["title_ko"] = result["title_ko"]
            item["summary_ko"] = result["summary_ko"]
            item["keywords_ko"] = result["keywords_ko"]
        except Exception as e:
            print(f"[경고] Gemini 번역 실패. 원문 사용: {e}")
            item["title_ko"] = item["title_en"]
            item["summary_ko"] = item["summary_en"]
            item["keywords_ko"] = []

        time.sleep(0.5)

    return items


def make_wordcloud_text(items):
    texts = []
    for item in items:
        texts.append(item.get("title_en", ""))
        texts.append(item.get("summary_en", ""))
        keywords = item.get("keywords_ko", [])
        if isinstance(keywords, list):
            texts.extend(keywords)
    return " ".join(texts)


def create_wordcloud_image(items, output_path, font_path=""):
    text = make_wordcloud_text(items)
    if not text.strip():
        text = "news technology artificial intelligence data cloud automation"

    stopwords = set(STOPWORDS)
    stopwords.update({"said", "will", "new", "one", "two", "may", "also", "more", "news", "york", "times", "nyt", "rss"})

    wc_kwargs = {
        "width": 1200,
        "height": 700,
        "background_color": "white",
        "stopwords": stopwords,
        "collocations": False,
    }

    if font_path and Path(font_path).exists():
        wc_kwargs["font_path"] = font_path

    wordcloud = WordCloud(**wc_kwargs).generate(text)

    plt.figure(figsize=(12, 7))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"워드클라우드 저장 완료: {output_path}")


def image_to_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def build_report_html(items, wordcloud_path, report_title):
    image_base64 = image_to_base64(wordcloud_path)
    now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows_html = []
    for index, item in enumerate(items, start=1):
        keywords = item.get("keywords_ko", [])
        keyword_text = ", ".join(keywords) if isinstance(keywords, list) else ""
        rows_html.append(f"""
        <tr>
            <td>{index}</td>
            <td>
                <strong>{item.get('title_ko', '')}</strong><br>
                <span class="small">원문: {item.get('title_en', '')}</span>
            </td>
            <td>{item.get('summary_ko', '')}</td>
            <td>{keyword_text}</td>
            <td><a href="{item.get('link', '')}" target="_blank">원문 보기</a></td>
        </tr>
        """)

    rows = "\n".join(rows_html)

    html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{report_title}</title>
    <style>
        body {{ font-family: Arial, 'Malgun Gothic', sans-serif; margin: 40px; line-height: 1.6; color: #222; }}
        h1 {{ border-bottom: 3px solid #333; padding-bottom: 10px; }}
        .summary-box {{ background: #f5f7fa; border: 1px solid #d9dee7; padding: 16px; border-radius: 8px; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; vertical-align: top; }}
        th {{ background: #f0f0f0; }}
        .small {{ color: #666; font-size: 0.9em; }}
        .wordcloud {{ max-width: 100%; border: 1px solid #ddd; border-radius: 8px; }}
        .footer {{ margin-top: 40px; color: #777; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>{report_title}</h1>
    <div class="summary-box">
        <p><strong>생성 시각:</strong> {now_text}</p>
        <p><strong>뉴스 개수:</strong> {len(items)}건</p>
        <p>이 보고서는 NYTimes RSS 제목과 요약만 사용해 생성했습니다.</p>
    </div>
    <h2>1. 주요 키워드 워드클라우드</h2>
    <img class="wordcloud" src="data:image/png;base64,{image_base64}" alt="wordcloud">
    <h2>2. 번역 뉴스 목록</h2>
    <table>
        <thead>
            <tr>
                <th>번호</th>
                <th>제목</th>
                <th>요약</th>
                <th>키워드</th>
                <th>링크</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
    <div class="footer">
        <p>자동 생성 보고서 · Jupyter Notebook + Gemini API + Google Drive + Make</p>
    </div>
</body>
</html>
"""

    return html


def save_translated_csv(items, csv_path):
    rows = []
    for item in items:
        keywords = item.get("keywords_ko", [])
        keyword_text = ", ".join(keywords) if isinstance(keywords, list) else ""
        rows.append({
            "source": item.get("source", ""),
            "title_en": item.get("title_en", ""),
            "summary_en": item.get("summary_en", ""),
            "title_ko": item.get("title_ko", ""),
            "summary_ko": item.get("summary_ko", ""),
            "keywords_ko": keyword_text,
            "link": item.get("link", ""),
            "published_at": item.get("published_at", ""),
            "collected_at": item.get("collected_at", ""),
            "source_file": item.get("source_file", ""),
        })

    pd.DataFrame(rows).to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"CSV 저장 완료: {csv_path}")


def archive_files(files, archive_dir):
    for file_path in files:
        target_path = archive_dir / file_path.name

        if target_path.exists():
            stem = file_path.stem
            suffix = file_path.suffix
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_path = archive_dir / f"{stem}_{timestamp}{suffix}"

        shutil.move(str(file_path), str(target_path))
        print(f"archive 이동 완료: {target_path}")


def run_pipeline():
    print("====================================")
    print("NYTimes RSS 자동 보고서 생성 시작")
    print("====================================")
    print("Google Drive 기준 폴더:", BASE_DIR)
    print("Gemini 사용 여부:", USE_GEMINI)

    items, used_files = load_all_inbox_items(INBOX_DIR, MAX_ITEMS_PER_RUN)

    if not items:
        print("처리할 JSON 파일이 없습니다.")
        print("먼저 Make가 inbox 폴더에 JSON 파일을 만들었는지 확인하세요.")
        return None

    print("처리할 뉴스 개수:", len(items))
    print("처리할 원본 파일 개수:", len(used_files))

    translated_items = translate_items(items, USE_GEMINI, GEMINI_API_KEY)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_title = f"NYTimes RSS AI 뉴스 브리핑 - {datetime.now().strftime('%Y-%m-%d')}"

    csv_path = OUTBOX_DIR / f"nyt_translated_news_{timestamp}.csv"
    wordcloud_path = OUTBOX_DIR / f"nyt_wordcloud_{timestamp}.png"
    report_path = OUTBOX_DIR / f"nyt_report_{timestamp}.html"
    log_path = LOGS_DIR / f"run_log_{timestamp}.txt"

    save_translated_csv(translated_items, csv_path)
    create_wordcloud_image(translated_items, wordcloud_path, FONT_PATH)

    html = build_report_html(translated_items, wordcloud_path, report_title)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML 보고서 저장 완료: {report_path}")

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("NYTimes RSS 자동 보고서 생성 완료\n")
        f.write(f"생성 시각: {datetime.now().isoformat()}\n")
        f.write(f"뉴스 개수: {len(translated_items)}\n")
        f.write(f"CSV: {csv_path}\n")
        f.write(f"WordCloud: {wordcloud_path}\n")
        f.write(f"Report: {report_path}\n")

    print(f"로그 저장 완료: {log_path}")

    archive_files(used_files, ARCHIVE_DIR)

    print("====================================")
    print("전체 처리 완료")
    print("====================================")
    print(f"보고서 파일: {report_path}")

    return report_path
```

---

## 11. 노트북 셀 3: 샘플 JSON 생성 함수

Make 연결 전에 테스트하고 싶다면 아래 셀을 실행합니다.

```python
def create_sample_input():
    now = datetime.now().strftime("%Y%m%d_%H%M%S")

    sample_items = [
        {
            "source": "NYTimes Technology RSS",
            "title": "A New AI Tool Is Changing How Companies Analyze Customer Data",
            "description": "Businesses are experimenting with artificial intelligence systems to summarize customer feedback and identify market trends more quickly.",
            "link": "https://www.nytimes.com/example-ai-customer-data",
            "published_at": "Wed, 10 Jun 2026 09:00:00 GMT",
            "collected_at": datetime.now().isoformat()
        },
        {
            "source": "NYTimes Technology RSS",
            "title": "Chip Makers Race to Build Faster Processors for Data Centers",
            "description": "The demand for cloud computing and AI services is increasing investment in specialized semiconductor technology.",
            "link": "https://www.nytimes.com/example-chip-makers",
            "published_at": "Wed, 10 Jun 2026 09:10:00 GMT",
            "collected_at": datetime.now().isoformat()
        },
        {
            "source": "NYTimes Technology RSS",
            "title": "Startups Use Automation to Reduce Repetitive Office Work",
            "description": "New software services are helping small teams automate reporting, email workflows and internal document processing.",
            "link": "https://www.nytimes.com/example-automation-startups",
            "published_at": "Wed, 10 Jun 2026 09:20:00 GMT",
            "collected_at": datetime.now().isoformat()
        }
    ]

    for index, item in enumerate(sample_items, start=1):
        file_path = INBOX_DIR / f"sample_nyt_{now}_{index}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(item, f, ensure_ascii=False, indent=2)
        print(f"샘플 파일 생성 완료: {file_path}")
```

샘플 파일이 필요하면 바로 아래 셀에서 실행합니다.

```python
create_sample_input()
```

---

## 12. 노트북 셀 4: 전체 실행

아래 셀을 실행하면 CSV, 워드클라우드, HTML 보고서가 한 번에 생성됩니다.

```python
report_path = run_pipeline()
report_path
```

---

## 13. 먼저 샘플 데이터로 테스트하기

Make 설정이 아직 안 되어 있어도 노트북만으로 전체 흐름을 테스트할 수 있습니다.

### 13.1 셀 실행 순서

```text
1. 셀 1: 설정값 하드코딩
2. 셀 2: 공통 함수 정의
3. 셀 3: create_sample_input() 실행
4. 셀 4: run_pipeline() 실행
```

### 13.2 실행 결과 예시

```text
설정 완료
Google Drive 기준 폴더: G:\내 드라이브\nyt_news_project
Gemini 사용 여부: True
샘플 파일 생성 완료: G:\내 드라이브\nyt_news_project\inbox\sample_nyt_20260610_090000_1.json
샘플 파일 생성 완료: G:\내 드라이브\nyt_news_project\inbox\sample_nyt_20260610_090000_2.json
샘플 파일 생성 완료: G:\내 드라이브\nyt_news_project\inbox\sample_nyt_20260610_090000_3.json
====================================
NYTimes RSS 자동 보고서 생성 시작
====================================
Google Drive 기준 폴더: G:\내 드라이브\nyt_news_project
Gemini 사용 여부: True
처리할 뉴스 개수: 3
처리할 원본 파일 개수: 3
Gemini 번역 중... (1/3) A New AI Tool Is Changing How Companies...
Gemini 번역 중... (2/3) Chip Makers Race to Build Faster Processors...
Gemini 번역 중... (3/3) Startups Use Automation to Reduce...
CSV 저장 완료
워드클라우드 저장 완료
HTML 보고서 저장 완료
archive 이동 완료
전체 처리 완료
```

### 13.3 결과 확인

Google Drive `outbox` 폴더를 확인합니다.

```text
nyt_news_project
└── outbox
    ├── nyt_translated_news_20260610_090100.csv
    ├── nyt_wordcloud_20260610_090100.png
    └── nyt_report_20260610_090100.html
```

`nyt_report_...html` 파일을 브라우저로 열어봅니다.

---

## 14. Make 시나리오 2 만들기: outbox 보고서 → Gmail 발송

두 번째 Make 시나리오는 Google Drive `outbox` 폴더에 새 HTML 보고서가 생기면 Gmail로 발송합니다.

### 14.1 시나리오 이름

```text
NYTimes Report Sender
```

### 14.2 Make 모듈 구성

```text
Google Drive - Watch files in a folder
↓
Google Drive - Download a file
↓
Gmail - Send an email
↓
Google Sheets - Add a row
```

### 14.3 Google Drive Watch 설정

모듈:

```text
Google Drive > Watch files in a folder
```

설정:

```text
Folder: 내 드라이브 / nyt_news_project / outbox
Limit: 10
```

필터 조건을 추가합니다.

```text
File name starts with nyt_report_
AND
File name ends with .html
```

이 필터를 넣는 이유는 CSV나 PNG 파일까지 이메일 발송 트리거로 잡히는 것을 막기 위해서입니다.

### 14.4 Google Drive Download 설정

모듈:

```text
Google Drive > Download a file
```

설정:

```text
File ID: Watch files 모듈에서 넘어온 File ID
```

### 14.5 Gmail 발송 설정

모듈:

```text
Gmail > Send an email
```

설정 예시:

```text
To: 본인 이메일 또는 수강생 테스트 이메일
Subject: [AI 뉴스 브리핑] NYTimes RSS 자동 보고서
Content-Type: HTML 또는 Plain text
Body:
안녕하세요.

NYTimes RSS 기반 AI 뉴스 브리핑 보고서를 전달드립니다.
첨부된 HTML 보고서를 확인해 주세요.

감사합니다.

Attachments:
Google Drive Download 모듈의 파일 데이터
```

HTML을 본문으로 바로 넣는 방식도 가능하지만, 초급 실습에서는 **첨부파일로 보내는 방식**이 가장 안정적입니다.

### 14.6 Google Sheets 로그 저장

Google Sheets에 아래와 같은 시트를 만듭니다.

시트명:

```text
email_send_log
```

컬럼:

```text
sent_at | file_name | receiver | status
```

Make 모듈:

```text
Google Sheets > Add a row
```

입력 예시:

```text
sent_at   : now
file_name : Google Drive 파일명
receiver  : 수신자 이메일
status    : sent
```

---

## 15. 최종 실행 순서

실제 시연은 다음 순서로 진행하면 됩니다.

### 15.1 1차 시연: Make 없이 Notebook만 테스트

```text
1. Google Drive for desktop 동기화 확인
2. 노트북 설정 셀 값 입력
3. create_sample_input() 셀 실행
4. run_pipeline() 셀 실행
5. outbox에 HTML 보고서 생성 확인
```

### 15.2 2차 시연: Make RSS 수집 포함

```text
1. Make Scenario 1 Run once 실행
2. Google Drive inbox에 JSON 생성 확인
3. 로컬 PC inbox 동기화 확인
4. run_pipeline() 셀 실행
5. outbox에 HTML 보고서 생성 확인
```

### 15.3 3차 시연: Gmail 발송까지 포함

```text
1. Make Scenario 2 활성화
2. 노트북에서 outbox HTML 보고서 생성
3. Make가 새 보고서 감지
4. Gmail 발송 확인
5. Google Sheets 로그 확인
```

---

## 16. 수업용 발표 멘트 예시

```text
이번 프로젝트는 RSS 뉴스 데이터를 자동으로 수집하고,
Google Drive를 데이터 저장소로 사용한 뒤,
로컬 Jupyter Notebook이 파일을 읽어 번역, 키워드 분석, 워드클라우드 생성을 수행합니다.

완성된 HTML 보고서는 다시 Google Drive에 저장되고,
Make가 해당 파일을 감지해 Gmail로 자동 발송합니다.

즉, 데이터 수집, 데이터 적재, AI 처리, 시각화, 보고서 생성, 이메일 자동화까지
하나의 실무형 데이터 파이프라인으로 연결한 프로젝트입니다.
```

---

## 17. 자주 발생하는 오류와 해결 방법

### 17.1 `DRIVE_BASE_DIR 값을 먼저 입력해 주세요` 오류

원인:

```text
노트북 설정 셀의 DRIVE_BASE_DIR 값이 비어 있음
```

해결:

```text
노트북 설정 셀에 Google Drive 동기화 폴더 경로 입력
```

예시:

```python
DRIVE_BASE_DIR = r"G:\내 드라이브\nyt_news_project"
```

---

### 17.2 inbox에 파일이 없다고 나오는 경우

원인:

```text
Make가 아직 JSON 파일을 만들지 않았거나,
Google Drive 동기화가 늦어졌을 수 있음
```

해결:

```text
1. Google Drive 웹에서 inbox 폴더 확인
2. PC의 Google Drive 폴더에도 파일이 내려왔는지 확인
3. 먼저 create_sample_input() 셀로 샘플 파일 생성 후 테스트
```

---

### 17.3 Gemini 번역 실패

원인:

```text
API Key 오류
네트워크 오류
Gemini API 사용량 제한
google-genai 설치 오류
```

해결:

```text
1. 노트북 설정 셀의 GEMINI_API_KEY 확인
2. pip install google-genai 재실행
3. USE_GEMINI = False 로 바꿔서 전체 흐름 먼저 테스트
```

---

### 17.4 워드클라우드 한글이 깨지는 경우

기본 코드는 영문 워드클라우드를 기준으로 설계했습니다.

한국어 워드클라우드를 만들고 싶다면 한글 폰트를 지정해야 합니다.

Windows 예시:

```python
FONT_PATH = r"C:\Windows\Fonts\malgun.ttf"
```

macOS 예시:

```python
FONT_PATH = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
```

다만 한국어는 공백 기준 단어 분리가 정확하지 않을 수 있으므로, 초급 실습에서는 영문 제목/요약 기반 워드클라우드를 추천합니다.

---

### 17.5 Make가 HTML 외에 PNG, CSV도 감지하는 경우

해결:

Make Scenario 2의 Google Drive Watch 뒤에 필터를 추가합니다.

```text
File name starts with nyt_report_
File name ends with .html
```

---

## 18. 과제 제출 기준 예시

수강생 제출물:

```text
1. Make Scenario 1 화면 캡처
2. Google Drive inbox JSON 파일 캡처
3. Notebook 실행 화면 캡처
4. Google Drive outbox 결과 파일 캡처
5. HTML 보고서 파일
6. Gmail 수신 결과 캡처
7. Google Sheets 발송 로그 캡처
8. 전체 프로젝트 설명 1페이지
```

평가 기준:

| 평가 항목 | 배점 |
|---|---:|
| Make RSS 수집 구성 | 15 |
| Google Drive 파일 저장 구조 | 15 |
| Notebook JSON 읽기 및 처리 | 15 |
| Gemini API 번역 활용 | 15 |
| 워드클라우드 생성 | 15 |
| HTML 보고서 생성 | 10 |
| Gmail 자동 발송 | 10 |
| 발표 및 설명 | 5 |
| 합계 | 100 |

---

## 19. 저작권 및 사용 범위 주의

이 실습에서는 NYTimes RSS의 제목, 요약, 링크만 사용합니다.

권장:

```text
- RSS 제목 사용
- RSS 요약 사용
- 원문 링크 제공
- 교육용 분석 및 시각화
```

주의:

```text
- 기사 본문 전체 크롤링 금지
- 기사 전문 번역 후 배포 금지
- 유료 기사 본문 우회 수집 금지
```

수업 프로젝트에서는 RSS에 공개된 제목과 요약을 기반으로 보고서를 만들고, 원문은 링크로 연결하는 수준이 적절합니다.

---

## 20. 확장 아이디어

기본 프로젝트가 완성되면 다음 기능을 추가할 수 있습니다.

### 20.1 카테고리별 RSS 수집

```text
Technology
Business
World
Science
Health
```

카테고리별로 워드클라우드를 따로 만들 수 있습니다.

### 20.2 Gemini 요약 보고서 추가

뉴스 목록 전체를 Gemini에 전달해서 다음 문장을 생성할 수 있습니다.

```text
오늘의 기술 뉴스 핵심 이슈 3가지를 요약해 주세요.
```

### 20.3 Google Sheets 대시보드

보고서 발송 로그뿐 아니라 키워드 빈도도 Sheets에 저장할 수 있습니다.

```text
date | keyword | count | category
```

### 20.4 매일 아침 자동 뉴스 브리핑

Make Scheduler를 매일 오전 8시에 실행하도록 설정합니다.

```text
매일 오전 8시 RSS 수집
↓
오전 8시 10분 Notebook 실행
↓
오전 8시 20분 Gmail 발송
```

단, 로컬 Notebook은 PC가 켜져 있어야 실행됩니다.
완전 자동화를 원하면 Notebook 코드를 `.py` 배치 작업이나 클라우드 서버, Cloud Run, GitHub Actions 등으로 옮길 수 있습니다.

---

## 21. 핵심 정리

이 프로젝트의 핵심은 역할 분리입니다.

```text
Make:
RSS 수집, Google Drive 저장, Gmail 발송

Google Drive:
Make와 Notebook 사이의 파일 전달 공간

Jupyter Notebook:
번역, 전처리, 워드클라우드, 보고서 생성

Gemini API:
영어 뉴스 제목/요약을 한국어로 번역하고 키워드 추출
```

초보자는 처음부터 모든 것을 완전 자동화하려고 하기보다 다음 순서로 진행하는 것이 좋습니다.

```text
1단계: 샘플 JSON으로 Notebook 보고서 생성
2단계: Make로 RSS JSON 저장
3단계: Notebook으로 실제 JSON 처리
4단계: Make로 Gmail 발송
5단계: Google Sheets 로그 추가
```

이 순서대로 진행하면 오류가 생겨도 어느 단계에서 문제가 발생했는지 쉽게 찾을 수 있습니다.

---

## 부록 A. 전체 파일 목록

최종적으로 작성해야 하는 파일은 다음 2개입니다.

```text
nyt_rss_local_processor/
│
├── nyt_rss_make_drive_gemini.ipynb
└── requirements.txt
```

---

## 부록 B. 실행 명령어 전체 모음

Windows PowerShell 기준:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

그 다음 VS Code에서 `nyt_rss_make_drive_gemini.ipynb`를 열고 셀을 순서대로 실행합니다.

macOS / Linux 기준:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

그 다음 VS Code에서 `nyt_rss_make_drive_gemini.ipynb`를 열고 셀을 순서대로 실행합니다.

---

## 부록 C. 참고 링크

- Google Drive for desktop 도움말: https://support.google.com/drive/answer/10838124
- Google Drive for desktop 설치 도움말: https://support.google.com/a/users/answer/13022292
- Gemini API Quickstart: https://ai.google.dev/gemini-api/docs/quickstart
- RSS 2.0 Specification: https://www.rssboard.org/rss-specification
- Make 공식 사이트: https://www.make.com/
