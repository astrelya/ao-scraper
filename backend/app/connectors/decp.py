"""
Connector for DECP (Données Essentielles de la Commande Publique).
Uses data.gouv.fr open data API to fetch public procurement data.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from app.connectors.base import BaseConnector

logger = logging.getLogger(__name__)

DECP_API_URL = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/decp_augmente/records"


class DECPConnector(BaseConnector):
    """Connector for DECP via data.economie.gouv.fr API."""

    def __init__(self):
        self.base_url = DECP_API_URL

    async def fetch(self, keywords: List[str], offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch marchés from DECP matching keywords."""
        if not keywords:
            return []

        # Build keyword conditions — search in objetmarche (title), considerationssociales and other content
        kw_conditions = []
        for kw in keywords:
            safe_kw = kw.replace('"', '')
            kw_conditions.append(
                f'(objetmarche like "{safe_kw}" OR codecpv like "{safe_kw}" OR lieuexecutionnom like "{safe_kw}")'
            )
        kw_clause = " OR ".join(kw_conditions)

        # Only fetch contracts notified within the last 2 months
        two_months_ago = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        date_filter = f'datenotification >= "{two_months_ago}"'

        where_clause = f'({kw_clause}) AND {date_filter}'

        params = {
            "where": where_clause,
            "order_by": "datenotification DESC",
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
            logger.error(f"DECP API error: {e}")
            raise

        return results

    def normalize(self, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize DECP record to standard schema."""
        try:
            fields = raw

            date_pub = None
            if fields.get("datenotification"):
                try:
                    date_pub = datetime.fromisoformat(str(fields["datenotification"]).replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass

            reference = fields.get("id", fields.get("uid", ""))

            # Build URL to the DECP record on data.economie.gouv.fr
            url = (
                f"https://data.economie.gouv.fr/explore/dataset/decp_augmente/"
                f"table/?q={reference}"
            ) if reference else None

            return {
                "reference": f"DECP-{reference}",
                "title": fields.get("objetmarche", "Sans titre"),
                "description": fields.get("objetmarche", ""),
                "organisme": fields.get("nomacheteur", ""),
                "date_publication": date_pub,
                "date_cloture": None,
                "source": "DECP",
                "url": url,
                "lieu_execution": fields.get("lieuexecutionnom", ""),
                "nature_marche": fields.get("nature", ""),
                "montant_estime": fields.get("montant", None),
                "cpv_codes": fields.get("codecpv", ""),
                "raw_data": json.dumps(fields, default=str, ensure_ascii=False),
            }
        except Exception as e:
            logger.error(f"Error normalizing DECP record: {e}")
            return None
