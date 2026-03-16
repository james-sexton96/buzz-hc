"""FastAPI application factory with lifespan and CORS."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.database import init_db
from api.routes.config import router as config_router
from api.routes.export import router as export_router
from api.routes.run import router as run_router
from api.routes.sessions import router as sessions_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Buzz-HC API",
        description="Multi-agent pharma market research — REST + SSE API",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS — allow the Next.js dev server and any configured frontend origin
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    extra_origin = os.environ.get("FRONTEND_URL", "").strip()
    if extra_origin:
        origins.append(extra_origin)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(run_router)
    app.include_router(sessions_router)
    app.include_router(export_router)
    app.include_router(config_router)

    return app


app = create_app()
