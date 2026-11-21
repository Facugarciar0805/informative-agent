from collections.abc import Sequence
import logging
import os
import time

from dotenv import load_dotenv
from google.genai.errors import ServerError
from strands.types.exceptions import EventLoopException

from src.agent import create_agent
from src.notifiers.base import Notifier
from src.tools import resolve_article_links

logger = logging.getLogger(__name__)

DEFAULT_PROMPT = "Contame qué pasó hoy"
DEFAULT_RETRY_DELAYS: tuple[int, ...] = (10, 25, 45)
DEFAULT_FALLBACK_MODELS: tuple[str, ...] = ("gemini-3.6-flash", "gemini-3.8-flash")


def _is_transient_server_error(exc: Exception) -> bool:
    """Indica si la excepción corresponde a un error transitorio del servidor (5xx)."""
    if isinstance(exc, ServerError):
        return True
    if isinstance(exc, EventLoopException):
        return isinstance(exc.original_exception, ServerError) or isinstance(exc.__cause__, ServerError)
    return False


def _resolve_model_candidates(
    primary_model: str | None,
    fallback_models: Sequence[str] | None,
) -> list[str]:
    """Arma la lista ordenada y sin duplicados de modelos primario y de respaldo."""
    if primary_model is None or fallback_models is None:
        load_dotenv()

    primary = primary_model or os.environ["GEMINI_MODEL"]
    if fallback_models is None:
        raw_fallbacks = os.environ.get("GEMINI_FALLBACK_MODELS", "")
        parsed = [m.strip() for m in raw_fallbacks.split(",") if m.strip()]
        fallbacks: Sequence[str] = parsed or DEFAULT_FALLBACK_MODELS
    else:
        fallbacks = fallback_models

    candidates: list[str] = []
    for model_id in [primary, *fallbacks]:
        if model_id and model_id not in candidates:
            candidates.append(model_id)
    return candidates


def generate_daily_briefing(
    prompt: str = DEFAULT_PROMPT,
    retry_delays: Sequence[int] = DEFAULT_RETRY_DELAYS,
    primary_model: str | None = None,
    fallback_models: Sequence[str] | None = None,
) -> str:
    """Genera el resumen diario con reintentos y fallback entre modelos ante errores transitorios."""
    models = _resolve_model_candidates(primary_model, fallback_models)
    total_attempts = len(retry_delays) + 1

    for model_idx, model_id in enumerate(models):
        has_fallback = model_idx < len(models) - 1
        for attempt in range(total_attempts):
            logger.info(
                "Generando resumen diario con modelo %s (intento %d/%d)...",
                model_id,
                attempt + 1,
                total_attempts,
            )
            agent = create_agent(model_id=model_id)
            try:
                result = agent(prompt)
                return resolve_article_links(str(result))
            except Exception as exc:
                if not _is_transient_server_error(exc):
                    raise
                if attempt < total_attempts - 1:
                    delay = retry_delays[attempt]
                    logger.warning(
                        "Error transitorio con %s (intento %d/%d): %s. Reintentando en %ds...",
                        model_id,
                        attempt + 1,
                        total_attempts,
                        exc,
                        delay,
                    )
                    time.sleep(delay)
                elif has_fallback:
                    logger.warning(
                        "Modelo %s no disponible tras %d intentos; probando siguiente modelo de respaldo...",
                        model_id,
                        total_attempts,
                    )
                else:
                    raise

    raise RuntimeError("No se pudo generar el resumen diario")


def run_daily_briefing(
    notifier: Notifier,
    prompt: str = DEFAULT_PROMPT,
    retry_delays: Sequence[int] = DEFAULT_RETRY_DELAYS,
    primary_model: str | None = None,
    fallback_models: Sequence[str] | None = None,
) -> str:
    """Genera el resumen diario y lo envía por el canal de notificación configurado."""
    summary = generate_daily_briefing(
        prompt=prompt,
        retry_delays=retry_delays,
        primary_model=primary_model,
        fallback_models=fallback_models,
    )
    notifier.send(summary)
    logger.info("Resumen diario enviado correctamente.")
    return summary
