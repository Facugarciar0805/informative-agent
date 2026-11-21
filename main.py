import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from src.notifiers.telegram import TelegramNotifier
from src.service import run_daily_briefing

LOG_PATH = Path(__file__).resolve().parent / "logs" / "briefing.log"
logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    """Configura logging en consola y archivo para ejecuciones desatendidas."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_PATH, encoding="utf-8"),
        ],
    )
    logging.getLogger("src").setLevel(logging.INFO)
    logger.setLevel(logging.INFO)


def main() -> None:
    _configure_logging()
    load_dotenv()
    notifier = TelegramNotifier(
        bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
        chat_id=os.environ["TELEGRAM_CHAT_ID"],
    )
    try:
        run_daily_briefing(notifier)
    except Exception:
        logger.exception("Error fatal ejecutando el resumen diario")
        raise


if __name__ == "__main__":
    main()
