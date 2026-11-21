from collections.abc import Sequence
import logging
import time

from google.genai.errors import ServerError
from strands.types.exceptions import EventLoopException

from src.agent import create_agent
from src.notifiers.base import Notifier

logger = logging.getLogger(__name__)

DEFAULT_PROMPT = "Contame qué pasó hoy"
DEFAULT_RETRY_DELAYS: tuple[int, ...] = (10, 25, 45)


def _is_transient_server_error(exc: Exception) -> bool:
    """Indica si la excepción corresponde a un error transitorio del servidor (5xx)."""
    if isinstance(exc, ServerError):
        return True
    if isinstance(exc, EventLoopException):
        return isinstance(exc.original_exception, ServerError) or isinstance(exc.__cause__, ServerError)
    return False


def generate_daily_briefing(
    prompt: str = DEFAULT_PROMPT,
    retry_delays: Sequence[int] = DEFAULT_RETRY_DELAYS,
) -> str:
    """Genera el resumen diario del agente con reintentos ante errores transitorios del modelo."""
    total_attempts = len(retry_delays) + 1
    for attempt in range(total_attempts):
        agent = create_agent()
        try:
            result = agent(prompt)
            return str(result)
        except Exception as exc:
            if not _is_transient_server_error(exc) or attempt == total_attempts - 1:
                raise
            delay = retry_delays[attempt]
            logger.warning(
                "Error transitorio del modelo (intento %d/%d): %s. Reintentando en %ds...",
                attempt + 1,
                total_attempts,
                exc,
                delay,
            )
            time.sleep(delay)

    raise RuntimeError("No se pudo generar el resumen diario")


def run_daily_briefing(
    notifier: Notifier,
    prompt: str = DEFAULT_PROMPT,
    retry_delays: Sequence[int] = DEFAULT_RETRY_DELAYS,
) -> str:
    """Genera el resumen diario y lo envía por el canal de notificación configurado."""
    summary = generate_daily_briefing(prompt=prompt, retry_delays=retry_delays)
    notifier.send(summary)
    logger.info("Resumen diario enviado correctamente.")
    return summary
