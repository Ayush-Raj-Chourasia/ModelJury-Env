"""Proxy module — re-exports the FastAPI app for uvicorn."""
from .app.main import app, main

if __name__ == "__main__":
    main()
