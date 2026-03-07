from urllib.parse import quote_plus

from imager.config import ARTGRID_SEARCH_BASE


def artgrid_search_url(keywords: list[str]) -> str:
    if not keywords:
        return ARTGRID_SEARCH_BASE
    query = " ".join(keywords)
    return f"{ARTGRID_SEARCH_BASE}?q={quote_plus(query)}"
