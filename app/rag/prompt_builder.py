def build_prompt(question: str, chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"[문서: {chunk['source_path']} / chunk {chunk['chunk_index']}]\n{chunk['content']}"
        for chunk in chunks
    )
    if not context:
        context = "관련 문서를 찾지 못했습니다."

    return f"""
당신은 AI 기반 과일 자동 수확, 선별, 가격산정, 판매등록 시스템의 업무 도우미입니다.
아래 RAG 문서 내용을 우선 근거로 삼아 한국어로 정확하고 간결하게 답변하세요.
문서에 없는 내용은 추측하지 말고, 문서에 없다고 말한 뒤 일반적인 참고 의견임을 구분하세요.

# RAG 문서
{context}

# 사용자 질문
{question}

# 답변
""".strip()
