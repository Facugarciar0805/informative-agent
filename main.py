import logging
import os

from dotenv import load_dotenv

from src.notifiers.telegram import TelegramNotifier
from src.service import run_daily_briefing


def main() -> None:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logging.getLogger("src").setLevel(logging.INFO)
    load_dotenv()
    notifier = TelegramNotifier(
        bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
        chat_id=os.environ["TELEGRAM_CHAT_ID"],
    )
    run_daily_briefing(notifier)


if __name__ == "__main__":
    main()
