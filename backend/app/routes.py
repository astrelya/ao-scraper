"""
API routes for the AO Scraper application.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    AOListResponse,
    AOOut,
    AOSaveRequest,
    FetchRequest,
    FetchResponse,
    KeywordCreate,
    KeywordOut,
    StatsOut,
)
from app.services import (
    create_keyword,
    delete_keyword,
    get_favorite_by_id,
    get_favorites,
    get_keywords,
    get_stats,
    remove_favorite,
    save_favorite,
    search_platforms,
    toggle_keyword,
)

router = APIRouter()


# ==================== Keywords ====================

@router.get("/keywords", response_model=list[KeywordOut], tags=["Keywords"])
async def list_keywords(
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    return await get_keywords(db, active_only=active_only)


@router.post("/keywords", response_model=KeywordOut, status_code=201, tags=["Keywords"])
async def add_keyword(
    payload: KeywordCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await create_keyword(db, word=payload.word, category=payload.category)
    except Exception:
        raise HTTPException(status_code=400, detail="Ce mot-clé existe déjà.")


@router.delete("/keywords/{keyword_id}", tags=["Keywords"])
async def remove_keyword(
    keyword_id: int,
    db: AsyncSession = Depends(get_db),
):
    deleted = await delete_keyword(db, keyword_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Mot-clé introuvable.")
    return {"ok": True}


@router.patch("/keywords/{keyword_id}/toggle", response_model=KeywordOut, tags=["Keywords"])
async def toggle_keyword_active(
    keyword_id: int,
    db: AsyncSession = Depends(get_db),
):
    kw = await toggle_keyword(db, keyword_id)
    if not kw:
        raise HTTPException(status_code=404, detail="Mot-clé introuvable.")
    return kw


# ==================== Favoris ====================

@router.get("/favorites", response_model=AOListResponse, tags=["Favoris"])
async def list_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    items, total = await get_favorites(
        db,
        page=page,
        page_size=page_size,
        source=source,
        keyword_filter=search,
    )
    return AOListResponse(
        total=total,
        items=items,
        page=page,
        page_size=page_size,
    )


@router.post("/favorites", response_model=AOOut, status_code=201, tags=["Favoris"])
async def add_favorite(
    payload: AOSaveRequest,
    db: AsyncSession = Depends(get_db),
):
    ao = await save_favorite(db, payload.model_dump())
    return ao


@router.delete("/favorites/{ao_id}", tags=["Favoris"])
async def delete_favorite(
    ao_id: int,
    db: AsyncSession = Depends(get_db),
):
    deleted = await remove_favorite(db, ao_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Favori introuvable.")
    return {"ok": True}


@router.get("/favorites/{ao_id}", response_model=AOOut, tags=["Favoris"])
async def get_favorite_detail(
    ao_id: int,
    db: AsyncSession = Depends(get_db),
):
    ao = await get_favorite_by_id(db, ao_id)
    if not ao:
        raise HTTPException(status_code=404, detail="Favori introuvable.")
    return ao


# ==================== Fetch ====================

@router.post("/fetch", response_model=FetchResponse, tags=["Fetch"])
async def trigger_fetch(
    payload: FetchRequest,
    db: AsyncSession = Depends(get_db),
):
    """Fetch AOs from platforms and return results (not stored in DB)."""
    allowed = {"BOAMP", "DECP"}
    for s in payload.sources:
        if s not in allowed:
            raise HTTPException(status_code=400, detail=f"Source inconnue: {s}")

    result = await search_platforms(db, payload.sources, search_terms=payload.keywords)
    return result


# ==================== Stats ====================

@router.get("/stats", response_model=StatsOut, tags=["Stats"])
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
):
    return await get_stats(db)
