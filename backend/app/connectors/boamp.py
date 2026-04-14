"""
Connector for BOAMP (Bulletin Officiel des Annonces de Marchés Publics).
Uses the OpenDataSoft API provided by DILA.
API docs: https://boamp-datadila.opendatasoft.com/api/explore/v2.1/
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from app.config import get_settings
from app.connectors.base import BaseConnector

logger = logging.getLogger(__name__)


class BOAMPConnector(BaseConnector):
    """Connector for BOAMP via OpenDataSoft API."""

    DATASET = "boamp"

    def __init__(self):
        self.settings = get_settings()
        self.base_url = f"{self.settings.BOAMP_API_URL}/catalog/datasets/{self.DATASET}/records"

    async def fetch(self, keywords: List[str], offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch AOs from BOAMP API matching given keywords.
        Searches in object and descriptors fields.
        """
        if not keywords:
            return []

        # Build keyword conditions — search in objet (title), donnees (full content) and descripteur_libelle
        kw_conditions = []
        for kw in keywords:
            safe_kw = kw.replace('"', '')
            kw_conditions.append(
                f'(objet like "{safe_kw}" OR donnees like "{safe_kw}" OR descripteur_libelle like "{safe_kw}")'
            )
        kw_clause = " OR ".join(kw_conditions)

        # Date filter: only AOs not yet closed OR closed within last 2 months
        two_months_ago = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        date_filter = f'(datelimitereponse IS NULL OR datelimitereponse >= "{two_months_ago}")'

        where_clause = f'({kw_clause}) AND {date_filter}'

        params = {
            "where": where_clause,
            "order_by": "dateparution DESC",
            "limit": limit,
            "offset": offset,
        }

        results = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()

                for record in data.get("results", []):
                    normalized = self.normalize(record)
                    if normalized:
                        results.append(normalized)

        except httpx.HTTPError as e:
            logger.error(f"BOAMP API error: {e}")
            raise

        return results

    async def fetch_recent(self, days: int = 7, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch recent AOs from the last N days."""
        params = {
            "where": f"dateparution >= '{datetime.now().strftime('%Y-%m-%d')}'",
            "order_by": "dateparution DESC",
            "limit": limit,
            "offset": offset,
        }

        results = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()

                for record in data.get("results", []):
                    normalized = self.normalize(record)
                    if normalized:
                        results.append(normalized)

        except httpx.HTTPError as e:
            logger.error(f"BOAMP API error: {e}")
            raise

        return results

    def normalize(self, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize BOAMP record to standard schema."""
        try:
            fields = raw

            date_pub = None
            if fields.get("dateparution"):
                try:
                    date_pub = datetime.fromisoformat(str(fields["dateparution"]).replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass

            # Use datelimitereponse (actual deadline) if available, fallback to datefindiffusion
            date_cloture = None
            for date_field in ("datelimitereponse", "datefindiffusion"):
                if fields.get(date_field):
                    try:
                        date_cloture = datetime.fromisoformat(str(fields[date_field]).replace("Z", "+00:00"))
                        break
                    except (ValueError, TypeError):
                        continue

            reference = fields.get("idweb", fields.get("id", ""))

            # Use the real BOAMP avis URL if available
            url = fields.get("url_avis")
            if not url and reference:
                url = f"https://www.boamp.fr/pages/avis/?q=idweb:{reference}"

            return {
                "reference": str(reference),
                "title": fields.get("objet", "Sans titre"),
                "description": fields.get("objet", ""),
                "organisme": fields.get("nomacheteur", fields.get("denomination", "")),
                "date_publication": date_pub,
                "date_cloture": date_cloture,
                "source": "BOAMP",
                "url": url,
                "lieu_execution": fields.get("lieu_exec_nom", fields.get("codeinsee_exec", "")),
                "nature_marche": fields.get("nature", ""),
                "cpv_codes": fields.get("codecpv", ""),
                "raw_data": json.dumps(fields, default=str, ensure_ascii=False),
            }
        except Exception as e:
            logger.error(f"Error normalizing BOAMP record: {e}")
            return None
