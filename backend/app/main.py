from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect

from .config import CORS_ORIGINS, SIMULATED_MODE
from .db import Base, engine
from .routers import demo, field, geography, organisations, public, verification, volunteers


@asynccontextmanager
async def lifespan(_: FastAPI):
    # First run: create tables and load the simulated demo.
    if not inspect(engine).has_table("users"):
        from .seed import reset
        reset()
    else:
        Base.metadata.create_all(engine)
    yield


app = FastAPI(title="VeraVote API", version="0.1.0", lifespan=lifespan,
              description="Election evidence, verification and public transparency. Hackathon MVP — "
                          "all data is SIMULATED; no live INEC or IReV integration.")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"],
                   expose_headers=["X-Evidence-SHA256"])

for r in (geography.router, public.router, volunteers.router, field.router, verification.router,
          organisations.router, demo.router):
    app.include_router(r)


@app.get("/health")
def health():
    return {"ok": True, "simulated": SIMULATED_MODE}
