from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from config import get_settings

router = APIRouter(prefix="/ai", tags=["ai"])


def verify_internal_token(
    token: Annotated[str | None, Header(alias="X-Internal-Service-Token")] = None,
) -> None:
    expected = get_settings().internal_service_token
    if not expected:
        raise HTTPException(status_code=503, detail="INTERNAL_SERVICE_TOKEN is not configured")
    if token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/health", dependencies=[Depends(verify_internal_token)])
def ai_health():
    return {"status": "ok", "service": "python-ai"}


class RateMyProfessorSearchRequest(BaseModel):
    professor_name: str
    school_name: str | None = None


@router.post("/ratemyprofessor/search", dependencies=[Depends(verify_internal_token)])
def ratemyprofessor_search(_payload: RateMyProfessorSearchRequest):
    return {"status": "not_implemented", "message": "RateMyProfessor integration pending"}
