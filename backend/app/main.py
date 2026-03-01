from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown


app = FastAPI(title="AI Assistant", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
