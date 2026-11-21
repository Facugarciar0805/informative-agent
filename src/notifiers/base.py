from typing import Protocol


class Notifier(Protocol):
    """Contrato que debe cumplir cualquier canal de entrega de resúmenes."""

    def send(self, message: str) -> None:
        """Envía un mensaje en Markdown al canal configurado."""
        ...
