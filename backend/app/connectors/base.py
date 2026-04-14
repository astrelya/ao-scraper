from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseConnector(ABC):
    """Base class for all AO source connectors."""

    @abstractmethod
    async def fetch(self, keywords: List[str], offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch appels d'offres matching keywords."""
        pass

    @abstractmethod
    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw API response to our standard schema."""
        pass
