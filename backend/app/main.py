"""FastAPI application entrypoint for Loreweaver v3."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import create_db_and_tables, engine
from .routers import agent, auth, heroes, users
from .seed import seed_initial_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once on startup: create tables and seed the world.
    create_db_and_tables()
    seed_initial_data(engine)
    yield


app = FastAPI(title="Loreweaver API", version="0.3.0 (v3)", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(heroes.router)
app.include_router(agent.router)


@app.get("/", tags=["meta"])
def root():
    return {"app": "Loreweaver", "phase": "v3", "docs": "/docs"}
