"""Exportación del patrón Strategy de FitTracker."""

from app.patterns.strategy.pr_strategy import (
    PRStrategy,
    PesoMaximoStrategy,
    VolumenSerieStrategy,
)
from app.patterns.strategy.resumen_strategy import (
    ComparacionMensualStrategy,
    ResumenClasificacionStrategy,
    ResumenMensualStrategy,
    ResumenStrategy,
)
from app.patterns.strategy.rutina_recomendacion_strategy import (
    RutinaRecomendacionStrategy,
)

__all__ = [
    "PRStrategy",
    "PesoMaximoStrategy",
    "VolumenSerieStrategy",
    "ResumenClasificacionStrategy",
    "ComparacionMensualStrategy",
    "ResumenStrategy",
    "ResumenMensualStrategy",
    "RutinaRecomendacionStrategy",
]
