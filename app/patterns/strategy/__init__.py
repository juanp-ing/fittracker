"""Exportación del patrón Strategy de FitTracker."""

from app.patterns.strategy.pr_strategy import (
    PRStrategy,
    PesoMaximoStrategy,
    VolumenSerieStrategy,
)

__all__ = [
    "PRStrategy",
    "PesoMaximoStrategy",
    "VolumenSerieStrategy",
]
