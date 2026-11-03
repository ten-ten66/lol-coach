from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from lol_coach import __version__
from lol_coach.api.champions import router as champions_router
from lol_coach.api.draft import router as draft_router
from lol_coach.api.health import router as health_router
from lol_coach.api.leaderboard import router as leaderboard_router
from lol_coach.api.summoner import router as summoner_router
from lol_coach.config import get_settings
from lol_coach.riot.errors import RiotAPIError

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    log.info("startup", env=settings.environment, version=__version__)
    yield
    log.info("shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RiotAPIError)
    async def _riot_api_error(_: Request, exc: RiotAPIError) -> JSONResponse:
        # Translate upstream Riot errors into clean HTTP statuses so clients can
        # distinguish "not found" / "key expired" / "rate limited" from a real 500.
        status = exc.status_code if exc.status_code in (400, 401, 403, 404, 429) else 502
        return JSONResponse(status_code=status, content={"detail": str(exc)})

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(summoner_router, prefix="/api/v1")
    app.include_router(champions_router, prefix="/api/v1")
    app.include_router(draft_router, prefix="/api/v1")
    app.include_router(leaderboard_router, prefix="/api/v1")
    return app


app = create_app()
