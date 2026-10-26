"""Repositorio para consultas y persistencia de Récords Personales (PR)."""

from datetime import datetime
from typing import Optional
from sqlalchemy import func

from app import db
from app.models.pr import PR
from app.models.sesion import Serie, Sesion


class PRRepository:
    """Gestiona el registro y consulta de récords personales e históricos."""

    def obtener_max_peso_historico(
        self,
        usuario_id: int,
        ejercicio_id: int,
        excluir_serie_id: Optional[int] = None,
    ) -> float:
        """Retorna el peso máximo histórico registrado para el usuario y ejercicio (0.0 si no existe)."""
        query_pr = db.session.query(func.max(PR.peso)).filter(
            PR.usuario_id == usuario_id,
            PR.ejercicio_id == ejercicio_id,
        )
        query_serie = (
            db.session.query(func.max(Serie.peso))
            .join(Sesion, Serie.sesion_id == Sesion.id)
            .filter(
                Sesion.usuario_id == usuario_id,
                Serie.ejercicio_id == ejercicio_id,
            )
        )
        if excluir_serie_id is not None:
            query_pr = query_pr.filter(PR.serie_id != excluir_serie_id)
            query_serie = query_serie.filter(Serie.id != excluir_serie_id)

        max_pr = query_pr.scalar()
        max_serie = query_serie.scalar()
        return float(max(max_pr or 0.0, max_serie or 0.0))

    def obtener_max_volumen_historico(
        self,
        usuario_id: int,
        ejercicio_id: int,
        excluir_serie_id: Optional[int] = None,
    ) -> float:
        """Retorna el volumen máximo histórico en una serie para el usuario y ejercicio (0.0 si no hay series)."""
        query = (
            db.session.query(func.max(Serie.peso * Serie.repeticiones))
            .join(Sesion, Serie.sesion_id == Sesion.id)
            .filter(
                Sesion.usuario_id == usuario_id,
                Serie.ejercicio_id == ejercicio_id,
            )
        )
        if excluir_serie_id is not None:
            query = query.filter(Serie.id != excluir_serie_id)

        max_vol = query.scalar()
        return float(max_vol) if max_vol is not None else 0.0

    def registrar_pr(
        self,
        usuario_id: int,
        ejercicio_id: int,
        serie_id: int,
        peso: float,
        tipo_pr: str = "PESO_MAXIMO",
        commit: bool = True,
    ) -> PR:
        """Registra un nuevo récord personal vinculado a una serie."""
        nuevo_pr = PR(
            usuario_id=usuario_id,
            ejercicio_id=ejercicio_id,
            serie_id=serie_id,
            peso=peso,
            tipo_pr=tipo_pr,
        )
        db.session.add(nuevo_pr)
        db.session.flush()
        if commit:
            db.session.commit()
        return nuevo_pr

    def listar_prs_usuario_rango(
        self,
        usuario_id: int,
        fecha_desde: datetime,
        fecha_hasta: Optional[datetime] = None,
    ) -> list[PR]:
        """Lista los récords personales alcanzados por un usuario en un rango de fechas."""
        query = db.session.query(PR).filter(
            PR.usuario_id == usuario_id,
            PR.fecha >= fecha_desde,
        )
        if fecha_hasta is not None:
            query = query.filter(PR.fecha <= fecha_hasta)

        return query.order_by(PR.fecha.desc(), PR.id.desc()).all()

    def obtener_mejor_pr_por_ejercicios(
        self,
        usuario_id: int,
        ejercicios_ids: list[int],
    ) -> Optional[PR]:
        """Retorna el mayor PR registrado por el usuario dentro de un conjunto de ejercicios."""
        if not ejercicios_ids:
            return None
        return (
            db.session.query(PR)
            .filter(
                PR.usuario_id == usuario_id,
                PR.ejercicio_id.in_(ejercicios_ids),
            )
            .order_by(PR.peso.desc(), PR.fecha.desc(), PR.id.desc())
            .first()
        )


