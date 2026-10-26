"""Patrón Strategy para la evaluación de Récords Personales (PR)."""

from abc import ABC, abstractmethod


class PRStrategy(ABC):
    """Interfaz para estrategias de evaluación de récords personales."""

    tipo_pr: str = ""

    @abstractmethod
    def es_nuevo_pr(
        self,
        nuevo_peso: float,
        repeticiones: int,
        valor_historico: float,
    ) -> bool:
        """Evalúa si la serie actual supera la marca histórica previa."""


class PesoMaximoStrategy(PRStrategy):
    """Estrategia principal (RF-10): evalúa si el peso levantado supera el máximo histórico."""

    tipo_pr = "PESO_MAXIMO"

    def es_nuevo_pr(
        self,
        nuevo_peso: float,
        repeticiones: int,
        valor_historico: float,
    ) -> bool:
        if nuevo_peso <= 0 or repeticiones <= 0:
            return False
        return float(nuevo_peso) > float(valor_historico)


class VolumenSerieStrategy(PRStrategy):
    """Estrategia secundaria: evalúa si el volumen (peso * reps) supera el máximo histórico."""

    tipo_pr = "VOLUMEN_SERIE"

    def es_nuevo_pr(
        self,
        nuevo_peso: float,
        repeticiones: int,
        valor_historico: float,
    ) -> bool:
        if nuevo_peso <= 0 or repeticiones <= 0:
            return False
        volumen_actual = float(nuevo_peso) * int(repeticiones)
        return volumen_actual > float(valor_historico)

