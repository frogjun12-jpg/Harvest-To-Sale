import json
import os
import re
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(Path("editions/pro/.env.pro"))
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise SystemExit("OPENAI_API_KEY가 editions/pro/.env.pro에 없습니다.")

# Ignore invalid local placeholder values while evaluating with the official API.
os.environ.pop("OPENAI_BASE_URL", None)
client = OpenAI(api_key=api_key)

CHAT_URL = os.getenv("EVAL_CHAT_URL", "http://127.0.0.1:8000/chat")
EVAL_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
TARGET_LABEL = os.getenv("EVAL_TARGET_LABEL", "pro")
TARGET_LLM_PROVIDER = os.getenv("EVAL_LLM_PROVIDER", "openai")
OUTPUT_PATH = Path(os.getenv("EVAL_OUTPUT_PATH", "reviews/rag_eval_pro_latest.json"))
QUESTIONS_PATH = os.getenv("EVAL_QUESTIONS_PATH")

if QUESTIONS_PATH:
    questions = json.loads(Path(QUESTIONS_PATH).read_text(encoding="utf-8"))
else:
    questions = [
        "현재 사과 시세를 알려줘",
        "대과 상 등급 kg당 가격은 얼마야?",
        "현재 재고현황을 크기와 품질별로 알려줘",
        "1달 내에 가장 팔기 좋은 날짜가 언제야?",
        "최근 과일 뉴스 중 판매 판단에 영향 있는 내용만 요약해줘",
        "바나나 수입 관세율을 알려줘",
    ]

judge_system = """당신은 RAG 챗봇 평가자입니다. 반드시 JSON만 출력하세요.
평가 기준:
- answer_relevancy: 질문에 직접 답했는가? 0~1
- faithfulness: 답변의 수치/사실이 제공된 contexts에 근거하는가? 0~1
- context_relevance: 검색된 contexts가 질문에 유용한가? 0~1
- hallucination_rate: contexts에 없거나 모순되는 사실 주장 비율. 0이면 없음, 1이면 심각함
- korean_quality: 한국어 자연스러움, 중국어/한자/긴 영어 문장 없음. 0~1
- 참고 정보가 없을 때 답변이 "확인 필요", "자료가 필요"처럼 모른다고 안내하고 구체 수치를 만들지 않으면 hallucination_rate는 0으로 평가하세요.
- 참고 정보가 없을 때 정확히 모른다고 안내한 답변은 answer_relevancy와 faithfulness를 낮게 주지 말고, 질문에 대한 안전한 응답으로 평가하세요.
짧은 reason을 한국어로 작성하세요."""


def call_chat(question: str, idx: int) -> tuple[dict, float]:
    payload = {
        "question": question,
        "user_id": f"eval_user_{idx}_{int(time.time())}",
        "llm_provider": TARGET_LLM_PROVIDER,
    }
    start = time.perf_counter()
    response = requests.post(CHAT_URL, json=payload, timeout=120)
    elapsed = time.perf_counter() - start
    response.raise_for_status()
    return response.json(), elapsed


def judge(question: str, answer: str, sources: list[dict]) -> dict:
    contexts = [source.get("content", "") for source in sources]
    prompt = {"question": question, "answer": answer, "contexts": contexts}
    response = client.chat.completions.create(
        model=EVAL_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": judge_system},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
    )
    text = response.choices[0].message.content or "{}"
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "answer_relevancy": None,
            "faithfulness": None,
            "context_relevance": None,
            "hallucination_rate": None,
            "korean_quality": None,
            "reason": f"평가 JSON 파싱 실패: {text[:200]}",
        }


rows = []
for idx, question in enumerate(questions, 1):
    data, elapsed = call_chat(question, idx)
    answer = data.get("answer", "")
    sources = data.get("sources", [])
    scores = judge(question, answer, sources)
    row = {
        "no": idx,
        "question": question,
        "answer": answer,
        "source_count": len(sources),
        "response_time_sec": round(elapsed, 2),
        **scores,
    }
    rows.append(row)
    print(f"[{idx}/{len(questions)}] {question}")
    print(f"  응답시간: {elapsed:.2f}s / sources: {len(sources)}")
    print(
        "  관련성 {answer_relevancy} | 충실도 {faithfulness} | 검색적합성 "
        "{context_relevance} | 환각률 {hallucination_rate} | 한국어 {korean_quality}".format(
            **scores
        )
    )
    print(f"  이유: {scores.get('reason')}")
    if os.getenv("EVAL_VERBOSE", "").lower() in {"1", "true", "yes"}:
        print(f"  답변: {answer[:260].replace(chr(10), ' ')}")
        print()

score_keys = [
    "answer_relevancy",
    "faithfulness",
    "context_relevance",
    "hallucination_rate",
    "korean_quality",
]
average = {}
for key in score_keys:
    vals = [row.get(key) for row in rows if isinstance(row.get(key), (int, float))]
    average[key] = round(sum(vals) / len(vals), 3) if vals else None
average["response_time_sec"] = round(
    sum(row["response_time_sec"] for row in rows) / len(rows), 2
)

out = {
    "eval_model": EVAL_MODEL,
    "target_label": TARGET_LABEL,
    "target_llm_provider": TARGET_LLM_PROVIDER,
    "target": CHAT_URL,
    "average": average,
    "rows": rows,
}
out_path = OUTPUT_PATH
out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

print("=== 평균 ===")
print(json.dumps(average, ensure_ascii=False, indent=2))
print(f"저장: {out_path}")
