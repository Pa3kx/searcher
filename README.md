# 🔎 Searcher

A simple FastAPI-based search service that fetches results using Google's Custom Search API and provides an interactive web interface.

## 🚀 Getting Started

### 1️⃣ Clone the Repository

    git clone https://github.com/Pa3kx/searcher.git
    cd searcher

### 2️⃣ Set Up Environment Variables

Create a `.env` file in the project root and add your Google API credentials:

    GOOGLE_API_KEY=yourapikey
    GOOGLE_CSE_ID=yourcseid

### 3️⃣ Run the Application with Docker

Use `docker-compose` to build and start the containerized application:

    docker-compose up --build


## 📖 API Documentation

FastAPI automatically generates API documentation that you can access in your browser:

- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
  (Interactive API explorer with request testing.)

- **ReDoc UI:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)  
  (Alternative clean and structured API documentation.)


## 🛠️ Features

- ✅ Search via Google's Custom Search API
- ✅ Store search results in session (Redis)
- ✅ Download search results as JSON

## 📜 Dependencies

- 📡 **[requests](https://github.com/psf/requests)** - Simplifies making HTTP requests, great for API calls.
- ⚡ **[fastapi](https://github.com/fastapi/fastapi)** - High-performance web framework for building modern APIs.
- 🦄 **[uvicorn](https://github.com/encode/uvicorn)** - ASGI server for running FastAPI applications with high concurrency.
- 🐱‍👤 **[jinja2](https://github.com/pallets/jinja)** - A powerful templating engine for rendering dynamic HTML.
- 🎲 **[redis](https://github.com/redis/redis)** - In-memory data store for caching, message brokering, and fast lookups.
- ⛰️ **[alpine.js](https://github.com/alpinejs/alpine)** - Lightweight JavaScript framework for adding interactivity.
- 🌐 **[htmx](https://github.com/bigskysoftware/htmx)** - Enhances HTML with AJAX, WebSockets, and modern dynamic capabilities.
- 📦 **[uv](https://github.com/astral-sh/uvt)** - Modern Python packaging tool written in Rust for blazingly fast performance
- 🐳 **[Docker](https://github.com/docker/docker-ce)** - Containerization platform for building, shipping, and running applications.
- 🏗️ **[Docker Compose](https://github.com/docker/compose)** - Tool for defining and running multi-container Docker applications.