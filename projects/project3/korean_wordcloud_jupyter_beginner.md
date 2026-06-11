# 한글 워드클라우드 초보자용 주피터 노트북 예제

이 문서는 **주피터 노트북에서 그대로 따라 실행**할 수 있는 한글 워드클라우드 실습 자료입니다.

목표는 다음과 같습니다.

- 별도 데이터 파일 없이 바로 실행
- 한글이 네모(`□□□`)로 깨지지 않게 처리
- Windows / macOS / Linux / Google Colab에서 최대한 자동으로 폰트 찾기
- 초보자가 셀 단위로 복사해서 실행 가능

---

# 1. 실습 결과

최종적으로 아래와 같은 작업을 합니다.

```text
한글 문장 준비
→ 불필요한 기호 제거
→ 단어 빈도수 계산
→ 한글 폰트 자동 찾기
→ 워드클라우드 이미지 생성
→ PNG 파일로 저장
```

---

# 2. 준비물

주피터 노트북에서 새 노트북을 하나 만들고, 아래 코드를 **셀 단위로 복사해서 실행**하세요.

필요한 패키지는 다음 3개입니다.

```text
wordcloud
matplotlib
pandas
```

---

# 3. 패키지 설치

## 셀 1: 패키지 설치

주피터 노트북 첫 번째 셀에 아래 코드를 넣고 실행하세요.

```python
# 워드클라우드 실습에 필요한 패키지 설치
# 이미 설치되어 있으면 Requirement already satisfied 라고 나올 수 있습니다.

!pip install wordcloud matplotlib pandas
```

실행 후 에러가 없다면 다음 단계로 넘어갑니다.

---

# 4. 라이브러리 불러오기

## 셀 2: 라이브러리 import

```python
# 기본 라이브러리
import os
import re
from collections import Counter

# 데이터 확인용
import pandas as pd

# 시각화
import matplotlib.pyplot as plt

# 워드클라우드
from wordcloud import WordCloud
```

---

# 5. 한글 폰트 자동 찾기

한글 워드클라우드에서 가장 많이 발생하는 문제가 **한글 깨짐**입니다.

워드클라우드는 반드시 한글 폰트 파일 경로를 알아야 합니다.

예를 들어 Windows에서는 보통 아래 경로에 있습니다.

```text
C:/Windows/Fonts/malgun.ttf
```

하지만 사람마다 운영체제가 다르기 때문에, 아래 코드는 자주 쓰이는 한글 폰트를 자동으로 찾아줍니다.

## 셀 3: 한글 폰트 자동 찾기 함수

```python
def find_korean_font():
    """
    현재 PC 또는 실행 환경에서 사용할 수 있는 한글 폰트 파일을 찾는 함수입니다.

    찾는 대표 폰트:
    - Windows: 맑은 고딕
    - macOS: AppleGothic
    - Linux / Colab: NanumGothic

    반환값:
    - 폰트 파일 경로 문자열
    - 찾지 못하면 None
    """

    font_candidates = [
        # Windows
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/malgunbd.ttf",

        # macOS
        "/System/Library/Fonts/AppleGothic.ttf",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",

        # Linux / Google Colab
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    ]

    for font_path in font_candidates:
        if os.path.exists(font_path):
            return font_path

    return None


font_path = find_korean_font()

print("찾은 한글 폰트 경로:", font_path)
```

---

# 6. 폰트를 못 찾았을 때 해결 방법

위 셀을 실행했는데 결과가 아래처럼 나오면 폰트를 못 찾은 것입니다.

```text
찾은 한글 폰트 경로: None
```

이 경우 환경별로 아래 방법을 사용하세요.

---

## Windows 사용자의 경우

대부분 아래 파일이 있습니다.

```text
C:/Windows/Fonts/malgun.ttf
```

직접 지정하려면 아래 코드를 실행하세요.

```python
font_path = "C:/Windows/Fonts/malgun.ttf"
print(font_path)
```

---

## Google Colab 사용자의 경우

Colab에서는 나눔고딕을 설치하면 됩니다.

아래 셀을 실행한 뒤, 런타임을 다시 시작하지 않아도 보통 바로 사용할 수 있습니다.

```python
!apt-get update -qq
!apt-get install -y fonts-nanum

font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
print(font_path)
```

---

## macOS 사용자의 경우

대부분 아래 파일이 있습니다.

```python
font_path = "/System/Library/Fonts/AppleGothic.ttf"
print(font_path)
```

---

# 7. 예제 한글 문장 준비

별도 파일 없이 바로 실행할 수 있도록 예제 문장을 코드 안에 넣겠습니다.

주제는 **AI 뉴스 브리핑 자동화**입니다.

## 셀 4: 한글 예제 텍스트 만들기

```python
text = """
인공지능은 교육, 의료, 금융, 제조, 마케팅 분야에서 빠르게 활용되고 있습니다.
최근 기업들은 생성형 인공지능을 활용하여 뉴스 요약, 문서 작성, 고객 상담, 데이터 분석 업무를 자동화하고 있습니다.

교육 분야에서는 인공지능 튜터가 학생의 학습 수준을 분석하고 맞춤형 문제를 추천합니다.
의료 분야에서는 인공지능 모델이 영상 데이터를 분석하여 질병 진단을 보조합니다.
금융 분야에서는 인공지능이 이상 거래를 탐지하고 고객 맞춤형 금융 상품을 추천합니다.

마케팅 분야에서는 고객 리뷰, 검색 키워드, 구매 이력을 분석하여 캠페인 전략을 수립합니다.
제조 분야에서는 센서 데이터를 분석하여 설비 고장을 예측하고 품질 관리를 자동화합니다.

하지만 인공지능을 활용할 때는 개인정보 보호, 데이터 품질, 모델 오류, 저작권 문제도 함께 고려해야 합니다.
따라서 실무에서는 인공지능 결과를 그대로 사용하기보다 사람이 검토하고 보완하는 과정이 중요합니다.

인공지능 자동화의 핵심은 데이터를 수집하고, 정리하고, 분석하고, 결과를 보고서로 만드는 흐름을 이해하는 것입니다.
RSS 뉴스 수집, Gemini 요약, 워드클라우드 생성, 이메일 보고서 발송 같은 자동화도 이러한 흐름에 해당합니다.
"""

print(text[:300])
```

---

# 8. 텍스트 전처리

워드클라우드에서는 의미 없는 기호와 너무 짧은 단어를 제거하는 것이 좋습니다.

예를 들어 아래 문장에서 쉼표, 마침표 같은 기호는 제거합니다.

```text
인공지능은 교육, 의료, 금융 분야에서 활용됩니다.
```

처리 후에는 대략 아래처럼 단어만 남깁니다.

```text
인공지능은 교육 의료 금융 분야에서 활용됩니다
```

## 셀 5: 한글 텍스트 전처리

```python
# 한글, 영어, 숫자, 공백만 남기고 나머지 기호 제거
clean_text = re.sub(r"[^가-힣a-zA-Z0-9\s]", " ", text)

# 공백이 여러 개 있으면 하나로 정리
clean_text = re.sub(r"\s+", " ", clean_text)

print(clean_text[:300])
```

---

# 9. 단어 분리

정교한 형태소 분석기를 쓰면 더 좋지만, 초보자 실습에서는 설치가 복잡할 수 있습니다.

그래서 여기서는 가장 단순하게 **공백 기준으로 단어를 나누는 방식**을 사용합니다.

## 셀 6: 단어 나누기

```python
words = clean_text.split()

print(words[:30])
print("전체 단어 수:", len(words))
```

---

# 10. 불용어 제거

불용어는 분석에 큰 의미가 없는 단어입니다.

예를 들어 아래 단어들은 너무 일반적입니다.

```text
그리고, 하지만, 있습니다, 같은, 때는
```

이런 단어를 제거하면 워드클라우드가 더 보기 좋아집니다.

## 셀 7: 불용어 제거

```python
stopwords = {
    "그리고", "하지만", "또한", "따라서",
    "있습니다", "합니다", "됩니다", "있고", "있는", "같은",
    "때는", "보다", "위해", "에서", "으로", "하고",
    "분야에서는", "분야에서", "활용하여", "활용할",
    "과정이", "결과를", "문제도", "함께"
}

filtered_words = []

for word in words:
    # 너무 짧은 단어 제거
    if len(word) <= 1:
        continue

    # 불용어 제거
    if word in stopwords:
        continue

    filtered_words.append(word)

print(filtered_words[:50])
print("불용어 제거 후 단어 수:", len(filtered_words))
```

---

# 11. 단어 빈도수 계산

워드클라우드는 단어가 많이 나올수록 크게 표시합니다.

먼저 어떤 단어가 많이 나오는지 확인해 보겠습니다.

## 셀 8: 단어 빈도수 계산

```python
word_counts = Counter(filtered_words)

# 가장 많이 나온 단어 20개 확인
top20 = word_counts.most_common(20)

top20
```

---

# 12. 표로 확인하기

## 셀 9: 단어 빈도수 표 만들기

```python
df_counts = pd.DataFrame(top20, columns=["단어", "빈도수"])
df_counts
```

---

# 13. 한글 그래프 깨짐 방지 설정

워드클라우드뿐만 아니라 matplotlib 그래프 제목에서도 한글이 깨질 수 있습니다.

아래 코드는 matplotlib에서도 한글이 최대한 잘 나오도록 설정합니다.

## 셀 10: matplotlib 한글 설정

```python
# matplotlib에서 한글이 깨지지 않도록 폰트 설정
# Windows에서는 Malgun Gothic, macOS에서는 AppleGothic을 우선 사용합니다.

import platform
import matplotlib.font_manager as fm

system_name = platform.system()

if system_name == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"
elif system_name == "Darwin":  # macOS
    plt.rcParams["font.family"] = "AppleGothic"
else:
    # Linux 또는 Colab에서는 font_path를 직접 등록
    if font_path is not None:
        fm.fontManager.addfont(font_path)
        font_name = fm.FontProperties(fname=font_path).get_name()
        plt.rcParams["font.family"] = font_name

# 마이너스 기호 깨짐 방지
plt.rcParams["axes.unicode_minus"] = False

print("matplotlib 폰트 설정 완료")
```

---

# 14. 막대그래프로 단어 빈도 확인

워드클라우드를 만들기 전에 막대그래프로 단어 빈도수를 확인해 보겠습니다.

## 셀 11: 단어 빈도 막대그래프

```python
plt.figure(figsize=(10, 5))
plt.bar(df_counts["단어"], df_counts["빈도수"])
plt.title("상위 20개 단어 빈도수")
plt.xlabel("단어")
plt.ylabel("빈도수")
plt.xticks(rotation=45)
plt.show()
```

만약 여기서 한글이 깨진다면 matplotlib 폰트 설정 문제입니다.

그래도 워드클라우드는 `font_path`만 정확하면 정상 출력될 수 있습니다.

---

# 15. 워드클라우드 생성

이제 워드클라우드를 생성합니다.

가장 중요한 옵션은 `font_path`입니다.

```python
font_path=font_path
```

이 값이 없으면 한글이 깨질 가능성이 높습니다.

## 셀 12: 워드클라우드 생성

```python
if font_path is None:
    raise ValueError(
        "한글 폰트를 찾지 못했습니다. "
        "Windows는 C:/Windows/Fonts/malgun.ttf, "
        "Colab은 fonts-nanum 설치 후 NanumGothic 경로를 지정하세요."
    )

wc = WordCloud(
    font_path=font_path,          # 한글 폰트 경로
    width=900,                    # 이미지 가로 크기
    height=500,                   # 이미지 세로 크기
    background_color="white",     # 배경색
    max_words=100,                # 최대 표시 단어 수
    collocations=False            # 영어 단어 묶음 방지용 옵션
).generate_from_frequencies(word_counts)

plt.figure(figsize=(12, 7))
plt.imshow(wc)
plt.axis("off")
plt.title("한글 워드클라우드")
plt.show()
```

---

# 16. 워드클라우드 이미지 저장

보고서나 이메일에 넣으려면 이미지 파일로 저장하면 됩니다.

## 셀 13: PNG 파일로 저장

```python
output_file = "korean_wordcloud.png"

wc.to_file(output_file)

print("저장 완료:", output_file)
```

실행 후 현재 노트북 폴더에 아래 파일이 생성됩니다.

```text
korean_wordcloud.png
```

---

# 17. 전체 코드 한 번에 실행 버전

아래 코드는 위 내용을 한 번에 실행하는 통합 버전입니다.

초보자는 위 셀들을 먼저 하나씩 실행해 보고, 나중에 아래 통합 코드를 사용하면 됩니다.

```python
import os
import re
import platform
from collections import Counter

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from wordcloud import WordCloud


def find_korean_font():
    font_candidates = [
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/malgunbd.ttf",
        "/System/Library/Fonts/AppleGothic.ttf",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    ]

    for font_path in font_candidates:
        if os.path.exists(font_path):
            return font_path

    return None


font_path = find_korean_font()

if font_path is None:
    raise ValueError(
        "한글 폰트를 찾지 못했습니다. "
        "Windows는 C:/Windows/Fonts/malgun.ttf, "
        "Colab은 !apt-get install -y fonts-nanum 실행 후 "
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf 를 사용하세요."
    )


# matplotlib 한글 설정
system_name = platform.system()

if system_name == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"
elif system_name == "Darwin":
    plt.rcParams["font.family"] = "AppleGothic"
else:
    fm.fontManager.addfont(font_path)
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rcParams["font.family"] = font_name

plt.rcParams["axes.unicode_minus"] = False


# 예제 텍스트
text = """
인공지능은 교육, 의료, 금융, 제조, 마케팅 분야에서 빠르게 활용되고 있습니다.
최근 기업들은 생성형 인공지능을 활용하여 뉴스 요약, 문서 작성, 고객 상담, 데이터 분석 업무를 자동화하고 있습니다.

교육 분야에서는 인공지능 튜터가 학생의 학습 수준을 분석하고 맞춤형 문제를 추천합니다.
의료 분야에서는 인공지능 모델이 영상 데이터를 분석하여 질병 진단을 보조합니다.
금융 분야에서는 인공지능이 이상 거래를 탐지하고 고객 맞춤형 금융 상품을 추천합니다.

마케팅 분야에서는 고객 리뷰, 검색 키워드, 구매 이력을 분석하여 캠페인 전략을 수립합니다.
제조 분야에서는 센서 데이터를 분석하여 설비 고장을 예측하고 품질 관리를 자동화합니다.

하지만 인공지능을 활용할 때는 개인정보 보호, 데이터 품질, 모델 오류, 저작권 문제도 함께 고려해야 합니다.
따라서 실무에서는 인공지능 결과를 그대로 사용하기보다 사람이 검토하고 보완하는 과정이 중요합니다.

인공지능 자동화의 핵심은 데이터를 수집하고, 정리하고, 분석하고, 결과를 보고서로 만드는 흐름을 이해하는 것입니다.
RSS 뉴스 수집, Gemini 요약, 워드클라우드 생성, 이메일 보고서 발송 같은 자동화도 이러한 흐름에 해당합니다.
"""


# 전처리
clean_text = re.sub(r"[^가-힣a-zA-Z0-9\s]", " ", text)
clean_text = re.sub(r"\s+", " ", clean_text)


# 단어 분리
words = clean_text.split()


# 불용어 제거
stopwords = {
    "그리고", "하지만", "또한", "따라서",
    "있습니다", "합니다", "됩니다", "있고", "있는", "같은",
    "때는", "보다", "위해", "에서", "으로", "하고",
    "분야에서는", "분야에서", "활용하여", "활용할",
    "과정이", "결과를", "문제도", "함께"
}

filtered_words = []

for word in words:
    if len(word) <= 1:
        continue

    if word in stopwords:
        continue

    filtered_words.append(word)


# 단어 빈도수 계산
word_counts = Counter(filtered_words)


# 상위 단어 표
df_counts = pd.DataFrame(
    word_counts.most_common(20),
    columns=["단어", "빈도수"]
)

display(df_counts)


# 막대그래프
plt.figure(figsize=(10, 5))
plt.bar(df_counts["단어"], df_counts["빈도수"])
plt.title("상위 20개 단어 빈도수")
plt.xlabel("단어")
plt.ylabel("빈도수")
plt.xticks(rotation=45)
plt.show()


# 워드클라우드
wc = WordCloud(
    font_path=font_path,
    width=900,
    height=500,
    background_color="white",
    max_words=100,
    collocations=False
).generate_from_frequencies(word_counts)

plt.figure(figsize=(12, 7))
plt.imshow(wc)
plt.axis("off")
plt.title("한글 워드클라우드")
plt.show()


# 파일 저장
output_file = "korean_wordcloud.png"
wc.to_file(output_file)

print("한글 폰트 경로:", font_path)
print("워드클라우드 이미지 저장 완료:", output_file)
```

---

# 18. 자주 나는 오류와 해결 방법

## 오류 1. 한글이 네모로 나와요

원인:

```text
워드클라우드에 한글 폰트 경로가 제대로 전달되지 않음
```

해결:

Windows라면 아래처럼 직접 지정해 보세요.

```python
font_path = "C:/Windows/Fonts/malgun.ttf"
```

Colab이라면 아래 설치를 먼저 실행하세요.

```python
!apt-get update -qq
!apt-get install -y fonts-nanum
font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
```

---

## 오류 2. ModuleNotFoundError: No module named 'wordcloud'

원인:

```text
wordcloud 패키지가 설치되지 않음
```

해결:

```python
!pip install wordcloud
```

---

## 오류 3. ValueError: 한글 폰트를 찾지 못했습니다

원인:

```text
자동 폰트 탐색 후보 경로에 한글 폰트가 없음
```

해결:

내 PC의 한글 폰트 파일 경로를 직접 찾아서 지정하세요.

예:

```python
font_path = "C:/Windows/Fonts/malgun.ttf"
```

---

## 오류 4. 그래프 제목은 깨지는데 워드클라우드는 정상이에요

이 경우는 다음 둘이 서로 다르기 때문입니다.

```text
워드클라우드 폰트 설정: WordCloud(font_path=...)
matplotlib 제목 폰트 설정: plt.rcParams["font.family"]
```

워드클라우드가 정상이라면 핵심 실습은 성공입니다.

---

# 19. 실무에서 RSS 뉴스 요약 결과에 적용하는 방법

나중에 Gemini나 RSS 자동화 결과를 워드클라우드로 만들고 싶다면, 아래 부분만 바꾸면 됩니다.

기존 코드:

```python
text = """
인공지능은 교육, 의료, 금융...
"""
```

RSS 뉴스 요약 결과가 문자열로 있다면:

```python
text = rss_summary_text
```

여러 뉴스 요약을 합치고 싶다면:

```python
news_list = [
    "첫 번째 뉴스 요약 내용",
    "두 번째 뉴스 요약 내용",
    "세 번째 뉴스 요약 내용",
]

text = " ".join(news_list)
```

그 다음 전처리, 단어 빈도수 계산, 워드클라우드 생성 코드는 그대로 사용하면 됩니다.

---

# 20. 초보자용 핵심 정리

한글 워드클라우드에서 가장 중요한 코드는 아래입니다.

```python
wc = WordCloud(
    font_path=font_path,
    background_color="white"
).generate_from_frequencies(word_counts)
```

특히 이 부분이 중요합니다.

```python
font_path=font_path
```

한글이 깨진다면 대부분 이 폰트 경로 문제입니다.

따라서 먼저 아래 출력값을 꼭 확인하세요.

```python
print(font_path)
```

`None`이 나오면 한글 폰트를 찾지 못한 것입니다.

---

# 21. 추천 실습 순서

처음 실습할 때는 아래 순서로 진행하세요.

```text
1. 패키지 설치
2. 라이브러리 불러오기
3. 한글 폰트 경로 확인
4. 예제 텍스트 실행
5. 단어 빈도수 표 확인
6. 막대그래프 확인
7. 워드클라우드 생성
8. PNG 파일 저장
```

여기까지 성공하면 RSS 뉴스 자동화, Gemini 요약 결과, 이메일 보고서 자동화에도 같은 방식을 적용할 수 있습니다.
