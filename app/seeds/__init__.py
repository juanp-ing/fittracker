"""Exportación de funciones de sembrado inicial de datos."""

from app.seeds.initial_data import (
    EJERCICIOS_PREDETERMINADOS_BASE,
    GRUPOS_MUSCULARES_BASE,
    seed_database,
)

__all__ = [
    "GRUPOS_MUSCULARES_BASE",
    "EJERCICIOS_PREDETERMINADOS_BASE",
    "seed_database",
]
