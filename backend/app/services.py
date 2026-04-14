"""
CRUD operations and service layer.
"""

import logging
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.boamp import BOAMPConnector
from app.connectors.decp import DECPConnector
from app.models import AppelOffre, Keyword, SearchLog

logger = logging.getLogger(__name__)


# --- Keyword CRUD ---

async def create_keyword(db: AsyncSession, word: str, category: Optional[str] = None) -> Keyword:
    kw = Keyword(word=word.strip(), category=category)
    db.add(kw)
    await db.commit()
    await db.refresh(kw)
    return kw


async def get_keywords(db: AsyncSession, active_only: bool = True) -> List[Keyword]:
    stmt = select(Keyword)
    if active_only:
        stmt = stmt.where(Keyword.is_active == True)
    stmt = stmt.order_by(Keyword.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def delete_keyword(db: AsyncSession, keyword_id: int) -> bool:
    stmt = select(Keyword).where(Keyword.id == keyword_id)
    result = await db.execute(stmt)
    kw = result.scalar_one_or_none()
    if kw:
        await db.delete(kw)
        await db.commit()
        return True
    return False


async def toggle_keyword(db: AsyncSession, keyword_id: int) -> Optional[Keyword]:
    stmt = select(Keyword).where(Keyword.id == keyword_id)
    result = await db.execute(stmt)
    kw = result.scalar_one_or_none()
    if kw:
        kw.is_active = not kw.is_active
        await db.commit()
        await db.refresh(kw)
    return kw


# --- Favorites CRUD ---

async def get_favorites(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    source: Optional[str] = None,
    keyword_filter: Optional[str] = None,
) -> Tuple[List[AppelOffre], int]:
    stmt = select(AppelOffre)

    if source:
        stmt = stmt.where(AppelOffre.source == source)
    if keyword_filter:
        stmt = stmt.where(
            AppelOffre.title.ilike(f"%{keyword_filter}%")
            | AppelOffre.description.ilike(f"%{keyword_filter}%")
        )

    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    # Paginate
    stmt = stmt.order_by(AppelOffre.date_publication.desc().nullslast())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return items, total


async def save_favorite(db: AsyncSession, ao_data: dict) -> AppelOffre:
    """Save an AO to DB as favorite."""
    existing = await db.execute(
        select(AppelOffre).where(AppelOffre.reference == ao_data["reference"])
    )
    ao = existing.scalar_one_or_none()
    if ao:
        return ao

    ao = AppelOffre(
        reference=ao_data["reference"],
        title=ao_data["title"],
        description=ao_data.get("description"),
        organisme=ao_data.get("organisme"),
        date_publication=ao_data.get("date_publication"),
        date_cloture=ao_data.get("date_cloture"),
        source=ao_data["source"],
        url=ao_data.get("url"),
        lieu_execution=ao_data.get("lieu_execution"),
        nature_marche=ao_data.get("nature_marche"),
        montant_estime=ao_data.get("montant_estime"),
        cpv_codes=ao_data.get("cpv_codes"),
        is_favorite=True,
    )
    db.add(ao)
    await db.commit()
    await db.refresh(ao)
    return ao


async def remove_favorite(db: AsyncSession, ao_id: int) -> bool:
    """Remove an AO from DB (unfavorite = delete)."""
    stmt = select(AppelOffre).where(AppelOffre.id == ao_id)
    result = await db.execute(stmt)
    ao = result.scalar_one_or_none()
    if ao:
        await db.delete(ao)
        await db.commit()
        return True
    return False


async def get_favorite_by_id(db: AsyncSession, ao_id: int) -> Optional[AppelOffre]:
    stmt = select(AppelOffre).where(AppelOffre.id == ao_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# --- Search Platforms (no DB storage) ---

async def search_platforms(db: AsyncSession, sources: List[str], search_terms: Optional[List[str]] = None) -> dict:
    """Fetch AOs from platforms and return results without storing.
    Cross-references DB to mark already-favorited items."""
    keywords = await get_keywords(db, active_only=True)
    keyword_words = [kw.word for kw in keywords]
    query_terms = search_terms if search_terms else keyword_words

    stats = {"fetched": 0, "errors": []}
    all_results = []

    connectors = {}
    if "BOAMP" in sources:
        connectors["BOAMP"] = BOAMPConnector()
    if "DECP" in sources:
        connectors["DECP"] = DECPConnector()

    for source_name, connector in connectors.items():
        try:
            raw_results = await connector.fetch(query_terms, offset=0, limit=100)
            stats["fetched"] += len(raw_results)
            all_results.extend(raw_results)

            log = SearchLog(
                source=source_name,
                query=", ".join(query_terms),
                results_count=len(raw_results),
                status="success",
            )
            db.add(log)

        except Exception as e:
            logger.error(f"Error fetching from {source_name}: {e}")
            stats["errors"].append(f"{source_name}: {str(e)}")
            log = SearchLog(
                source=source_name,
                query=", ".join(query_terms),
                results_count=0,
                status="error",
                error_message=str(e),
            )
            db.add(log)

    await db.commit()

    # Check which results are already favorited in DB
    references = [r["reference"] for r in all_results]
    fav_map = {}
    if references:
        existing = await db.execute(
            select(AppelOffre.reference, AppelOffre.id).where(AppelOffre.reference.in_(references))
        )
        fav_map = {ref: ao_id for ref, ao_id in existing.all()}

    # Build enriched results
    enriched = []
    for ao_data in all_results:
        ref = ao_data["reference"]
        enriched.append({
            "reference": ref,
            "title": ao_data["title"],
            "description": ao_data.get("description"),
            "organisme": ao_data.get("organisme"),
            "date_publication": ao_data.get("date_publication"),
            "date_cloture": ao_data.get("date_cloture"),
            "source": ao_data["source"],
            "url": ao_data.get("url"),
            "lieu_execution": ao_data.get("lieu_execution"),
            "nature_marche": ao_data.get("nature_marche"),
            "montant_estime": ao_data.get("montant_estime"),
            "cpv_codes": ao_data.get("cpv_codes"),
            "is_favorite": ref in fav_map,
            "db_id": fav_map.get(ref),
        })

    # Sort by publication date (most recent first)
    enriched.sort(key=lambda x: x.get("date_publication") or "", reverse=True)

    return {"results": enriched, "stats": stats}


# --- Stats ---

async def get_stats(db: AsyncSession) -> dict:
    total_kw = (await db.execute(select(func.count(Keyword.id)))).scalar() or 0
    favs = (await db.execute(select(func.count(AppelOffre.id)))).scalar() or 0

    source_counts = {}
    sources_result = await db.execute(
        select(AppelOffre.source, func.count(AppelOffre.id)).group_by(AppelOffre.source)
    )
    for source, count in sources_result.all():
        source_counts[source] = count

    recent_fetches = (await db.execute(select(func.count(SearchLog.id)))).scalar() or 0

    return {
        "total_keywords": total_kw,
        "favorites": favs,
        "sources": source_counts,
        "recent_fetches": recent_fetches,
    }
