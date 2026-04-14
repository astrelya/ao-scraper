"""
Keyword matching engine.
Matches AO content against user-defined keywords.
"""

import re
from typing import Dict, Any, List, Set


def match_keywords(ao_data: Dict[str, Any], keywords: List[str]) -> Set[str]:
    """
    Check which keywords match within an AO's searchable fields.
    Returns the set of matched keyword strings.
    """
    if not keywords:
        return set()

    searchable_text = " ".join(
        str(ao_data.get(field, ""))
        for field in ["title", "description", "organisme", "nature_marche", "cpv_codes", "lieu_execution"]
    ).lower()

    matched = set()
    for keyword in keywords:
        pattern = re.compile(re.escape(keyword.lower()), re.IGNORECASE)
        if pattern.search(searchable_text):
            matched.add(keyword)

    return matched


def compute_relevance_score(ao_data: Dict[str, Any], matched_keywords: Set[str], total_keywords: int) -> float:
    """
    Compute a relevance score (0.0 to 1.0) based on:
    - Number of matched keywords vs total
    - Whether keyword appears in title (higher weight)
    """
    if total_keywords == 0 or not matched_keywords:
        return 0.0

    base_score = len(matched_keywords) / total_keywords

    title = str(ao_data.get("title", "")).lower()
    title_bonus = 0.0
    for kw in matched_keywords:
        if kw.lower() in title:
            title_bonus += 0.1

    return min(1.0, base_score + title_bonus)
