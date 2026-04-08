from fastapi import APIRouter
from pydantic import BaseModel

from podpal.search.resolve import resolve_search_term


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


class SearchRequest(BaseModel):
    query: str


@router.post("/preview")
def preview_search(request: SearchRequest):
    """
    Preview how a natural-language search query is resolved
    into podcast RSS feed URLs.
    """

    query = request.query.strip()

    if not query:
        return {
            "query": query,
            "resolved_feeds": [],
            "message": "Empty query provided",
        }

    feeds = resolve_search_term(query)

    return {
        "query": query,
        "resolved_feed_count": len(feeds),
        "resolved_feeds": feeds,
    }
