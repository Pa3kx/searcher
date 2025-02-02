import logging
import json
import uuid
import asyncio

from fastapi import FastAPI, Query, Response, HTTPException, Request, Depends
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import redis.asyncio as redis

from searcher.search import google_search

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_client = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)

SESSION_COOKIE_NAME = "session_id"
SESSION_TTL = 3600  # invalidate session after one hour

# Initialize FastAPI app and mount static files and templates
app = FastAPI(
    title="Searcher",
    description="API that handles Google searches and downloads using Google Custom Search Engine and Google API key.",
    version="0.1.0",
    openapi_tags=[
        {"name": "Search", "description": "Endpoints related to searching operations."},
        {"name": "Download", "description": "Endpoints for downloading results."},
    ],
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def get_session_id(request: Request) -> str:
    if not (session_id := request.cookies.get(SESSION_COOKIE_NAME)):
        session_id = str(uuid.uuid4())
        logger.info(f"Session ID generated: {session_id}")
        # Store the new session id in request.state so the middleware can set it later.
        request.state.session_id = session_id
    return session_id


@app.middleware("http")
async def add_session_cookie(request: Request, call_next):
    # Process the request and get the response from the endpoint.
    response = await call_next(request)

    # If the dependency generated a new session ID, attach it as a cookie.
    if hasattr(request.state, "session_id"):
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=request.state.session_id,
            max_age=SESSION_TTL,
            httponly=True,
        )
    return response


@app.get("/", tags=["Search"])
async def serve_frontend() -> FileResponse:
    """
    Serves the static homepage.

    Returns:
        FileResponse: The index.html file from the static directory.
    """
    return FileResponse("static/index.html")


@app.get("/search", response_class=HTMLResponse, tags=["Search"])
async def search(
    request: Request,
    response: Response,
    query: str = Query(..., min_length=1),
    session_id: str = Depends(get_session_id),
) -> HTMLResponse:
    """
    Executes a search based on the query and returns the results.

    Args:
        request (Request): The request object.
        response (Response): The response object.
        query (str): The search keyword provided by the user.
        session_id (str): The session identifier (retrieved via dependency injection).

    Returns:
        HTMLResponse: The rendered search results page with the search items.
    """
    logger.info(query)
    new_results = await google_search(query)

    await redis_client.setex(session_id, SESSION_TTL, json.dumps(new_results))

    return templates.TemplateResponse(
        "results.html", {"request": request, "search_items": new_results}
    )


@app.get("/download", tags=["Download"])
async def download_json(
    request: Request, response: Response, session_id: str = Depends(get_session_id)
) -> Response:
    """
    Provides a JSON file containing search results stored in the session.

    Args:
        request (Request): The request object.
        response (Response): The response object.
        session_id (str): The session identifier (retrieved via dependency injection).

    Returns:
        Response: A downloadable JSON file containing search results.

    Raises:
        HTTPException: If no search results are found for the session.
    """
    logger.info(f"session ID for download: {session_id}")

    if data := await redis_client.get(session_id):
        search_items = json.loads(data)
    else:
        search_items = []

    if not search_items:
        raise HTTPException(
            status_code=404, detail="Session expired or no search results available"
        )

    json_items = json.dumps(
        {f"result{i + 1}": item for i, item in enumerate(search_items)}, indent=4
    )
    response.headers["Content-Disposition"] = "attachment; filename=search_results.json"
    response.headers["Content-Type"] = "application/json"
    response.body = json_items.encode("utf-8")
    response.status_code = 200
    return response
