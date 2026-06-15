import json
import os
import re
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / "editions/pro/.env.pro")

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise SystemExit("OPENAI_API_KEY is missing in editions/pro/.env.pro")

os.environ.pop("OPENAI_BASE_URL", None)
client = OpenAI(api_key=api_key)

EVAL_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
OUTPUT_PATH = PROJECT_ROOT / "reviews/llm_reasoning_eval_latest.json"

TARGETS = [
    {
        "label": "free_ollama",
        "provider": "ollama",
        "url": os.getenv("FREE_CHAT_URL", "http://127.0.0.1:8001/chat"),
    },
    {
        "label": "pro_openai",
        "provider": "openai",
        "url": os.getenv("PRO_CHAT_URL", "http://127.0.0.1:8000/chat"),
    },
]

QUESTIONS = [
    "최근 뉴스와 시세 예측을 같이 보면 지금 사과를 판매하는 게 좋을까?",
    "가격이 하락할 가능성이 있을 때 분할 판매가 유리한 이유를 설명해줘.",
    "재고가 많고 뉴스에서는 가격 하락 가능성이 있을 때 판매 전략을 추천해줘.",
    "시세 예측과 뉴스 내용이 서로 다를 때 어떤 기준으로 판단해야 해?",
    "지금 판매, 분할 판매, 단기 보류 중 하나를 골라 근거와 함께 말해줘.",
    "가격 예측이 불확실하고 재고도 남아 있다면 어떤 방식으로 판매 결정을 해야 해?",
    "최근 과일 뉴스가 사과 판매 시점에 어떤 영향을 줄 수 있는지 운영자 관점에서 정리해줘.",
    "시세, 뉴스, 재고를 함께 고려해서 오늘 해야 할 판매 액션을 짧게 제안해줘.",
]

JUDGE_SYSTEM = """
당신은 농산물 판매 AI 챗봇의 'LLM 추론 품질' 평가자입니다.
반드시 JSON만 출력하세요.

평가 목적:
- 단순 DB 조회 성능이 아니라 LLM이 문맥을 종합하고 판매 판단을 설명하는 능력을 평가합니다.
- 질문, 답변, sources를 함께 보고 평가합니다.
- sources는 RAG 검색 문맥입니다. 답변이 sources를 잘 사용하면 높은 점수를 줄 수 있습니다.
- sources가 부족할 때는 답변이 불확실성을 안전하게 다루는지 평가하세요.

모든 점수는 0~1 사이입니다.
- complex_reasoning: 시세, 뉴스, 재고, 불확실성 등 여러 요소를 종합해 판단하는가?
- evidence_explanation: 결론의 근거를 명확히 설명하고 근거와 결론을 자연스럽게 연결하는가?
- actionability: 운영자가 바로 사용할 수 있는 판매 액션이 있는가?
- uncertainty_handling: 근거가 부족하거나 예측이 불확실할 때 단정하지 않고 안전하게 답하는가?
- instruction_following: 질문에서 요구한 방식, 길이, 결론 형식을 잘 따르는가?
- korean_quality: 자연스럽고 읽기 쉬운 한국어인가?
- hallucination_risk: 근거 없는 사실 주장 또는 sources와 모순되는 주장 위험. 0이면 낮음, 1이면 높음.
- overall: 위 항목을 종합한 전체 추론 품질. hallucination_risk가 높으면 overall은 낮아야 합니다.

reason은 한국어 1~3문장으로 작성하세요.
"""


def call_chat(target: dict, question: str, idx: int) -> tuple[dict, float]:
    payload = {
        "question": question,
        "user_id": f"reasoning_eval_{target['label']}_{idx}_{int(time.time())}",
        "llm_provider": target["provider"],
    }
    start = time.perf_counter()
    response = requests.post(target["url"], json=payload, timeout=180)
    elapsed = time.perf_counter() - start
    response.raise_for_status()
    return response.json(), elapsed


def judge(question: str, answer: str, sources: list[dict]) -> dict:
    contexts = [source.get("content", "") for source in sources]
    prompt = {
        "question": question,
        "answer": answer,
        "contexts": contexts,
    }
    response = client.chat.completions.create(
        model=EVAL_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
    )
    text = response.choices[0].message.content or "{}"
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "complex_reasoning": None,
            "evidence_explanation": None,
            "actionability": None,
            "uncertainty_handling": None,
            "instruction_following": None,
            "korean_quality": None,
            "hallucination_risk": None,
            "overall": None,
            "reason": f"평가 JSON 파싱 실패: {text[:200]}",
        }


def average_rows(rows: list[dict], label: str) -> dict:
    score_keys = [
        "complex_reasoning",
        "evidence_explanation",
        "actionability",
        "uncertainty_handling",
        "instruction_following",
        "korean_quality",
        "hallucination_risk",
        "overall",
        "response_time_sec",
    ]
    target_rows = [row for row in rows if row["target"] == label]
    averages = {}
    for key in score_keys:
        vals = [row.get(key) for row in target_rows if isinstance(row.get(key), (int, float))]
        averages[key] = round(sum(vals) / len(vals), 3) if vals else None
    return averages


def main() -> None:
    rows = []
    for target in TARGETS:
        for idx, question in enumerate(QUESTIONS, 1):
            data, elapsed = call_chat(target, question, idx)
            answer = data.get("answer", "")
            sources = data.get("sources", [])
            scores = judge(question, answer, sources)
            row = {
                "target": target["label"],
                "provider": target["provider"],
                "no": idx,
                "question": question,
                "answer": answer,
                "source_count": len(sources),
                "response_time_sec": round(elapsed, 2),
                **scores,
            }
            rows.append(row)
            print(f"[{target['label']}] {idx}/{len(QUESTIONS)} {question}")
            print(
                "  overall={overall} reasoning={complex_reasoning} action={actionability} "
                "hallucination_risk={hallucination_risk} time={time}s".format(
                    overall=scores.get("overall"),
                    complex_reasoning=scores.get("complex_reasoning"),
                    actionability=scores.get("actionability"),
                    hallucination_risk=scores.get("hallucination_risk"),
                    time=round(elapsed, 2),
                )
            )

    averages = {target["label"]: average_rows(rows, target["label"]) for target in TARGETS}

    out = {
        "eval_type": "llm_reasoning_quality",
        "eval_model": EVAL_MODEL,
        "criteria": {
            "complex_reasoning": "복합 문맥을 종합해 판단하는 능력",
            "evidence_explanation": "근거와 결론을 연결해 설명하는 능력",
            "actionability": "운영자가 바로 쓸 수 있는 액션 제안",
            "uncertainty_handling": "불확실성의 안전한 처리",
            "instruction_following": "질문 의도와 형식 준수",
            "korean_quality": "한국어 답변 품질",
            "hallucination_risk": "근거 없는 주장 위험도, 낮을수록 좋음",
            "overall": "종합 추론 품질",
        },
        "targets": TARGETS,
        "average": averages,
        "rows": rows,
    }

    OUTPUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("=== average ===")
    print(json.dumps(averages, ensure_ascii=False, indent=2))
    print(f"saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
