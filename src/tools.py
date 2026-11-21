import logging
import re

from strands import tool

from src.models import Article
from src.scrappers.infobae import InfobaeScraper
from src.utils import format_articles

logger = logging.getLogger(__name__)

NO_ARTICLES_MESSAGE = "No se pudo encontrar articulos"
NO_CONTENT_MESSAGE = "No se pudo obtener el contenido del artículo"

_LINK_PLACEHOLDER_RE = re.compile(r"\[([^\]]+)\]\(#(\d+)\)")
_cached_articles: list[Article] = []


def resolve_article_links(text: str) -> str:
    """Reemplaza placeholders `[texto](#N)` por la URL canónica cacheada."""

    def _replace(match: re.Match[str]) -> str:
        label, index_str = match.group(1), match.group(2)
        index = int(index_str)
        if 1 <= index <= len(_cached_articles):
            return f"[{label}]({_cached_articles[index - 1].url})"
        return match.group(0)

    return _LINK_PLACEHOLDER_RE.sub(_replace, text)


@tool
def get_infobae_articles(limit: int = 10) -> str:
    """Obtiene los últimos artículos de la portada de Infobae para informarse de las noticias del día.

    Args:
        limit: Cantidad máxima de artículos a obtener (opcional, por defecto 10).

    Returns:
        Un string con un artículo por línea, con el formato:
        #N título | url | bajada (la bajada es opcional y puede no estar).
        Si devuelve "No se pudo encontrar articulos", hubo un error con la tool:
        no inventes noticias, avisá que no se pudo obtener la información.
    """
    try:
        articles = InfobaeScraper().get_latest_articles(limit=limit)
    except Exception:
        logger.exception("Error obteniendo artículos de Infobae")
        return NO_ARTICLES_MESSAGE
    if not articles:
        return NO_ARTICLES_MESSAGE
    _cached_articles.clear()
    _cached_articles.extend(articles)
    return format_articles(articles)


@tool
def get_infobae_articles_content(article_ids: list[int]) -> str:
    """Obtiene el contenido completo en texto plano de varias notas de Infobae por su número de índice.

    Args:
        article_ids: Lista de números enteros (#N) devueltos por get_infobae_articles
            (por ejemplo: [1, 3, 5, 11]).

    Returns:
        El cuerpo de cada nota en texto plano separado por "---", con su título y URL canónica,
        o "No se pudo obtener el contenido del artículo" si no se pudo leer ninguna nota.
    """
    scraper = InfobaeScraper()
    seen_ids: set[int] = set()
    results: list[str] = []

    for aid in article_ids:
        if isinstance(aid, bool) or not isinstance(aid, int) or not (1 <= aid <= len(_cached_articles)):
            logger.warning("Índice de artículo inválido: %s (disponibles: %d)", aid, len(_cached_articles))
            continue
        if aid in seen_ids:
            continue
        seen_ids.add(aid)

        article = _cached_articles[aid - 1]
        try:
            content = scraper.get_article_content(article.url, max_chars=2500)
        except Exception:
            logger.exception("Error obteniendo contenido de %s", article.url)
            continue
        if content:
            results.append(f"### #{aid} {article.title}\nURL: {article.url}\n\n{content}")

    if not results:
        return NO_CONTENT_MESSAGE
    return "\n\n---\n\n".join(results)
