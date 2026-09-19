# Meraki

A modular, plugin-based backend framework built with Python. 

## About

Meraki is a community-driven backend framework focused on modularity and extensibility through a plugin system.

## Tech Stack

- Python

## Status

> Phase 1 MVP implemented — ASGI core, routing, middleware, plugins, config, errors, and the database extension. See `SRS.md` and `docs/PHASE1.md`.

## Features

- ASGI application core served by Uvicorn (`Meraki` object, lifespan startup/shutdown)
- Routing for all standard methods with path params (`{id}`, `{id:int}`, `{id:float}`, `{id:path}`, `{id:uuid}`), 404/405 handling, router prefixes
- Request/Response abstractions (query, headers, cookies, JSON/form bodies, `JSONResponse`)
- Composable middleware pipeline + built-ins (logger, CORS with preflight, trusted hosts)
- Plugin system (`Plugin` base, `PluginManager`, services via `app.state`, lifecycle hooks)
- Centralized `Settings` (defaults, `MERAKI_` env vars, overrides)
- Centralized error handling (`HTTPException` hierarchy, custom handlers, debug mode)
- Database extension: `DatabaseConnector` strategy interface + SQLite (stdlib), PostgreSQL, MySQL, SQL Server implementations

## Getting Started

### Clone the repository

```bash
git clone https://github.com/sulfurcodes/Meraki.git
cd Meraki
```

### Install and run the example

```bash
pip install -e .[test]
uvicorn examples.basic:app --reload
curl http://127.0.0.1:8000/users/42
```

### Minimal app

```python
from meraki import Meraki

app = Meraki()

@app.get("/hello")
def hello(request):
    return {"message": "hi"}
```

### Run tests

```bash
pytest
```

## Contribution

[![Discord](https://img.shields.io/badge/Discord-%237289DA.svg?logo=discord&logoColor=white)](https://discord.gg/Pcj8vq6Rru)

## License

MIT