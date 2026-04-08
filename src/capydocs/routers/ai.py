"""AI text refinement API endpoint."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from capydocs.services.ai import PRESETS, refine_text

router = APIRouter(tags=["ai"])


class RefineRequest(BaseModel):
    text: str
    instruction: str = ""
    preset: str | None = None


class RefineResponse(BaseModel):
    refined: str
    model: str


@router.post("/ai/refine", response_model=RefineResponse)
async def api_refine(body: RefineRequest) -> RefineResponse:
    """Refine selected text using AI."""
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    try:
        result = await refine_text(body.text, body.instruction, body.preset)
        return RefineResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {e}") from None


@router.get("/ai/presets")
async def api_presets() -> dict[str, str]:
    """Get available refinement presets."""
    return PRESETS
