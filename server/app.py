"""Proxy module — re-exports the FastAPI app for uvicorn."""
from .app.main import app, main as backend_main

def main() -> None:
    backend_main()

if __name__ == "__main__":
    main()
