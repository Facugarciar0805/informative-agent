import re
from typing import List, Set
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from src.models import Article


class InfobaeScraper:
    """Scraper específico para la portada de Infobae."""
    BASE_URL: str = "https://www.infobae.com"
    _DATE_PATTERN = re.compile(r"/\d{4}/\d{2}/\d{2}/")

    def __init__(self, timeout: int = 15):
        # Inyección de configuración simple: permite cambiar el timeout en tests
        self.timeout = timeout

    def get_latest_articles(self, limit: int = 10) -> List[Article]:
        """Obtiene las notas principales de la portada (tarjetas `story-card-ctn`)."""
        resp = requests.get(self.BASE_URL, timeout=self.timeout)
        resp.raise_for_status()  # si Infobae responde 4xx/5xx, la excepción sube al llamador
        soup = BeautifulSoup(resp.text, "html.parser")

        articles: List[Article] = []
        seen: Set[str] = set()  # URLs ya vistas, para no repetir notas

        for a in soup.select("a.story-card-ctn"):
            url = urljoin(self.BASE_URL, a["href"])
            h2 = a.find("h2")
            if not self._DATE_PATTERN.search(url):
                continue  # no es una nota fechada (ej: video de YouTube)
            if url in seen or h2 is None:
                continue  # duplicada o tarjeta sin título

            h3 = a.find("h3")  # la bajada es opcional
            articles.append(Article(
                title=h2.get_text(strip=True),
                url=url,
                summary=h3.get_text(strip=True) if h3 else None,
            ))
            seen.add(url)

            if len(articles) >= limit:
                break

        return articles

