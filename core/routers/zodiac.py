from fastapi import APIRouter, HTTPException, Query

from core.gaian.base_forms import get_base_form
from core.zodiac_engine import ALL_SIGNS, ZODIAC_FORM_MAP, ZodiacEngine

router = APIRouter()


@router.get("/zodiac/preview")
async def zodiac_preview(birth_date: str = Query(..., description="Birth date: YYYY-MM-DD, MM/DD/YYYY, or DD/MM/YYYY")):
    try:
        reading = ZodiacEngine.read(birth_date)
        form = get_base_form(reading.base_form_id)
        return {
            "birth_date": reading.birth_date,
            "sign": reading.sign,
            "element": reading.element,
            "base_form_id": reading.base_form_id,
            "base_form_name": form.name if form else reading.base_form_id,
            "base_form_role": form.role if form else "",
            "avatar_color": form.avatar_color if form else "",
            "avatar_style": form.avatar_style if form else "",
            "visual_notes": form.visual_notes if form else "",
            "reason": reading.reason,
            "assigned_by": "cosmos",
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/zodiac/all")
async def zodiac_all():
    rows = []
    for sign in ALL_SIGNS:
        form_id = ZODIAC_FORM_MAP.get(sign, "gaia")
        form = get_base_form(form_id)
        rows.append({
            "sign": sign,
            "base_form_id": form_id,
            "base_form_name": form.name if form else form_id,
            "avatar_color": form.avatar_color if form else "",
            "avatar_style": form.avatar_style if form else "",
        })
    return {"zodiac_map": rows, "count": len(rows)}
