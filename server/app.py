"""Proxy file to satisfy openenv static paths check."""
from .app import main as backend_main

def main() -> None:
    backend_main.main()

if __name__ == "__main__":
    main()
