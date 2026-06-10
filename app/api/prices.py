from fastapi import APIRouter, HTTPException

from app.prices.refresh import refresh_price_forecast_rag

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("/refresh")
def refresh_prices_info() -> dict:
    return {
        "message": "이 주소는 가격 정보 업데이트 API입니다. 관리자 Streamlit 화면의 '가격 정보 업데이트' 버튼으로 실행하세요.",
        "method": "POST",
        "path": "/prices/refresh",
    }


@router.post("/refresh")
def refresh_prices() -> dict:
    try:
        return refresh_price_forecast_rag()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
