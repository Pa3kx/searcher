import pytest
import httpx
import respx

from searcher import search


@pytest.mark.asyncio
async def test_google_search_success():
    query = "python"
    fake_items = [
        {"title": "Python", "link": "https://python.org", "snippet": "Python website"}
        for _ in range(10)
    ]

    fake_response = {"items": fake_items}

    with respx.mock() as mock:
        route = mock.get("https://www.googleapis.com/customsearch/v1").respond(
            json=fake_response, status_code=200
        )
        results = await search.google_search(query)
        assert results == fake_items
        assert route.called


@pytest.mark.asyncio
async def test_google_search_non_200():
    """Ensure that google_search() correctly handles a 400 Bad Request response by returning an empty list."""
    query = "python"
    with respx.mock() as mock:
        mock.get("https://www.googleapis.com/customsearch/v1").respond(
            json={"error": "bad request"}, status_code=400
        )
        results = await search.google_search(query)
        assert results == []


@pytest.mark.asyncio
async def test_google_search_exception(monkeypatch):
    """Ensure that google_search() correctly handles a an exception by returning an empty list."""
    query = "python"

    async def fake_get(*args, **kwargs):
        raise Exception("Test exception")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    results = await search.google_search(query)
    assert results == []
