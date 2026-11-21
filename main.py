import logging

from src.service import generate_daily_briefing


def main() -> None:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logging.getLogger("src").setLevel(logging.INFO)
    generate_daily_briefing()


if __name__ == "__main__":
    main()
