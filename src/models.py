from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Article:
    title: str
    url: str
    summary: Optional[str] = None