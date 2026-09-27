from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.database.mongo import ensure_indexes, get_client
from app.api.v1 import vocabulary, model_status, auth, recognize, translate
from app.websocket import recognize_ws

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Fails loudly if MongoDB isn't reachable, rather than the app coming
    # up "healthy" and every DB-touching request failing individually.
    get_client().admin.command("ping")
    ensure_indexes()


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}


app.include_router(vocabulary.router, prefix="/api/v1")
app.include_router(model_status.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(recognize.router, prefix="/api/v1")
app.include_router(translate.router, prefix="/api/v1")
app.include_router(recognize_ws.router)
