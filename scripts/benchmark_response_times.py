import csv
import json
import statistics
import time
from datetime import datetime
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_path = OUTPUT_DIR / f"response_time_benchmark_{timestamp}.csv"
json_path = OUTPUT_DIR / f"response_time_benchmark_{timestamp}.json"

targets = [
    {"label": "Free-Ollama", "url": "http://127.0.0.1:8001/chat", "provider": "ollama"},
    {"label": "Pro-OpenAI", "url": "http://127.0.0.1:8000/chat", "provider": "openai"},
]

questions = [
    ("direct_db_inventory", "현재 재고현황을 크기와 등급별로 알려줘"),
    ("direct_db_harvest", "오늘 로봇이 수확한 사과 기록을 알려줘"),
    ("rag_price", "현재 사과 시세를 알려줘"),
    ("rag_news", "최근 과일 뉴스 중 판매 판단에 영향 있는 내용만 요약해줘"),
    ("rag_decision", "시세 예측과 뉴스를 고려하면 지금 사과를 팔아야 할까?"),
    ("unknown_safe_answer", "바나나 수입 관세율을 알려줘"),
]

rows = []

for target in targets:
    for category, question in questions:
        for run in range(1, 4):
            payload = {
                "question": question,
                "user_id": f"bench_{target['label']}_{category}_{run}_{int(time.time())}",
                "llm_provider": target["provider"],
            }
            started = time.perf_counter()
            status = "ok"
            answer_length = 0
            source_count = 0
            error = ""
            try:
                response = requests.post(target["url"], json=payload, timeout=180)
                response.raise_for_status()
                data = response.json()
                answer_length = len(data.get("answer", "") or "")
                source_count = len(data.get("sources", []) or [])
            except Exception as exc:
                status = "error"
                error = str(exc)
            elapsed = round(time.perf_counter() - started, 3)
            rows.append(
                {
                    "target": target["label"],
                    "provider": target["provider"],
                    "category": category,
                    "run": run,
                    "elapsed_sec": elapsed,
                    "status": status,
                    "source_count": source_count,
                    "answer_length": answer_length,
                    "error": error,
                    "question": question,
                }
            )
            print(
                f"{target['label']} | {category} | run {run} | "
                f"{elapsed:.3f}s | {status}"
            )

with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

with json_path.open("w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)


def summarize(group_rows):
    ok = [row for row in group_rows if row["status"] == "ok"]
    if not ok:
        return {"count": 0, "avg_sec": None, "min_sec": None, "max_sec": None}
    values = [row["elapsed_sec"] for row in ok]
    return {
        "count": len(ok),
        "avg_sec": round(statistics.mean(values), 3),
        "min_sec": round(min(values), 3),
        "max_sec": round(max(values), 3),
    }


overall = {}
by_category = {}
for target in targets:
    label = target["label"]
    target_rows = [row for row in rows if row["target"] == label]
    overall[label] = summarize(target_rows)
    by_category[label] = {}
    for category, _ in questions:
        by_category[label][category] = summarize(
            [row for row in target_rows if row["category"] == category]
        )

result = {
    "csv": str(csv_path),
    "json": str(json_path),
    "overall": overall,
    "by_category": by_category,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
