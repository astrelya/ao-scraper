"""
AO Scraper - FastAPI Application
Connects to French public procurement APIs (BOAMP, DECP) to identify
relevant appels d'offres for ESN companies.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AO Scraper API...")
    await init_db()
    logger.info("Database initialized.")
    yield
    logger.info("Shutting down AO Scraper API.")


app = FastAPI(
    title="AO Scraper",
    description="Veille automatisée sur les appels d'offres des marchés publics",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
