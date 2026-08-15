import re

from fastapi import FastAPI, Request, Response
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


@app.middleware("http")
async def dev_cors_fallback(request: Request, call_next):
    origin = request.headers.get("origin")
    try:
        if request.method == "OPTIONS" and _is_allowed_dev_origin(origin):
            response = Response(status_code=204)
        else:
            response = await call_next(request)
    except Exception as exc:
        response = Response(
            content=f'{{"detail":"Error interno: {str(exc)}"}}',
            media_type="application/json",
            status_code=500,
        )

    if _is_allowed_dev_origin(origin):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = request.headers.get(
            "access-control-request-headers",
            "authorization,content-type",
        )
        response.headers["Vary"] = "Origin"
    return response


def _is_allowed_dev_origin(origin: str | None) -> bool:
    if not origin:
        return False
    if origin in settings.cors_origins:
        return True
    return bool(re.match(r"^https://[a-z0-9-]+\.(?:use2\.)?devtunnels\.ms$", origin))


app.include_router(router, prefix="/api/v1/noticias", tags=["Noticias"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "noticias"}
