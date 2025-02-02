import httpx
import logging
import os

logger = logging.getLogger(__name__)

API_KEY = os.getenv("GOOGLE_API_KEY")
CSE_ID = os.getenv("GOOGLE_CSE_ID")


async def google_search(query: str) -> list[dict[str, str]]:
    """Searches Google and extracts essential information.

    Args:
        query (str): The key phrase to search for.

    Returns:
        list[dict[str, Any]]: A list of extracted search results with title, link and snippet
    """
    logger.info(f"Searching for: {query}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={"q": query, "key": API_KEY, "cx": CSE_ID, "num": 10},
            )
        logger.debug(f"Google Search API status code: {response.status_code}")

        if response.status_code == 200:
            items = response.json().get("items", [])
            logger.debug(f"Number of results: {len(items)}")
            return [
                {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                }
                for item in items
            ]
        else:
            logger.error(f"Google API error: {response.text}")
            return []
    except Exception:
        logger.exception("Exception calling Google Search API")
        return []
