"""Servicio de dominio para la evaluación y registro de Récords Personales (PR)."""

from typing import Optional

from app.models.sesion import Serie
from app.patterns.strategy import (
    PRStrategy,
    PesoMaximoStrategy,
    VolumenSerieStrategy,
)
from app.repositories.pr_repository import PRRepository


class PRService:
    """Evalúa si una serie entrante constituye un nuevo récord personal y lo registra."""

    def __init__(
        self,
        pr_repo: Optional[PRRepository] = None,
        peso_strategy: Optional[PRStrategy] = None,
        volumen_strategy: Optional[PRStrategy] = None,
    ) -> None:
        self.pr_repo = pr_repo or PRRepository()
        self.peso_strategy = peso_strategy or PesoMaximoStrategy()
        self.volumen_strategy = volumen_strategy or VolumenSerieStrategy()

    def evaluar_y_registrar_pr(
        self,
        usuario_id: int,
        serie: Serie,
        max_peso_previo: Optional[float] = None,
        max_volumen_previo: Optional[float] = None,
        commit: bool = True,
    ) -> dict:
        """Compara la serie contra el historial previo y persiste el PR si aplica."""
        if max_peso_previo is None:
            max_peso_previo = self.pr_repo.obtener_max_peso_historico(
                usuario_id=usuario_id,
                ejercicio_id=serie.ejercicio_id,
                excluir_serie_id=serie.id,
            )

        if max_volumen_previo is None:
            max_volumen_previo = self.pr_repo.obtener_max_volumen_historico(
                usuario_id=usuario_id,
                ejercicio_id=serie.ejercicio_id,
                excluir_serie_id=serie.id,
            )

        es_pr_peso = self.peso_strategy.es_nuevo_pr(
            nuevo_peso=serie.peso,
            repeticiones=serie.repeticiones,
            valor_historico=max_peso_previo,
        )
        es_pr_volumen = self.volumen_strategy.es_nuevo_pr(
            nuevo_peso=serie.peso,
            repeticiones=serie.repeticiones,
            valor_historico=max_volumen_previo,
        )

        pr_registrado = None
        nuevo_pr_peso: Optional[float] = None

        if es_pr_peso:
            pr_registrado = self.pr_repo.registrar_pr(
                usuario_id=usuario_id,
                ejercicio_id=serie.ejercicio_id,
                serie_id=serie.id,
                peso=serie.peso,
                tipo_pr=self.peso_strategy.tipo_pr,
                commit=commit,
            )
            nuevo_pr_peso = float(serie.peso)

        return {
            "es_pr": es_pr_peso,
            "nuevo_pr": es_pr_peso,
            "es_pr_peso": es_pr_peso,
            "es_pr_volumen": es_pr_volumen,
            "peso_anterior": float(max_peso_previo),
            "nuevo_pr_peso": nuevo_pr_peso,
            "pr_id": pr_registrado.id if pr_registrado else None,
        }
