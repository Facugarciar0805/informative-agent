from src.agent import create_agent


def main() -> None:
    agent = create_agent()
    agent("Contame qué pasó hoy")


if __name__ == "__main__":
    main()
