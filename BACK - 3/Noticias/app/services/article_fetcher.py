from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings
from app.schemas.news import UrlHealth


class FetchError(RuntimeError):
    pass


@dataclass(frozen=True)
class FetchedPage:
    html: str
    final_url: str
    url_health: UrlHealth


async def fetch_html(url: str) -> FetchedPage:
    try:
        return await _fetch_with_httpx(url)
    except ModuleNotFoundError:
        return _fetch_with_urllib(url)


async def _fetch_with_httpx(url: str) -> FetchedPage:
    import httpx

    headers = {
        "User-Agent": "AMA-LLU-IA-NewsAnalyzer/0.1 (+https://localhost)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    limits = httpx.Limits(max_connections=5, max_keepalive_connections=2)
    timeout = httpx.Timeout(settings.request_timeout_seconds)

    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout, limits=limits) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise FetchError(f"No se pudo descargar la noticia: {exc}") from exc

    _validate_html_response(response.headers.get("content-type", ""), response.content)
    return _fetched_page(response.text, url, str(response.url), response.status_code, len(response.history))


def _fetch_with_urllib(url: str) -> FetchedPage:
    request = Request(
        url,
        headers={
            "User-Agent": "AMA-LLU-IA-NewsAnalyzer/0.1 (+https://localhost)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urlopen(request, timeout=settings.request_timeout_seconds) as response:
            content = response.read(settings.max_html_bytes + 1)
            content_type = response.headers.get("content-type", "")
            final_url = response.geturl()
            status_code = response.status
    except HTTPError as exc:
        raise FetchError(f"No se pudo descargar la noticia: HTTP {exc.code}") from exc
    except URLError as exc:
        raise FetchError(f"No se pudo descargar la noticia: {exc.reason}") from exc

    _validate_html_response(content_type, content)
    encoding = response.headers.get_content_charset() or "utf-8"
    text = content.decode(encoding, errors="replace")
    redirect_count = 1 if final_url != url else 0
    return _fetched_page(text, url, final_url, status_code, redirect_count)


def _validate_html_response(content_type: str, content: bytes) -> None:
    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        raise FetchError("La URL no parece ser una pagina HTML de noticia.")
    if len(content) > settings.max_html_bytes:
        raise FetchError("La pagina supera el tamano maximo permitido.")


def _fetched_page(html: str, original_url: str, final_url: str, status_code: int, redirect_count: int) -> FetchedPage:
    warnings: list[str] = []
    if redirect_count:
        warnings.append("La URL redirige antes de mostrar la noticia.")
    return FetchedPage(
        html=html,
        final_url=final_url,
        url_health=UrlHealth(
            status="redirected" if redirect_count else "active",
            http_status=status_code,
            is_reachable=True,
            is_disconnected=False,
            redirect_count=redirect_count,
            warnings=warnings,
        ),
    )
