import re
import os
from pathlib import Path

os.environ.setdefault("USE_TF", "0")

import pandas as pd
import torch
from bs4 import BeautifulSoup
from chronos import ChronosPipeline

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "fruits_data"
CRAWLED_PRICE_PATH = DATA_DIR / "garak_apple_prices.csv"
OUTPUT_PATH = PROJECT_ROOT / "rag_docs" / "apple_price_forecast_chronos_mini.md"

MODEL_NAME = "amazon/chronos-t5-mini"
PREDICTION_LENGTH = 30
NUM_SAMPLES = 100
FORECAST_GRADES = ("상", "중")
SIZE_MARKET_GRADE = {
    "대": "상",
    "중": "중",
}
QUALITY_PRICE_MULTIPLIER = {
    "상": 1.12,
    "중": 1.00,
    "하": 0.82,
}


def parse_price(value: str) -> int | None:
    digits = re.sub(r"[^0-9]", "", value)
    return int(digits) if digits else None


def parse_date(value: str) -> pd.Timestamp | None:
    match = re.search(r"(\d{2})\.(\d{2})\.(\d{2})", value)
    if not match:
        return None

    year, month, day = match.groups()
    return pd.Timestamp(year=2000 + int(year), month=int(month), day=int(day))


def load_apple_price_series(grade: str) -> pd.DataFrame:
    if CRAWLED_PRICE_PATH.exists():
        frame = pd.read_csv(CRAWLED_PRICE_PATH)
        frame["date"] = pd.to_datetime(frame["date"])
        if "price_per_kg" not in frame.columns:
            raise ValueError(f"{CRAWLED_PRICE_PATH} must contain price_per_kg")

        filtered = frame[
            (frame["grade"] == grade)
            & frame["price_per_kg"].notna()
        ].copy()
        if filtered.empty:
            raise ValueError(f"No {grade} grade price rows found in {CRAWLED_PRICE_PATH}")

        filtered["price"] = filtered["price_per_kg"].round().astype(int)
        filtered["source"] = CRAWLED_PRICE_PATH.name
        return (
            filtered[["date", "price", "source"]]
            .groupby("date", as_index=False)
            .agg({"price": "mean", "source": "first"})
            .assign(price=lambda data: data["price"].round().astype(int))
            .sort_values("date")
            .reset_index(drop=True)
        )

    rows: list[dict] = []
    for path in sorted(DATA_DIR.glob("*.xls")):
        soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
        tables = soup.find_all("table")
        if not tables:
            continue

        for tr in tables[-1].find_all("tr"):
            cells = [cell.get_text(" ", strip=True) for cell in tr.find_all(["th", "td"])]
            if len(cells) < 2 or cells[0] == "날짜":
                continue

            date = parse_date(cells[0])
            price = parse_price(cells[1])
            if date is None or price is None:
                continue

            rows.append({"date": date, "price": price, "source": path.name})

    if not rows:
        raise ValueError(f"No apple price rows found in {DATA_DIR}")

    frame = pd.DataFrame(rows)
    return frame.drop_duplicates("date").sort_values("date").reset_index(drop=True)


def load_pipeline() -> ChronosPipeline:
    return ChronosPipeline.from_pretrained(
        MODEL_NAME,
        device_map="cpu",
        dtype=torch.float32,
    )


def forecast_prices(series: pd.Series, pipeline: ChronosPipeline) -> pd.DataFrame:
    context = torch.tensor(series.to_numpy(dtype="float32"))
    forecast = pipeline.predict(
        context,
        prediction_length=PREDICTION_LENGTH,
        num_samples=NUM_SAMPLES,
    )
    samples = forecast[0]
    quantiles = torch.quantile(samples, torch.tensor([0.1, 0.5, 0.9]), dim=0)

    return pd.DataFrame(
        {
            "forecast_step": range(1, PREDICTION_LENGTH + 1),
            "p10": quantiles[0].round().to(torch.int64).tolist(),
            "median": quantiles[1].round().to(torch.int64).tolist(),
            "p90": quantiles[2].round().to(torch.int64).tolist(),
        }
    )


def business_days_after(last_date: pd.Timestamp, periods: int) -> pd.DatetimeIndex:
    return pd.bdate_range(last_date + pd.Timedelta(days=1), periods=periods)


def trend_label(first_value: int, last_value: int) -> str:
    change_rate = (last_value - first_value) / first_value
    if change_rate >= 0.03:
        return "상승 가능성이 있는 흐름"
    if change_rate <= -0.03:
        return "하락 가능성이 있는 흐름"
    return "큰 방향성보다는 보합권 흐름"


def round_price(value: float) -> int:
    return int(round(value / 100) * 100)


def prepare_forecast(grade: str, history: pd.DataFrame, forecast: pd.DataFrame) -> dict:
    dates = business_days_after(history["date"].max(), len(forecast))
    forecast = forecast.copy()
    forecast["date"] = dates
    forecast["change_from_latest_percent"] = (
        (forecast["median"] - int(history["price"].iloc[-1]))
        / int(history["price"].iloc[-1])
        * 100
    ).round(2)

    latest_price = int(history["price"].iloc[-1])
    recent_20_mean = int(round(history["price"].tail(20).mean()))
    forecast_mean = int(round(forecast["median"].mean()))
    low_forecast = int(forecast["p10"].min())
    high_forecast = int(forecast["p90"].max())
    label = trend_label(int(forecast["median"].iloc[0]), int(forecast["median"].iloc[-1]))

    return {
        "grade": grade,
        "history": history,
        "forecast": forecast,
        "latest_price": latest_price,
        "recent_20_mean": recent_20_mean,
        "forecast_mean": forecast_mean,
        "low_forecast": low_forecast,
        "high_forecast": high_forecast,
        "label": label,
    }


def forecast_table_rows(forecast: pd.DataFrame) -> str:
    return "\n".join(
        "| {date} | {median:,} | {p10:,} | {p90:,} | {change:+.2f}% |".format(
            date=row.date.strftime("%Y-%m-%d"),
            median=int(row.median),
            p10=int(row.p10),
            p90=int(row.p90),
            change=float(row.change_from_latest_percent),
        )
        for row in forecast.itertuples(index=False)
    )


def derived_price_rows(forecasts: dict[str, dict]) -> str:
    rows = []
    for size_class, market_grade in SIZE_MARKET_GRADE.items():
        base_price = forecasts[market_grade]["forecast_mean"]
        for quality_grade, multiplier in QUALITY_PRICE_MULTIPLIER.items():
            rows.append(
                "| {size}과 | {quality} | 가락 {market} 예측 평균 | {base:,} | {multiplier:.2f} | {price:,} |".format(
                    size=size_class,
                    quality=quality_grade,
                    market=market_grade,
                    base=base_price,
                    multiplier=multiplier,
                    price=round_price(base_price * multiplier),
                )
            )
    return "\n".join(rows)


def forecast_sections(forecasts: dict[str, dict]) -> str:
    sections = []
    for grade in FORECAST_GRADES:
        result = forecasts[grade]
        history = result["history"]
        sections.append(
            f"""## 가락시장 {grade} 등급 예측
- 관측 기간: {history['date'].min().strftime('%Y-%m-%d')} ~ {history['date'].max().strftime('%Y-%m-%d')}
- 관측치 수: {len(history):,}개
- 최신 관측 가격: {result['latest_price']:,}원/kg
- 최근 20개 관측 평균: {result['recent_20_mean']:,}원/kg
- 30영업일 중앙값 평균: {result['forecast_mean']:,}원/kg
- 예측 참고 범위: {result['low_forecast']:,}원/kg ~ {result['high_forecast']:,}원/kg
- 전체 흐름 판단: {result['label']}

| 예측일 | 중앙값 예상가(원/kg) | 낮은 경우 p10 | 높은 경우 p90 | 최신가 대비 |
|---|---:|---:|---:|---:|
{forecast_table_rows(result['forecast'])}
"""
        )
    return "\n\n".join(sections)


def write_markdown(forecasts: dict[str, dict]) -> None:
    min_date = min(result["history"]["date"].min() for result in forecasts.values())
    max_date = max(result["history"]["date"].max() for result in forecasts.values())

    content = f"""# 사과 시세 예측 RAG 문서

## 데이터 개요
- 품목: 사과
- 세부 기준: 가락시장 사과, 상/중 등급, kg당 환산 가격
- 원천 파일 위치: `fruits_data/garak_apple_prices.csv` 우선 사용, 없으면 `fruits_data/*.xls`
- 관측 기간: {min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}
- 기준 해석: 가락시장 상/중 등급은 우리 시스템의 상품성 등급이 아니라 대과/중과 기준 시세로 사용한다.
- 가격 산정: 대과는 가락시장 상 등급 예측가, 중과는 가락시장 중 등급 예측가를 기준으로 삼고, 우리 상품성 상/중/하는 보정 계수를 적용한다.

## 예측 설정
- 예측 모델: Chronos mini (`{MODEL_NAME}`)
- 실행 방식: 로컬 CPU 추론
- 예측 범위: 최신 관측일 이후 30영업일
- 예측값 의미: 중앙값은 기본 예상 시세, p10은 낮은 경우, p90은 높은 경우의 참고 범위
- 주의: 이 예측은 과거 소매가격 흐름만 사용한 시계열 예측이며, 날씨, 작황, 명절 수요, 산지 출하량, 도매시장 수급, 재고 정보는 직접 반영하지 않았다.

## 판매 기준가 산정표
| 크기 | 상품성 | 기준 시세 | 기준 예측가(원/kg) | 보정 계수 | 추천 판매가(원/kg) |
|---|---|---|---:|---:|---:|
{derived_price_rows(forecasts)}

{forecast_sections(forecasts)}

## 챗봇 답변 기준
- 사용자가 사과 시세 전망을 물으면 크기 기준이 있으면 대과는 가락시장 상 등급 예측, 중과는 가락시장 중 등급 예측을 우선 안내한다.
- 사용자가 상품성 등급별 가격을 물으면 판매 기준가 산정표의 추천 판매가를 우선 안내한다.
- 사용자가 판매 시점을 물으면 예측 흐름뿐 아니라 재고 상태와 뉴스 기반 시장 압력을 함께 고려해 답한다.
- 예측값은 확정 가격이 아니라 의사결정을 돕는 참고값으로 설명한다.
- kg당 가격 질문에는 이 문서의 추천 판매가 또는 kg당 환산 가격을 우선 사용한다.
"""
    OUTPUT_PATH.write_text(content, encoding="utf-8")


def main() -> None:
    pipeline = load_pipeline()
    forecasts = {}
    for grade in FORECAST_GRADES:
        history = load_apple_price_series(grade)
        forecast = forecast_prices(history["price"], pipeline)
        forecasts[grade] = prepare_forecast(grade, history, forecast)
    write_markdown(forecasts)
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
