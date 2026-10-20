from typing import List
from src.models import Article


def format_articles(articles: List[Article]) -> str:
    """Convierte una lista de artículos en texto plano para pasárselo al agente.

    Formato, un artículo por línea:
        #1 Título | URL | Bajada
    Si el artículo no tiene bajada, se omite ese campo.
    """
    lines = []
    for i, article in enumerate(articles, start=1):
        parts = [f"#{i} {article.title}", article.url]
        if article.summary:
            parts.append(article.summary)
        lines.append(" | ".join(parts))
    return "\n".join(lines)
