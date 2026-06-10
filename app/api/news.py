from fastapi import APIRouter, HTTPException

from app.news.refresh import preview_news, refresh_news_rag

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/refresh")
def refresh_news_info() -> dict:
    return {
        "message": "이 주소는 최신 뉴스 업데이트 API입니다. 관리자 Streamlit 화면의 '최신 뉴스 업데이트' 버튼으로 실행하세요.",
        "method": "POST",
        "path": "/news/refresh",
    }


@router.get("/preview")
def news_preview() -> dict:
    try:
        return preview_news()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/refresh")
def refresh_news() -> dict:
    try:
        return refresh_news_rag()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
