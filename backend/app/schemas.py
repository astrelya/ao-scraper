from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# --- Keyword Schemas ---

class KeywordCreate(BaseModel):
    word: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = None


class KeywordOut(BaseModel):
    id: int
    word: str
    category: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- AO Schemas ---

class AOOut(BaseModel):
    id: int
    reference: str
    title: str
    description: Optional[str]
    organisme: Optional[str]
    date_publication: Optional[datetime]
    date_cloture: Optional[datetime]
    source: str
    url: Optional[str]
    lieu_execution: Optional[str]
    nature_marche: Optional[str]
    montant_estime: Optional[float]
    cpv_codes: Optional[str]
    is_favorite: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AOListResponse(BaseModel):
    total: int
    items: List[AOOut]
    page: int
    page_size: int


class AOUpdateFavorite(BaseModel):
    is_favorite: bool


class AOUpdateRead(BaseModel):
    is_read: bool


# --- Search / Fetch Schemas ---

class AOSearchResult(BaseModel):
    reference: str
    title: str
    description: Optional[str] = None
    organisme: Optional[str] = None
    date_publication: Optional[datetime] = None
    date_cloture: Optional[datetime] = None
    source: str
    url: Optional[str] = None
    lieu_execution: Optional[str] = None
    nature_marche: Optional[str] = None
    montant_estime: Optional[float] = None
    cpv_codes: Optional[str] = None
    is_favorite: bool = False
    db_id: Optional[int] = None


class FetchRequest(BaseModel):
    sources: List[str] = Field(default=["BOAMP"])
    keywords: Optional[List[str]] = None


class FetchResponse(BaseModel):
    results: List[AOSearchResult]
    stats: dict


class AOSaveRequest(BaseModel):
    reference: str
    title: str
    description: Optional[str] = None
    organisme: Optional[str] = None
    date_publication: Optional[datetime] = None
    date_cloture: Optional[datetime] = None
    source: str
    url: Optional[str] = None
    lieu_execution: Optional[str] = None
    nature_marche: Optional[str] = None
    montant_estime: Optional[float] = None
    cpv_codes: Optional[str] = None


# --- Stats ---

class StatsOut(BaseModel):
    total_keywords: int
    favorites: int
    sources: dict
    recent_fetches: int
