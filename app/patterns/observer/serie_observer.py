"""Patrón Observer para eventos post-registro de una Serie de entrenamiento."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class SerieObserver(ABC):
    """Interfaz para observadores que reaccionan al guardado de una Serie."""

    @abstractmethod
    def actualizar(
        self,
        usuario_id: int,
        serie: Any,
        max_peso_previo: Optional[float] = None,
        max_volumen_previo: Optional[float] = None,
    ) -> dict:
        """Ejecuta la lógica asociada al evento de nueva serie registrada."""


class SerieSubject:
    """Sujeto observable que notifica a los observadores tras registrar una serie."""

    def __init__(self) -> None:
        self._observers: list[SerieObserver] = []

    def suscribir(self, observer: SerieObserver) -> None:
        """Agrega un observador a la lista de suscriptores."""
        if observer not in self._observers:
            self._observers.append(observer)

    def desuscribir(self, observer: SerieObserver) -> None:
        """Elimina un observador de la lista de suscriptores."""
        if observer in self._observers:
            self._observers.remove(observer)

    def notificar(
        self,
        usuario_id: int,
        serie: Any,
        max_peso_previo: Optional[float] = None,
        max_volumen_previo: Optional[float] = None,
    ) -> dict:
        """Notifica a todos los observadores suscritos y consolida sus resultados."""
        resultado_consolidado: dict = {}
        for observer in self._observers:
            res = observer.actualizar(
                usuario_id=usuario_id,
                serie=serie,
                max_peso_previo=max_peso_previo,
                max_volumen_previo=max_volumen_previo,
            )
            if isinstance(res, dict):
                resultado_consolidado.update(res)
        return resultado_consolidado


class PRDetectionObserver(SerieObserver):
    """Observador concreto que evalúa y registra automáticamente Récords Personales (PR)."""

    def __init__(self, pr_service: Any) -> None:
        self.pr_service = pr_service

    def actualizar(
        self,
        usuario_id: int,
        serie: Any,
        max_peso_previo: Optional[float] = None,
        max_volumen_previo: Optional[float] = None,
    ) -> dict:
        """Delega en PRService la evaluación y registro del PR dentro de la misma transacción."""
        return self.pr_service.evaluar_y_registrar_pr(
            usuario_id=usuario_id,
            serie=serie,
            max_peso_previo=max_peso_previo,
            max_volumen_previo=max_volumen_previo,
            commit=False,
        )
