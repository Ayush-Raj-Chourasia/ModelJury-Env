"""Proxy file to satisfy openenv static paths check."""
from .app.main import app, main

if __name__ == "__main__":
    main()
