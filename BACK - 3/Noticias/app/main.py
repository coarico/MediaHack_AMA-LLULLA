from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings


app = FastAPI(
    title="AMA-LLU-IA Noticias API",
    description="Analisis profundo de noticias por URL con keywords y noticias relacionadas.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1/noticias", tags=["Noticias"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "noticias"}
