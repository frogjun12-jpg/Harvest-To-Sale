import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

BASE_URL = "https://www.garakprice.com/pum_detail.php"
PUM_CD = "41130"
YEARS = list(range(2017, 2026))
OUTPUT_PATH = "garak_apple_prices.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def crawl_year(year: int) -> list[dict]:
    url = f"{BASE_URL}?pum_cd={PUM_CD}&year={year}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"  [{year}] 요청 실패: {e}")
        return []

    soup = BeautifulSoup(res.text, "lxml")
    rows = []

    # ul 안의 li 전체 순회
    # 헤더 li (날짜/기준단위/등급/평균가) 제외하고 데이터 li만 파싱
    for ul in soup.select("ul"):
        items = ul.find_all("li", recursive=False)
        
        # 헤더 li 건너뛰기 (첫번째 li가 헤더인 경우)
        for li in items:
            texts = [t.strip() for t in li.stripped_strings]
            
            # 데이터 li는 [날짜, 기준단위, 등급, 가격] 4개 요소
            if len(texts) < 4:
                continue
            
            # 날짜 형식 확인 (2024/1/15)
            if "/" not in texts[0] or not texts[0][0].isdigit():
                continue

            try:
                date_parts = texts[0].split("/")
                if len(date_parts) != 3:
                    continue
                date = pd.Timestamp(
                    year=int(date_parts[0]),
                    month=int(date_parts[1]),
                    day=int(date_parts[2])
                )
            except:
                continue

            unit  = texts[1]  # 10 키로상자
            grade = texts[2]  # 특/상/중/하
            price_text = texts[3].replace(",", "")

            if grade not in ["특", "상", "중", "하"]:
                continue

            try:
                price = int(price_text)
            except:
                continue

            price_per_kg = round(price / 10, 1) if "10" in unit else round(price / 5, 1)

            rows.append({
                "date":         date,
                "unit":         unit,
                "grade":        grade,
                "price":        price,
                "price_per_kg": price_per_kg,
            })

    print(f"  [{year}] {len(rows)}건 수집")
    return rows


def main():
    all_rows = []

    for year in YEARS:
        print(f"{year}년 크롤링 중...")
        rows = crawl_year(year)
        all_rows.extend(rows)
        time.sleep(1)

    if not all_rows:
        print("수집된 데이터 없음")
        return

    df = pd.DataFrame(all_rows)
    df = df.sort_values(["date", "grade"]).reset_index(drop=True)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"\n저장 완료: {OUTPUT_PATH}")
    print(f"총 {len(df)}건")
    print(df["date"].min(), "~", df["date"].max())
    print(df.head(10))


if __name__ == "__main__":
    main()