# 이세현님 진동/CAN 데이터 분석 실습 가이드

## 0. 이 문서의 목적

이 문서는 초보자가 혼자서도 따라 할 수 있도록 작성한 **진동 데이터 분석 실습 매뉴얼**입니다.

이번 실습의 목표는 다음과 같습니다.

1. `TXT` 파일 안에 섞여 있는 **진동 데이터**와 **CAN 데이터** 구조를 이해합니다.
2. `163.txt` 파일에서 **Z+ 방향 진동 데이터**를 뽑아 그래프로 그립니다.
3. 여러 TXT 파일의 Z+ 방향 진동을 비교하여 **정상/비정상 후보 기준**을 만들어 봅니다.
4. `XLS` 엑셀 파일을 파이썬으로 읽고 그래프로 그립니다.
5. `163.txt`와 `163_하품_40도_270도_200Nm_1.XLS`를 공통 CAN 신호 기준으로 맞춰서 **시간 오프셋을 보정**합니다.
6. 보정된 데이터를 하나의 CSV 파일로 저장합니다.

---

## 1. 실험 상황 이해하기

실험에는 두 종류의 계측 데이터가 있습니다.

| 구분 | 계측자/장비 | 계측 데이터 | 특징 |
|---|---|---|---|
| A 데이터 | MVH 장비 | 진동 + CAN | 진동은 매우 고주파, CAN은 상대적으로 저주파 |
| B 데이터 | 별도 장비 | CAN + 실제 토크 등 | XLS 파일 형태 |

두 장비는 사람이 동시에 시작 버튼을 눌렀지만, 실제 시작 시점은 약간 다릅니다. 이 시간 차이를 **오프셋(offset)** 이라고 합니다.

이번 실습에서는 두 장비에 공통으로 들어 있는 CAN 신호인 `TQC_CUR`를 이용하여 TXT와 XLS의 시간축을 맞춥니다.

---

## 2. 준비 파일

실습 폴더에 아래 파일을 넣어 둡니다.

```text
115.txt
163.txt
67.txt
163_하품_40도_270도_200Nm_1.XLS
```

파일 역할은 다음과 같습니다.

| 파일 | 역할 |
|---|---|
| `115.txt` | 정상 후보 데이터 |
| `163.txt` | 비정상 후보 데이터, TXT/XLS 병합 기준 파일 |
| `67.txt` | 비정상 후보 데이터 |
| `163_하품_40도_270도_200Nm_1.XLS` | B 장비에서 계측한 XLS 파일 |

---

## 3. 권장 폴더 구조

```text
vibration_practice/
│
├─ 115.txt
├─ 163.txt
├─ 67.txt
├─ 163_하품_40도_270도_200Nm_1.XLS
│
├─ vibration_analysis_helper.py
├─ vibration_analysis_isehyeon.ipynb
│
└─ outputs/
```

초보자는 `vibration_practice`라는 폴더를 하나 만들고, 위 파일들을 모두 같은 폴더에 넣는 방식으로 시작하면 됩니다.

---

## 4. 파이썬 환경 준비

### 4.1 가상환경 만들기

Windows PowerShell 기준입니다.

```powershell
cd 원하는\폴더\경로
mkdir vibration_practice
cd vibration_practice

python -m venv .venv
.venv\Scripts\activate
```

정상적으로 활성화되면 터미널 앞쪽에 `(.venv)`가 표시됩니다.

### 4.2 필요한 라이브러리 설치

```powershell
pip install pandas numpy matplotlib xlrd openpyxl notebook tabulate
```

| 라이브러리 | 역할 |
|---|---|
| `pandas` | 표 형태 데이터 처리 |
| `numpy` | 숫자 계산 |
| `matplotlib` | 그래프 작성 |
| `xlrd` | 구형 `.XLS` 엑셀 파일 읽기 |
| `openpyxl` | `.xlsx` 엑셀 파일 읽기/쓰기 |
| `notebook` | 주피터 노트북 실행 |
| `tabulate` | 마크다운 표 출력 보조 |

### 4.3 주피터 노트북 실행

```powershell
jupyter notebook
```

브라우저가 열리면 `vibration_analysis_isehyeon.ipynb` 파일을 열어 순서대로 실행합니다.

---

## 5. TXT 파일 구조 이해하기

이번 TXT 파일은 일반적인 CSV처럼 깔끔하게 `시간, 값` 두 컬럼만 있는 형태가 아닙니다.

파일 안에 여러 채널이 함께 들어 있고, 각 채널은 대략 아래 구조로 반복됩니다.

```text
채널1_시간    채널1_값    빈칸    빈칸    채널2_시간    채널2_값    빈칸    빈칸 ...
```

즉, 각 채널은 4칸씩 차지합니다.

```text
group 0: 0번째 열 = 시간, 1번째 열 = 값
group 1: 4번째 열 = 시간, 5번째 열 = 값
group 2: 8번째 열 = 시간, 9번째 열 = 값
group 3: 12번째 열 = 시간, 13번째 열 = 값
```

그래서 특정 채널을 읽을 때는 아래 규칙을 사용합니다.

```python
time_col = group * 4
value_col = group * 4 + 1
```

예를 들어 `group = 3`이면:

```python
time_col = 12
value_col = 13
```

입니다.

---

## 6. 진동 데이터와 CAN 데이터 차이

TXT 파일에는 진동 데이터와 CAN 데이터가 같이 들어 있습니다.

| 데이터 종류 | 예시 | 샘플링 주파수 의미 |
|---|---|---|
| 진동 데이터 | X/Y/Z 방향 진동 | 1초에 매우 많은 데이터가 저장됨 |
| CAN 데이터 | 토크, 가속도, 휠속도 등 | 진동보다 적은 개수의 데이터가 저장됨 |

예를 들어 12,800Hz는 1초에 12,800개 값이 저장된다는 뜻입니다. 200Hz는 1초에 200개 값이 저장된다는 뜻입니다.

따라서 같은 30초 계측 파일이라도 진동 데이터 행 수와 CAN 데이터 행 수는 서로 다릅니다.

---

# Part A. 공통 함수 파일 만들기

아래 코드를 `vibration_analysis_helper.py`라는 이름으로 저장합니다.

이 파일은 다음 기능을 담당합니다.

- TXT 메타데이터 읽기
- TXT에서 특정 채널 읽기
- Z+ 방향 진동 채널 자동 탐색
- 진동 특징값 계산
- XLS 파일 읽기
- TXT와 XLS의 시간 오프셋 추정

## A-1. 전체 helper 코드

```python
from pathlib import Path
import pandas as pd
import numpy as np

def read_meta(path, n_lines=52, encoding="latin1"):
    lines = []
    with open(path, "r", encoding=encoding, errors="replace") as f:
        for _ in range(n_lines):
            line = f.readline()
            if not line:
                break
            lines.append(line.rstrip("\r\n").split("\t"))
    return lines

def find_data_start(path, encoding="latin1"):
    with open(path, "r", encoding=encoding, errors="replace") as f:
        for i, line in enumerate(f):
            parts = line.rstrip("\r\n").split("\t")
            try:
                float(parts[0])
                float(parts[1])
                return i
            except Exception:
                continue
    raise ValueError(f"숫자 데이터 시작 행을 찾지 못했습니다: {path}")

def parse_meta_channels(path):
    lines = read_meta(path)
    n_groups = max((len(x) for x in lines), default=0) // 4
    rows = []
    for g in range(n_groups):
        d = {"group": g, "time_col": g * 4, "value_col": g * 4 + 1}
        for parts in lines:
            key_idx = g * 4
            val_idx = g * 4 + 1
            key = parts[key_idx].strip() if key_idx < len(parts) else ""
            val = parts[val_idx].strip() if val_idx < len(parts) else ""
            if key and key not in d:
                d[key] = val
        rows.append(d)
    return pd.DataFrame(rows)

def read_channel(path, group, data_start=None, encoding="latin1"):
    if data_start is None:
        data_start = find_data_start(path, encoding=encoding)

    usecols = [group * 4, group * 4 + 1]
    df = pd.read_csv(
        path,
        sep="\t",
        header=None,
        skiprows=data_start,
        usecols=usecols,
        names=["time", "value"],
        encoding=encoding,
        engine="c",
        na_values=[""],
        on_bad_lines="skip",
    )
    df["time"] = pd.to_numeric(df["time"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna().reset_index(drop=True)

def find_channel_group(meta, keyword):
    mask = meta.astype(str).apply(
        lambda row: row.str.contains(keyword, case=False, regex=False, na=False).any(),
        axis=1,
    )
    hits = meta[mask]
    if len(hits) == 0:
        raise ValueError(f"채널을 찾지 못했습니다: {keyword}")
    return int(hits.iloc[0]["group"])

def read_z_channel(path):
    meta = parse_meta_channels(path)

    # +Z가 적힌 채널을 자동 검색합니다.
    mask = meta.astype(str).apply(
        lambda row: row.str.contains("+Z", regex=False, na=False).any(),
        axis=1,
    )
    hits = meta[mask]

    # 진동 채널이 여러 개 잡힐 경우 Vibration 채널 우선
    if len(hits) > 1 and "Channelgroup" in hits.columns:
        vib = hits[hits["Channelgroup"].astype(str).str.contains("Vibration", case=False, na=False)]
        if len(vib) > 0:
            hits = vib

    if len(hits) == 0:
        raise ValueError(f"Z+ 채널을 찾지 못했습니다: {path}")

    group = int(hits.iloc[0]["group"])
    return read_channel(path, group), hits.iloc[0].to_dict(), meta

def extract_features(df, threshold=5.0):
    t = df["time"].to_numpy()
    y = df["value"].to_numpy()
    ay = np.abs(y)

    duration = float(t[-1] - t[0]) if len(t) > 1 else 0.0
    dt = float(np.median(np.diff(t))) if len(t) > 1 else np.nan
    over = ay >= threshold

    # 기준값 이상으로 새로 진입한 횟수
    event_count = int(np.sum(over & np.r_[True, ~over[:-1]])) if len(over) else 0

    # 기준값을 넘은 만큼의 면적. 단발성 튐보다 지속적 이상을 잡는 데 유용합니다.
    excess = np.maximum(ay - threshold, 0)
    area = float(np.trapezoid(excess, t)) if len(t) > 1 else 0.0

    duration_over = float(over.sum() * dt) if len(t) > 1 else 0.0

    return {
        "n_samples": int(len(y)),
        "duration_sec": duration,
        "sample_rate_hz": float(1 / dt) if dt and dt > 0 else np.nan,
        "mean": float(np.mean(y)),
        "std": float(np.std(y)),
        "rms": float(np.sqrt(np.mean(y * y))),
        "max": float(np.max(y)),
        "min": float(np.min(y)),
        "max_abs": float(np.max(ay)),
        "p95_abs": float(np.percentile(ay, 95)),
        "p99_abs": float(np.percentile(ay, 99)),
        f"count_abs_ge_{threshold}": int(over.sum()),
        f"duration_abs_ge_{threshold}_sec": duration_over,
        f"event_count_abs_ge_{threshold}": event_count,
        f"area_over_{threshold}": area,
    }

def read_xls_clean(path):
    # .XLS 구형 엑셀 파일은 xlrd 엔진이 필요합니다.
    # 설치가 안 되어 있으면: pip install xlrd
    df = pd.read_excel(path, sheet_name=0, engine="xlrd")

    time_col = df.columns[0]
    df[time_col] = pd.to_numeric(df[time_col], errors="coerce")
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=[time_col]).reset_index(drop=True)
    return df.rename(columns={time_col: "time"})

def estimate_offset_by_xcorr(t_txt, y_txt, t_xls, y_xls, dt=0.005, max_lag=3.0):
    """
    공통 CAN 신호를 이용해 TXT와 XLS 시간 오프셋을 추정합니다.

    반환값 offset_sec의 의미:
    - XLS 시간에 offset_sec를 더하면 TXT 시간축과 더 잘 맞습니다.
    - 예: offset_sec = 1.4 이면 xls_time_aligned = xls_time + 1.4
    """
    t_txt = np.asarray(t_txt, dtype=float)
    y_txt = np.asarray(y_txt, dtype=float)
    t_xls = np.asarray(t_xls, dtype=float)
    y_xls = np.asarray(y_xls, dtype=float)

    # 각 파일의 시작 시간을 0으로 맞춘 뒤 상관계수를 비교합니다.
    t_txt0 = t_txt - t_txt[0]
    t_xls0 = t_xls - t_xls[0]

    start = max(t_txt0.min(), t_xls0.min())
    end = min(t_txt0.max(), t_xls0.max())
    grid = np.arange(start, end, dt)

    a = np.interp(grid, t_txt0, y_txt)
    b = np.interp(grid, t_xls0, y_xls)

    a = (a - np.mean(a)) / (np.std(a) + 1e-9)
    b = (b - np.mean(b)) / (np.std(b) + 1e-9)

    max_shift = int(max_lag / dt)
    lags = np.arange(-max_shift, max_shift + 1)
    corrs = []

    for lag in lags:
        if lag < 0:
            aa = a[-lag:]
            bb = b[: len(aa)]
        elif lag > 0:
            aa = a[:-lag]
            bb = b[lag:]
        else:
            aa = a
            bb = b

        corrs.append(float(np.mean(aa * bb)))

    corrs = np.array(corrs)
    best_lag = lags[int(np.argmax(corrs))] * dt

    # 위 계산에서 best_lag가 음수이면 TXT 이벤트가 XLS보다 늦게 나타난다는 뜻입니다.
    # 따라서 XLS 시간에 더해 줄 보정값은 -best_lag입니다.
    offset_sec = -float(best_lag)
    return offset_sec, float(corrs.max())
```

---

## A-2. helper 코드 핵심 설명

### `read_meta()`

```python
def read_meta(path, n_lines=52, encoding="latin1"):
```

TXT 파일 앞부분에는 실제 숫자 데이터가 아니라 채널 설명 정보가 들어 있습니다. 이 부분을 메타데이터라고 부릅니다.

이 함수는 파일 앞부분을 읽어서 채널 정보를 분석할 수 있게 해 줍니다.

`latin1` 인코딩을 쓰는 이유는 장비 파일에 특수문자가 섞여 있어도 최대한 에러 없이 읽기 위해서입니다.

### `find_data_start()`

```python
def find_data_start(path, encoding="latin1"):
```

TXT 파일은 처음부터 숫자 데이터가 나오지 않습니다. 먼저 메타데이터가 나오고, 어느 줄부터 실제 숫자 데이터가 시작됩니다.

이 함수는 첫 번째 열과 두 번째 열이 숫자로 읽히는 첫 행을 찾아 실제 데이터 시작 위치를 반환합니다.

### `parse_meta_channels()`

```python
def parse_meta_channels(path):
```

채널 이름, 방향, 샘플링 주파수, 데이터 개수 등을 표 형태로 정리합니다.

이 함수를 실행하면 `+Z` 방향 채널이 몇 번째 group인지 확인할 수 있습니다.

### `read_channel()`

```python
def read_channel(path, group, data_start=None, encoding="latin1"):
```

특정 group 번호의 시간과 값만 읽습니다.

핵심 규칙은 아래입니다.

```python
usecols = [group * 4, group * 4 + 1]
```

읽은 결과는 다음 형태의 DataFrame입니다.

| time | value |
|---:|---:|
| 0.00001 | 0.123 |
| 0.00009 | 0.125 |

### `find_channel_group()`

```python
def find_channel_group(meta, keyword):
```

메타데이터에서 특정 키워드가 들어 있는 채널을 찾아 group 번호를 반환합니다.

예를 들어:

```python
find_channel_group(meta, "TQC_CUR")
```

라고 하면 `TQC_CUR` 신호가 들어 있는 group 번호를 찾습니다.

### `read_z_channel()`

```python
def read_z_channel(path):
```

TXT 파일에서 `+Z` 방향 진동 채널을 자동으로 찾아 읽습니다.

중요한 이유는 파일마다 Z+ 채널 위치가 다를 수 있기 때문입니다.

실제 이번 데이터에서도 다음처럼 달랐습니다.

| 파일 | Z+ group | 채널 |
|---|---:|---|
| `115.txt` | 3 | C5 |
| `163.txt` | 1 | C3 |
| `67.txt` | 1 | C3 |

### `extract_features()`

```python
def extract_features(df, threshold=5.0):
```

Z+ 진동 데이터에서 정상/비정상 판단에 사용할 특징값을 계산합니다.

| 특징값 | 의미 |
|---|---|
| `max_abs` | 진동 절대값 최대 |
| `rms` | 전체 진동 에너지 수준 |
| `p95_abs` | 상위 5% 진동 수준 |
| `p99_abs` | 상위 1% 진동 수준 |
| `duration_abs_ge_5.0_sec` | 절대값 5 이상 누적 시간 |
| `event_count_abs_ge_5.0` | 절대값 5 이상으로 튄 이벤트 횟수 |
| `area_over_5.0` | 기준값 5를 초과한 면적 |

단순히 한 번 5를 넘었는지만 보면 노면 영향 때문에 오탐이 생길 수 있습니다. 그래서 **초과 시간, 초과 면적, 반복 횟수**를 같이 봅니다.

### `read_xls_clean()`

```python
def read_xls_clean(path):
```

구형 `.XLS` 파일을 읽고 숫자 데이터로 정리합니다.

### `estimate_offset_by_xcorr()`

```python
def estimate_offset_by_xcorr(t_txt, y_txt, t_xls, y_xls, dt=0.005, max_lag=3.0):
```

TXT와 XLS에 공통으로 들어 있는 CAN 신호를 이용하여 시간 오프셋을 추정합니다.

반환값 `offset_sec`의 의미는 다음과 같습니다.

```python
xls_time_aligned = xls_time + offset_sec
```

즉, XLS 시간에 이 값을 더하면 TXT 시간축과 더 잘 맞습니다.

---

# Part B. 노트북에서 단계별 실행하기

아래 코드는 주피터 노트북에서 순서대로 실행합니다.

---

## B-1. 라이브러리 불러오기

```python
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from vibration_analysis_helper import (
    parse_meta_channels,
    read_channel,
    read_z_channel,
    extract_features,
    read_xls_clean,
    find_channel_group,
    estimate_offset_by_xcorr,
)

DATA_DIR = Path(".")
```

### 설명

- `Path`는 파일 경로를 다룹니다.
- `pandas`는 표 데이터를 다룹니다.
- `numpy`는 숫자 계산을 합니다.
- `matplotlib`은 그래프를 그립니다.
- `vibration_analysis_helper`는 앞에서 만든 공통 함수 파일입니다.
- `DATA_DIR = Path(".")`는 현재 노트북 폴더를 데이터 폴더로 사용하겠다는 뜻입니다.

---

## B-2. 163 TXT 메타데이터 확인하기

```python
txt_path = DATA_DIR / "163.txt"
meta = parse_meta_channels(txt_path)

display(meta[[
    "group",
    "Channel name",
    "DOF id",
    "Point direction",
    "Sample frequency",
    "Number of lines"
]])
```

### 설명

이 단계에서는 TXT 파일 안에 어떤 채널이 들어 있는지 확인합니다.

특히 `DOF id` 또는 `Point direction`에 `+Z`가 들어 있는 채널을 찾아야 합니다.

---

## B-3. 163 TXT에서 Z+ 진동 데이터 추출하기

```python
z_163, z_channel_info, meta_163 = read_z_channel(DATA_DIR / "163.txt")

print("선택된 Z+ 채널")
print(z_channel_info)

display(z_163.head())
```

### 설명

`read_z_channel()` 함수는 `+Z`가 포함된 채널을 자동으로 찾아 줍니다.

반환값은 3개입니다.

| 변수 | 의미 |
|---|---|
| `z_163` | 163 TXT의 Z+ 진동 데이터 |
| `z_channel_info` | 선택된 Z+ 채널 정보 |
| `meta_163` | 163 TXT 전체 메타데이터 |

---

## B-4. 163 TXT의 Z+ 진동 그래프 그리기

```python
step = max(1, len(z_163) // 8000)
plot_df = z_163.iloc[::step]

plt.figure(figsize=(12, 4))
plt.plot(plot_df["time"], plot_df["value"], linewidth=1)
plt.axhline(5, linestyle="--", linewidth=1)
plt.axhline(-5, linestyle="--", linewidth=1)
plt.title("163 TXT - Z+ vibration")
plt.xlabel("Time (sec)")
plt.ylabel("Acceleration (m/s²)")
plt.grid(True, alpha=0.3)
plt.show()
```

### 설명

```python
step = max(1, len(z_163) // 8000)
```

데이터가 너무 많으면 그래프가 느려질 수 있습니다. 그래서 그래프에는 일부 샘플만 표시합니다.

```python
plt.axhline(5, linestyle="--", linewidth=1)
plt.axhline(-5, linestyle="--", linewidth=1)
```

`+5`, `-5` 기준선을 표시합니다.

---

## B-5. 163 TXT 안의 CAN 신호 그래프 그리기

```python
for keyword, ylabel in [
    ("TQC_CUR", "Torque (Nm)"),
    ("LONG_ACCEL", "Acceleration (m/s²)")
]:
    group = find_channel_group(meta_163, keyword)
    can_df = read_channel(DATA_DIR / "163.txt", group)

    step = max(1, len(can_df) // 8000)
    plot_df = can_df.iloc[::step]

    plt.figure(figsize=(12, 4))
    plt.plot(plot_df["time"], plot_df["value"], linewidth=1)
    plt.title(f"163 TXT - CAN {keyword}")
    plt.xlabel("Time (sec)")
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.show()
```

### 설명

TXT 안에는 진동뿐 아니라 CAN 데이터도 함께 들어 있습니다. 여기서는 `TQC_CUR`와 `LONG_ACCEL`을 찾아 그래프로 그립니다.

---

# Part C. 여러 TXT 파일의 Z+ 진동 비교

## C-1. 여러 파일에서 Z+ 특징값 계산하기

```python
txt_files = ["115.txt", "163.txt", "67.txt"]

z_data = {}
feature_rows = []

for fname in txt_files:
    z_df, ch_info, meta = read_z_channel(DATA_DIR / fname)
    z_data[fname] = z_df

    features = extract_features(z_df, threshold=5.0)
    features.update({
        "file": fname,
        "z_group": ch_info.get("group"),
        "channel_name": ch_info.get("Channel name"),
        "dof_id": ch_info.get("DOF id"),
    })
    feature_rows.append(features)

feature_df = pd.DataFrame(feature_rows)

feature_df["rule_result"] = np.where(
    (feature_df["duration_abs_ge_5.0_sec"] >= 0.05) |
    (feature_df["area_over_5.0"] >= 0.02),
    "비정상 후보",
    "정상 후보",
)

display(feature_df)
```

### 설명

이 코드는 여러 TXT 파일을 반복하면서 다음 작업을 수행합니다.

1. Z+ 진동 채널을 자동으로 찾습니다.
2. Z+ 진동 데이터를 읽습니다.
3. 특징값을 계산합니다.
4. 임시 룰로 정상/비정상 후보를 판정합니다.

현재 임시 룰은 다음과 같습니다.

```text
5 이상 누적 시간이 0.05초 이상이거나
5 초과 면적이 0.02 이상이면
비정상 후보
```

---

## C-2. 현재 데이터 기준 결과

| file    |   z_group | channel_name   | dof_id    |   sample_rate_hz |   max_abs |      rms |   p99_abs |   duration_abs_ge_5.0_sec |   event_count_abs_ge_5.0 |   area_over_5.0 | rule_result   |
|:--------|----------:|:---------------|:----------|-----------------:|----------:|---------:|----------:|--------------------------:|-------------------------:|----------------:|:--------------|
| 115.txt |         3 | C5             | #1_CPL:+Z |            12800 |   2.51831 | 0.456608 |   1.27808 |                  0        |                        0 |       0         | 정상 후보     |
| 163.txt |         1 | C3             | #1_CPL:+Z |            12800 |   9.65332 | 0.880607 |   3.69629 |                  0.117656 |                      546 |       0.0975155 | 비정상 후보   |
| 67.txt  |         1 | C3             | #1_CPL:+Z |            12800 |  10.4602  | 1.29067  |   5.32715 |                  0.429766 |                     1510 |       0.585118  | 비정상 후보   |

해석하면 다음과 같습니다.

- `115.txt`는 기준값 5를 넘지 않아 정상 후보입니다.
- `163.txt`는 기준값 5 이상 구간이 반복적으로 나타나 비정상 후보입니다.
- `67.txt`는 기준값 5 이상 구간이 더 많이 나타나 비정상 후보입니다.

---

## C-3. 여러 TXT 파일 Z+ 진동 비교 그래프

```python
plt.figure(figsize=(12, 5))

for fname, z_df in z_data.items():
    step = max(1, len(z_df) // 8000)
    plot_df = z_df.iloc[::step]
    plt.plot(plot_df["time"], plot_df["value"], linewidth=1, label=fname)

plt.axhline(5, linestyle="--", linewidth=1)
plt.axhline(-5, linestyle="--", linewidth=1)
plt.title("Z+ vibration comparison")
plt.xlabel("Time (sec)")
plt.ylabel("Acceleration (m/s²)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

생성된 예시 그래프:

![Z+ 진동 비교](vibration_analysis_outputs/z_plus_comparison.png)

---

# Part D. 정상/비정상 기준 잡는 방법

## D-1. 단순 기준값 방식

가장 쉬운 기준은 다음입니다.

```text
Z+ 진동 절대값이 5 이상이면 비정상
```

하지만 이 방식은 오탐이 생길 수 있습니다.

예를 들어 노면이 거칠거나 순간 충격이 있으면 정상 제품도 잠깐 5를 넘을 수 있습니다.

## D-2. 더 안정적인 기준

따라서 다음 지표를 함께 보는 것이 좋습니다.

| 지표 | 의미 | 장점 |
|---|---|---|
| `max_abs` | 가장 크게 튄 값 | 직관적 |
| `rms` | 전체 진동 에너지 | 전체 흔들림 수준 반영 |
| `p99_abs` | 상위 1% 진동 수준 | 극단값 영향 감소 |
| 초과 누적시간 | 기준값 이상 지속 시간 | 순간 튐과 지속 이상 구분 |
| 이벤트 횟수 | 기준값 이상 발생 횟수 | 반복성 확인 |
| 초과 면적 | 초과 크기와 시간을 함께 반영 | 크기와 지속시간 동시 반영 |

## D-3. 머신러닝은 언제 필요한가?

현재처럼 파일 수가 적을 때는 머신러닝보다 룰 기반 분석이 적합합니다.

머신러닝을 하려면 최소한 다음이 필요합니다.

| 필요 항목 | 설명 |
|---|---|
| 정상 데이터 | 여러 조건의 정상 계측 파일 |
| 비정상 데이터 | 여러 조건의 비정상 계측 파일 |
| 라벨 | 각 파일이 정상인지 비정상인지 정답 표시 |
| 특징값 | RMS, p99, 초과시간, 초과면적 등 |

추천 순서는 다음입니다.

```text
1단계: 룰 기반
2단계: 특징값 기반 간단한 분류 모델
3단계: 주파수 분석, FFT 분석 추가
4단계: 딥러닝 기반 이상 탐지
```

---

# Part E. XLS 파일 그래프화

## E-1. XLS 파일 읽기

```python
xls_path = DATA_DIR / "163_하품_40도_270도_200Nm_1.XLS"
xls_df = read_xls_clean(xls_path)

display(xls_df.head())
display(xls_df.notna().sum())
```

### 설명

`read_xls_clean()` 함수는 구형 XLS 파일을 읽고 숫자형으로 변환합니다.

빈 값이 많을 수 있으므로, 각 신호를 그래프로 그릴 때는 `dropna()`를 사용합니다.

## E-2. XLS 주요 신호 그래프 그리기

```python
for col in ["LONG_ACCEL[m/s^2]", "Torque[Nm]", "TQC_CUR[Nm]"]:
    if col in xls_df.columns:
        d = xls_df[["time", col]].dropna()

        plt.figure(figsize=(12, 4))
        plt.plot(d["time"], d[col], linewidth=1)
        plt.title(f"163 XLS - {col}")
        plt.xlabel("Time (sec)")
        plt.ylabel(col)
        plt.grid(True, alpha=0.3)
        plt.show()
```

## E-3. 휠 속도 그래프 그리기

```python
wheel_cols = [c for c in xls_df.columns if c.startswith("WHL_SPD")]

plt.figure(figsize=(12, 4))
for col in wheel_cols:
    d = xls_df[["time", col]].dropna()
    plt.plot(d["time"], d[col], linewidth=1, label=col)

plt.title("163 XLS - Wheel speeds")
plt.xlabel("Time (sec)")
plt.ylabel("km/h")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

---

# Part F. TXT와 XLS 오프셋 보정

## F-1. 오프셋 보정이 필요한 이유

두 장비는 동시에 계측을 시작했지만, 사람이 손으로 시작했기 때문에 약간의 시간 차이가 발생합니다.

따라서 TXT와 XLS를 단순히 시간 0초부터 겹치면 정확히 맞지 않을 수 있습니다.

이때 두 파일에 공통으로 들어 있는 CAN 신호를 기준으로 두 신호가 가장 잘 겹치는 시간 차이를 찾습니다.

이번 실습에서는 `TQC_CUR`를 기준으로 사용했습니다.

---

## F-2. 오프셋 계산 코드

```python
txt_tqc_group = find_channel_group(meta_163, "TQC_CUR")
txt_tqc = read_channel(DATA_DIR / "163.txt", txt_tqc_group)

xls_tqc = xls_df[["time", "TQC_CUR[Nm]"]].dropna()

offset_sec, corr = estimate_offset_by_xcorr(
    txt_tqc["time"].to_numpy(),
    txt_tqc["value"].to_numpy(),
    xls_tqc["time"].to_numpy(),
    xls_tqc["TQC_CUR[Nm]"].to_numpy(),
    dt=0.005,
    max_lag=3.0,
)

print(f"XLS 시간에 더할 오프셋: {offset_sec:.3f}초")
print(f"정렬 후 상관계수: {corr:.3f}")
```

### 설명

```python
txt_tqc_group = find_channel_group(meta_163, "TQC_CUR")
```

TXT에서 `TQC_CUR` 채널을 찾습니다.

```python
xls_tqc = xls_df[["time", "TQC_CUR[Nm]"]].dropna()
```

XLS에서 `TQC_CUR` 신호를 가져옵니다.

```python
offset_sec, corr = estimate_offset_by_xcorr(...)
```

상호상관 방식으로 가장 잘 맞는 시간 차이를 계산합니다.

---

## F-3. 현재 오프셋 계산 결과

- XLS 시간에 더할 보정값: **1.415초**
- 정렬 후 상관계수: **0.993**

```python
xls_time_aligned = xls_time + 1.415
```

즉, XLS 시간에 약 1.415초를 더하면 TXT 시간축과 잘 맞는 것으로 추정되었습니다.

---

## F-4. 시간축 보정 후 병합하기

```python
grid = pd.DataFrame({
    "time": np.arange(
        0,
        min(z_163["time"].max(), (xls_df["time"] + offset_sec).max()),
        0.005,
    )
})

grid["txt_z_plus"] = np.interp(
    grid["time"],
    z_163["time"],
    z_163["value"]
)

grid["txt_tqc_cur"] = np.interp(
    grid["time"],
    txt_tqc["time"],
    txt_tqc["value"]
)

xls_tqc_aligned = xls_tqc.copy()
xls_tqc_aligned["time_aligned"] = xls_tqc_aligned["time"] + offset_sec

grid["xls_tqc_cur_aligned"] = np.interp(
    grid["time"],
    xls_tqc_aligned["time_aligned"],
    xls_tqc_aligned["TQC_CUR[Nm]"],
)

display(grid.head())
```

### 설명

```python
np.arange(..., 0.005)
```

0.005초 간격의 공통 시간축을 만듭니다.

```python
np.interp(...)
```

서로 다른 시간 간격으로 저장된 데이터를 공통 시간축에 맞춥니다.

쉽게 말해, 진동 데이터와 CAN 데이터가 서로 다른 시간 간격을 가지고 있기 때문에 같은 시간표 위에 올려놓는 과정입니다.

---

## F-5. 보정 결과 그래프

```python
plt.figure(figsize=(12, 4))
plt.plot(grid["time"], grid["txt_tqc_cur"], label="TXT TQC_CUR", linewidth=1)
plt.plot(
    grid["time"],
    grid["xls_tqc_cur_aligned"],
    label=f"XLS TQC_CUR aligned (+{offset_sec:.3f}s)",
    linewidth=1
)
plt.title("TXT/XLS offset correction using common CAN signal")
plt.xlabel("TXT time axis (sec)")
plt.ylabel("TQC_CUR (Nm)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

생성된 예시 그래프:

![오프셋 보정 그래프](vibration_analysis_outputs/merged_163_offset_corrected_tqc.png)

그래프에서 두 선이 거의 겹치면 오프셋 보정이 잘 된 것입니다.

---

## F-6. 병합 결과 CSV 저장

```python
grid.to_csv(
    "merged_163_txt_xls_offset_corrected.csv",
    index=False,
    encoding="utf-8-sig"
)

feature_df.to_csv(
    "z_feature_summary.csv",
    index=False,
    encoding="utf-8-sig"
)
```

### 설명

```python
index=False
```

DataFrame의 행 번호를 CSV에 저장하지 않습니다.

```python
encoding="utf-8-sig"
```

엑셀에서 한글이 깨지지 않도록 저장합니다.

---

# Part G. 전체 실행 코드

아래 코드는 노트북에서 한 번에 실행할 수 있는 전체 흐름입니다.

단, 먼저 `vibration_analysis_helper.py`가 같은 폴더에 있어야 합니다.

```python
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from vibration_analysis_helper import (
    parse_meta_channels,
    read_channel,
    read_z_channel,
    extract_features,
    read_xls_clean,
    find_channel_group,
    estimate_offset_by_xcorr,
)

DATA_DIR = Path(".")

# 1. 여러 TXT 파일의 Z+ 특징값 계산
txt_files = ["115.txt", "163.txt", "67.txt"]
z_data = {}
feature_rows = []

for fname in txt_files:
    z_df, ch_info, meta = read_z_channel(DATA_DIR / fname)
    z_data[fname] = z_df

    features = extract_features(z_df, threshold=5.0)
    features.update({
        "file": fname,
        "z_group": ch_info.get("group"),
        "channel_name": ch_info.get("Channel name"),
        "dof_id": ch_info.get("DOF id"),
    })
    feature_rows.append(features)

feature_df = pd.DataFrame(feature_rows)
feature_df["rule_result"] = np.where(
    (feature_df["duration_abs_ge_5.0_sec"] >= 0.05) |
    (feature_df["area_over_5.0"] >= 0.02),
    "비정상 후보",
    "정상 후보",
)

display(feature_df)

# 2. Z+ 비교 그래프
plt.figure(figsize=(12, 5))
for fname, z_df in z_data.items():
    step = max(1, len(z_df) // 8000)
    plot_df = z_df.iloc[::step]
    plt.plot(plot_df["time"], plot_df["value"], linewidth=1, label=fname)

plt.axhline(5, linestyle="--", linewidth=1)
plt.axhline(-5, linestyle="--", linewidth=1)
plt.title("Z+ vibration comparison")
plt.xlabel("Time (sec)")
plt.ylabel("Acceleration (m/s²)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()

# 3. 163 TXT Z+ 데이터
z_163, z_channel_info, meta_163 = read_z_channel(DATA_DIR / "163.txt")

# 4. XLS 읽기
xls_df = read_xls_clean(DATA_DIR / "163_하품_40도_270도_200Nm_1.XLS")

# 5. XLS 주요 신호 그래프
for col in ["LONG_ACCEL[m/s^2]", "Torque[Nm]", "TQC_CUR[Nm]"]:
    if col in xls_df.columns:
        d = xls_df[["time", col]].dropna()
        plt.figure(figsize=(12, 4))
        plt.plot(d["time"], d[col], linewidth=1)
        plt.title(f"163 XLS - {col}")
        plt.xlabel("Time (sec)")
        plt.ylabel(col)
        plt.grid(True, alpha=0.3)
        plt.show()

# 6. TXT와 XLS 공통 CAN 신호로 오프셋 추정
txt_tqc_group = find_channel_group(meta_163, "TQC_CUR")
txt_tqc = read_channel(DATA_DIR / "163.txt", txt_tqc_group)
xls_tqc = xls_df[["time", "TQC_CUR[Nm]"]].dropna()

offset_sec, corr = estimate_offset_by_xcorr(
    txt_tqc["time"].to_numpy(),
    txt_tqc["value"].to_numpy(),
    xls_tqc["time"].to_numpy(),
    xls_tqc["TQC_CUR[Nm]"].to_numpy(),
    dt=0.005,
    max_lag=3.0,
)

print(f"XLS 시간에 더할 오프셋: {offset_sec:.3f}초")
print(f"정렬 후 상관계수: {corr:.3f}")

# 7. 공통 시간축 생성 후 병합
grid = pd.DataFrame({
    "time": np.arange(
        0,
        min(z_163["time"].max(), (xls_df["time"] + offset_sec).max()),
        0.005,
    )
})

grid["txt_z_plus"] = np.interp(grid["time"], z_163["time"], z_163["value"])
grid["txt_tqc_cur"] = np.interp(grid["time"], txt_tqc["time"], txt_tqc["value"])

xls_tqc_aligned = xls_tqc.copy()
xls_tqc_aligned["time_aligned"] = xls_tqc_aligned["time"] + offset_sec

grid["xls_tqc_cur_aligned"] = np.interp(
    grid["time"],
    xls_tqc_aligned["time_aligned"],
    xls_tqc_aligned["TQC_CUR[Nm]"],
)

# 8. 보정 결과 그래프
plt.figure(figsize=(12, 4))
plt.plot(grid["time"], grid["txt_tqc_cur"], label="TXT TQC_CUR", linewidth=1)
plt.plot(
    grid["time"],
    grid["xls_tqc_cur_aligned"],
    label=f"XLS TQC_CUR aligned (+{offset_sec:.3f}s)",
    linewidth=1
)
plt.title("TXT/XLS offset correction using common CAN signal")
plt.xlabel("TXT time axis (sec)")
plt.ylabel("TQC_CUR (Nm)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()

# 9. 결과 저장
feature_df.to_csv("z_feature_summary.csv", index=False, encoding="utf-8-sig")
grid.to_csv("merged_163_txt_xls_offset_corrected.csv", index=False, encoding="utf-8-sig")
```

---

# Part H. 결과 파일 설명

| 파일 | 설명 |
|---|---|
| `z_feature_summary.csv` | TXT 파일별 Z+ 진동 특징값 요약 |
| `merged_163_txt_xls_offset_corrected.csv` | TXT/XLS 시간 보정 후 병합 데이터 |
| `163_txt_channel_metadata.csv` | 163 TXT의 채널 메타정보 |
| `offset_estimation_163.csv` | TXT/XLS 오프셋 계산 결과 |

## H-1. `z_feature_summary.csv` 주요 컬럼

| 컬럼 | 의미 |
|---|---|
| `file` | 파일명 |
| `z_group` | Z+ 채널 group 번호 |
| `sample_rate_hz` | 샘플링 주파수 |
| `max_abs` | 진동 절대값 최대 |
| `rms` | 진동 에너지 수준 |
| `p99_abs` | 상위 1% 진동 절대값 |
| `duration_abs_ge_5.0_sec` | 5 이상 누적 시간 |
| `event_count_abs_ge_5.0` | 5 이상 이벤트 횟수 |
| `area_over_5.0` | 5 초과 면적 |
| `rule_result` | 임시 정상/비정상 후보 판정 |

## H-2. `merged_163_txt_xls_offset_corrected.csv` 주요 컬럼

| 컬럼 | 의미 |
|---|---|
| `time` | 공통 시간축 |
| `txt_z_plus` | TXT에서 추출한 Z+ 진동 |
| `txt_tqc_cur` | TXT의 TQC_CUR |
| `xls_tqc_cur_aligned` | 시간 보정된 XLS의 TQC_CUR |
| `xls_torque_aligned` | 시간 보정된 XLS의 실제 토크, 있는 경우 |

---

# Part I. 자주 발생하는 오류와 해결 방법

## I-1. `ModuleNotFoundError: No module named 'xlrd'`

구형 `.XLS` 파일을 읽는 라이브러리가 설치되지 않은 경우입니다.

```powershell
pip install xlrd
```

## I-2. `FileNotFoundError`

데이터 파일이 노트북과 같은 폴더에 없는 경우입니다.

아래 파일들이 같은 폴더에 있는지 확인합니다.

```text
115.txt
163.txt
67.txt
163_하품_40도_270도_200Nm_1.XLS
vibration_analysis_helper.py
```

## I-3. 한글 파일명 때문에 오류가 나는 경우

파일명을 영어로 바꿔서 테스트합니다.

```text
163_하품_40도_270도_200Nm_1.XLS
```

를 아래처럼 바꿉니다.

```text
163_data.xls
```

코드도 같이 수정합니다.

```python
xls_df = read_xls_clean(DATA_DIR / "163_data.xls")
```

## I-4. 그래프 한글이 깨지는 경우

Windows에서는 노트북 앞부분에 아래 코드를 추가합니다.

```python
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
```

Mac에서는 아래처럼 시도합니다.

```python
plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False
```

---

# Part J. 수업 진행용 설명 스크립트

이번 데이터는 차량에서 계측한 진동 데이터와 CAN 데이터입니다. TXT 파일에는 진동과 CAN이 함께 들어 있고, XLS 파일에는 다른 장비에서 계측한 CAN과 실제 토크 값이 들어 있습니다.

두 장비는 동시에 계측을 시작했지만 사람 손으로 시작했기 때문에 약간의 시간 차이가 있습니다. 그래서 이번 실습에서는 먼저 TXT에서 Z+ 방향 진동을 뽑아 그래프를 그리고, 정상/비정상 후보 기준을 만들어 본 뒤, TXT와 XLS의 공통 CAN 신호를 기준으로 시간 오프셋을 보정합니다.

핵심은 세 가지입니다.

1. 장비 데이터는 일반 CSV처럼 깔끔하지 않을 수 있으므로 파일 구조를 먼저 이해해야 합니다.
2. 진동 이상 판단은 한 번 튄 값만 보면 안 되고, 초과 시간, 반복 횟수, 초과 면적을 함께 봐야 합니다.
3. 두 장비 데이터를 합칠 때는 공통 신호를 기준으로 시간축을 맞춰야 합니다.

---

# Part K. 다음 확장 과제

데이터가 더 많이 쌓이면 다음 작업을 추가할 수 있습니다.

1. 정상/비정상 라벨 데이터셋 만들기
2. 파일별 특징값 자동 계산
3. 정상/비정상 분류 모델 만들기
4. 새 TXT 파일이 들어오면 자동 판정하기
5. FFT 기반 주파수 분석 추가하기
6. Streamlit 또는 Dash로 대시보드 만들기

머신러닝용 특징값 테이블 예시는 다음과 같습니다.

| file | rms | max_abs | p99_abs | duration_over_5 | event_count | area_over_5 | label |
|---|---:|---:|---:|---:|---:|---:|---|
| 115.txt | 0.46 | 2.52 | 1.28 | 0.00 | 0 | 0.00 | 정상 |
| 163.txt | 0.88 | 9.65 | 3.70 | 0.12 | 546 | 0.10 | 비정상 |
| 67.txt | 1.29 | 10.46 | 5.33 | 0.43 | 1510 | 0.59 | 비정상 |

---

# Part L. 최종 정리

이번 실습에서 완성한 작업은 다음과 같습니다.

```text
TXT 파일 구조 분석
+Z 진동 채널 자동 추출
Z+ 진동 그래프 작성
CAN 신호 그래프 작성
정상/비정상 후보 특징값 계산
XLS 파일 그래프화
TXT/XLS 공통 CAN 신호 기반 오프셋 추정
시간축 보정
병합 CSV 저장
```

현재 결과에서는 `115.txt`는 정상 후보, `163.txt`와 `67.txt`는 비정상 후보로 분류되었습니다.

또한 `163.txt`와 `163 XLS`의 시간 오프셋은 약 `+1.415초`로 추정되었고, 보정 후 공통 CAN 신호의 상관계수는 약 `0.993`으로 높게 나타났습니다.

향후 새 데이터가 들어오면 아래 흐름으로 자동화할 수 있습니다.

```text
새 TXT 파일 입력
→ Z+ 채널 자동 추출
→ 특징값 계산
→ 정상/비정상 후보 판정
→ XLS와 공통 CAN 기준 시간 보정
→ 통합 분석 데이터 생성
```
