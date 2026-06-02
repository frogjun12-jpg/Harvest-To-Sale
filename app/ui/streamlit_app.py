import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

CHAT_API_URL = os.getenv("CHAT_API_URL", "http://localhost:8000/chat")

st.set_page_config(page_title="Fruits RAG Chatbot", page_icon="🍎", layout="centered")
st.title("과일 자동화 RAG 챗봇")

question = st.text_area("질문", placeholder="예: 사과 선별 기준을 알려줘", height=120)

if st.button("질문하기", type="primary", disabled=not question.strip()):
    with st.spinner("로컬 LLM이 답변을 생성하는 중입니다..."):
        try:
            response = requests.post(CHAT_API_URL, json={"question": question}, timeout=120)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            st.error(f"API 호출 실패: {exc}")
        else:
            st.subheader("답변")
            st.write(data["answer"])

            with st.expander("검색된 문서 chunk"):
                for source in data.get("sources", []):
                    st.markdown(
                        f"**{source['source_path']} / chunk {source['chunk_index']}** "
                        f"(distance: {source['distance']:.4f})"
                    )
                    st.write(source["content"])
