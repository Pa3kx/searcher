FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# allow __pycache__
# Copy files instead of hardlinklink
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# First copy files specifying dependencies and install them
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Copy and install rest
COPY . .
RUN uv sync --frozen --no-dev

# Ensure the virtual environment’s binaries are in the PATH so that commands like `uvicorn` are found.
ENV PATH="/app/.venv/bin:$PATH"

# Clear any inherited entrypoint to avoid unexpected behavior.
ENTRYPOINT []

CMD ["uvicorn", "searcher.main:app", "--host", "0.0.0.0", "--port", "8000"]
