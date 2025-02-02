# test_app.py

import json
import uuid
import asyncio
import pytest
from fastapi.testclient import TestClient
from fastapi.responses import Response

# Import the entire module containing the endpoints so we can patch its globals.
# (Assume the main file is named "app.py".)
import searcher.main as main
from searcher.main import SESSION_COOKIE_NAME, SESSION_TTL

# === Fake dependencies ===

class FakeRedis:
    """
    A simple in-memory substitute for the Redis client.
    This ignores the TTL (time-to-live) and simply stores values in a dict.
    """
    def __init__(self):
        self.store = {}

    async def setex(self, key, ttl, value):
        self.store[key] = value

    async def get(self, key):
        return self.store.get(key)


async def fake_google_search(query: str):
    """
    A fake search function that always returns a fixed result.
    """
    return [{"title": "Fake Result", "url": "http://fake.com"}]


def fake_file_response(path: str):
    """
    A fake FileResponse that returns a plain text response.
    This bypasses the need for a physical file on disk.
    """
    return Response(content="Fake index file content", media_type="text/html")


def fake_template_response(template_name: str, context: dict):
    """
    A fake TemplateResponse function that returns a plain text response
    incorporating the template name and (fake) search items.
    """
    content = f"Template: {template_name}, Search items: {context.get('search_items')}"
    return Response(content=content, media_type="text/html")


# === Fixtures and Monkeypatching ===

@pytest.fixture(autouse=True)
def setup_monkeypatch(monkeypatch):
    """
    Replace external dependencies with our fake versions.
    Since the Redis client is a module-level variable (and not attached to the FastAPI app),
    we import the module (as main) and replace its global 'redis_client'.
    """
    fake_redis = FakeRedis()
    monkeypatch.setattr(main, "redis_client", fake_redis)
    monkeypatch.setattr(main, "google_search", fake_google_search)
    monkeypatch.setattr(main, "FileResponse", fake_file_response)
    monkeypatch.setattr(main.templates, "TemplateResponse", fake_template_response)


@pytest.fixture
def client():
    """
    Returns a TestClient instance for our FastAPI app.
    """
    return TestClient(main.app)


# === Tests ===

def test_root_endpoint(client):
    """
    Test that GET "/" returns a 200 response with the fake file content
    and does not set a session cookie (because the endpoint does not depend on session).
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "Fake index file content" in response.text
    # The root endpoint does not call the session dependency, so no session cookie is set.
    assert SESSION_COOKIE_NAME not in response.cookies


def test_search_endpoint_valid_query(client):
    """
    Test that GET "/search" with a valid query:
      - Returns a 200 response.
      - Calls our fake google_search (which returns a known result).
      - Renders a (fake) template that includes the search results.
      - Sets a session cookie.
      - Stores the results in the fake Redis client.
    """
    response = client.get("/search?query=test")
    assert response.status_code == 200
    # Our fake template response includes the fake search result.
    assert "Fake Result" in response.text
    # A new session cookie should be set.
    assert SESSION_COOKIE_NAME in response.cookies

    session_id = response.cookies.get(SESSION_COOKIE_NAME)
    # Verify that our fake Redis has stored the search results.
    stored_value = asyncio.run(main.redis_client.get(session_id))
    expected_value = json.dumps([{"title": "Fake Result", "url": "http://fake.com"}])
    assert stored_value == expected_value


def test_search_endpoint_missing_query(client):
    """
    Test that GET "/search" without providing the required query parameter
    returns a 422 Unprocessable Entity error.
    """
    response = client.get("/search")
    assert response.status_code == 422


def test_download_endpoint_with_results(client):
    """
    Test that GET "/download" returns a downloadable JSON file when search results
    exist for the session. We simulate the situation by manually inserting a fake
    search result in the fake Redis client and sending the matching session cookie.
    """
    fake_redis = main.redis_client
    test_session_id = str(uuid.uuid4())
    fake_results = [{"title": "Fake Download", "url": "http://download.com"}]
    asyncio.run(fake_redis.setex(test_session_id, SESSION_TTL, json.dumps(fake_results)))

    client.cookies.set(SESSION_COOKIE_NAME, test_session_id)
    response = client.get("/download")
    assert response.status_code == 200
    # Check that the appropriate headers are set.
    assert response.headers.get("Content-Disposition") == "attachment; filename=search_results.json"
    assert response.headers.get("Content-Type") == "application/json"
    # Verify the JSON structure in the response.
    data = json.loads(response.content)
    assert "result1" in data
    assert data["result1"] == fake_results[0]


def test_download_endpoint_without_results(client):
    """
    Test that GET "/download" returns a 404 error when no search results
    are available in the session (i.e. the session key is missing from Redis).
    """
    test_session_id = str(uuid.uuid4())
    client.cookies.set(SESSION_COOKIE_NAME, test_session_id)
    response = client.get("/download")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Session expired or no search results available"


def test_download_endpoint_without_cookie(client):
    """
    Test that when no session cookie is provided to GET "/download", the dependency
    creates one (the response should set a session cookie) but, since there are no search
    results in Redis for that session, a 404 error is returned.
    """
    response = client.get("/download")
    assert response.status_code == 404
    # A new session cookie should be set even if there are no stored results.
    assert SESSION_COOKIE_NAME in response.cookies
