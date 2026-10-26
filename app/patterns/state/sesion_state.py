"""Patrón State para gestionar el ciclo de vida de una Sesión de entrenamiento."""

from abc import ABC, abstractmethod


class SesionCerradaError(ValueError):
    """Excepción de dominio lanzada al intentar mutar una sesión ya finalizada."""


class SesionState(ABC):
    """Interfaz base del patrón State para el estado de una Sesión."""

    nombre_estado: str = ""

    @abstractmethod
    def validar_registro_serie(self) -> None:
        """Verifica si el estado actual permite agregar una nueva serie."""

    @abstractmethod
    def validar_finalizacion(self) -> None:
        """Verifica si el estado actual permite finalizar la sesión."""

    @classmethod
    def obtener_estado(cls, estado_str: str) -> "SesionState":
        """Retorna la instancia de estado correspondiente al valor almacenado."""
        if (estado_str or "").upper() == "ACTIVA":
            return SesionActivaState()
        return SesionFinalizadaState()


class SesionActivaState(SesionState):
    """Estado de una sesión en curso que admite nuevas series y su cierre."""

    nombre_estado = "ACTIVA"

    def validar_registro_serie(self) -> None:
        return None

    def validar_finalizacion(self) -> None:
        return None


class SesionFinalizadaState(SesionState):
    """Estado inmutable de una sesión cerrada que bloquea nuevas mutaciones."""

    nombre_estado = "FINALIZADA"

    def validar_registro_serie(self) -> None:
        raise SesionCerradaError(
            "No se pueden agregar series a una sesión que ya está FINALIZADA."
        )

    def validar_finalizacion(self) -> None:
        raise SesionCerradaError("La sesión ya se encuentra en estado FINALIZADA.")

