import re
from typing import List, Set
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from src.models import Article


class InfobaeScraper:
    """Scraper específico para la portada de Infobae."""
    BASE_URL: str = "https://www.infobae.com"
    HOME_URL: str = "https://www.infobae.com/?noredirect"
    _DATE_PATTERN = re.compile(r"/\d{4}/\d{2}/\d{2}/")
    _WHITESPACE_PATTERN = re.compile(r"[ \t]+")

    def __init__(self, timeout: int = 15):
        # Inyección de configuración simple: permite cambiar el timeout en tests
        self.timeout = timeout

    def get_latest_articles(self, limit: int = 10) -> List[Article]:
        """Obtiene las notas principales de la portada (tarjetas `story-card-ctn`)."""
        resp = requests.get(self.HOME_URL, timeout=self.timeout)
        resp.raise_for_status()  # si Infobae responde 4xx/5xx, la excepción sube al llamador
        soup = BeautifulSoup(resp.text, "html.parser")

        articles: List[Article] = []
        seen: Set[str] = set()  # URLs ya vistas, para no repetir notas

        for a in soup.select("a.story-card-ctn"):
            href = a.get("href")
            if not isinstance(href, str) or not href:
                continue
            url = urljoin(self.BASE_URL, href)
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

    def get_article_content(self, url: str, max_chars: int = 4000) -> str:
        """Obtiene el cuerpo en texto plano de una nota de Infobae."""
        netloc = urlparse(url).netloc.lower()
        if netloc != "infobae.com" and not netloc.endswith(".infobae.com"):
            raise ValueError(f"URL no pertenece a Infobae: {url}")

        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        paragraphs_tags = soup.select("p.paragraph") or soup.select("div.body-article p")
        paragraphs = []
        for p in paragraphs_tags:
            text = self._WHITESPACE_PATTERN.sub(" ", p.get_text(" ", strip=True)).strip()
            if text:
                paragraphs.append(text)

        content = "\n\n".join(paragraphs)
        if len(content) > max_chars:
            content = content[:max_chars].rstrip() + "..."
        return content

