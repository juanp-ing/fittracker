"""Utilidades de zona horaria para calcular el "día local" del usuario.

Las fechas se persisten en UTC (naive). La interfaz, en cambio, piensa en días locales:
un entrenamiento a las 21:00 en Bogotá pertenece a ese día aunque en UTC ya sea mañana.
"""

from datetime import date, datetime, time, timezone, tzinfo
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Cookie que fija el navegador (base.html) con su zona horaria IANA, p. ej. "America/Bogota".
COOKIE_ZONA_HORARIA = "ft_tz"


def resolver_zona_horaria(nombre: Optional[str]) -> tzinfo:
    """Devuelve la zona IANA indicada o UTC si viene vacía o no es válida."""
    if nombre and nombre.strip():
        try:
            return ZoneInfo(nombre.strip())
        except (ZoneInfoNotFoundError, ValueError):
            pass
    return timezone.utc


def limites_utc_de_dias_locales(
    desde: date, hasta: date, zona: tzinfo
) -> tuple[datetime, datetime]:
    """Convierte el rango de días locales [desde, hasta] a límites UTC naive para consultar."""
    inicio = datetime.combine(desde, time.min, tzinfo=zona).astimezone(timezone.utc)
    fin = datetime.combine(hasta, time.max, tzinfo=zona).astimezone(timezone.utc)
    return inicio.replace(tzinfo=None), fin.replace(tzinfo=None)


def fecha_local(momento: datetime, zona: tzinfo) -> date:
    """Día local de un instante persistido en UTC (naive o aware)."""
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento.astimezone(zona).date()
