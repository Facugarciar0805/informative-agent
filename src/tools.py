from strands import tool

from src.scrappers.infobae import InfobaeScraper
from src.utils import format_articles

NO_ARTICLES_MESSAGE = "No se pudo encontrar articulos"


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
        return NO_ARTICLES_MESSAGE
    if not articles:
        return NO_ARTICLES_MESSAGE
    return format_articles(articles)
