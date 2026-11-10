"""Repositorio para operaciones de persistencia de Sesion y Serie."""

from datetime import datetime, timezone
from typing import Optional

from app import db
from app.models.sesion import Serie, Sesion


class SesionRepository:
    """Gestiona las sesiones de entrenamiento y el registro de series."""

    def iniciar_sesion(
        self,
        usuario_id: int,
        rutina_id: Optional[int] = None,
    ) -> Sesion:
        """Crea e inicia una nueva sesión de entrenamiento activa."""
        sesion = Sesion(
            usuario_id=usuario_id,
            rutina_id=rutina_id,
            estado="ACTIVA",
        )
        db.session.add(sesion)
        db.session.commit()
        return sesion

    def obtener_por_id_y_usuario(
        self,
        sesion_id: int,
        usuario_id: int,
    ) -> Optional[Sesion]:
        """Obtiene una sesión verificando que pertenezca al usuario indicado."""
        return (
            db.session.query(Sesion)
            .filter(
                Sesion.id == sesion_id,
                Sesion.usuario_id == usuario_id,
            )
            .first()
        )

    def obtener_activa_desde(self, usuario_id: int, desde: datetime) -> Optional[Sesion]:
        """Sesión ACTIVA más reciente del usuario iniciada a partir de ``desde`` (UTC naive)."""
        return (
            db.session.query(Sesion)
            .filter(
                Sesion.usuario_id == usuario_id,
                Sesion.estado == "ACTIVA",
                Sesion.fecha_inicio >= desde,
            )
            .order_by(Sesion.fecha_inicio.desc(), Sesion.id.desc())
            .first()
        )

    def obtener_serie_de_sesion(self, serie_id: int, sesion_id: int) -> Optional[Serie]:
        """Obtiene una serie solo si pertenece a la sesión indicada."""
        return (
            db.session.query(Serie)
            .filter(Serie.id == serie_id, Serie.sesion_id == sesion_id)
            .first()
        )

    def eliminar_serie(self, serie: Serie) -> None:
        """Elimina una serie; sus PRs se borran en cascada."""
        db.session.delete(serie)
        db.session.commit()

    def agregar_serie(
        self,
        sesion_id: int,
        ejercicio_id: int,
        peso: float,
        repeticiones: int,
        commit: bool = True,
    ) -> Serie:
        """Registra una nueva serie dentro de una sesión de entrenamiento."""
        serie = Serie(
            sesion_id=sesion_id,
            ejercicio_id=ejercicio_id,
            peso=peso,
            repeticiones=repeticiones,
        )
        db.session.add(serie)
        db.session.flush()
        if commit:
            db.session.commit()
        return serie

    def confirmar_transaccion(self) -> None:
        """Confirma de forma atómica los cambios pendientes en la sesión de base de datos."""
        db.session.commit()

    def obtener_ultima_serie_ejercicio(
        self,
        usuario_id: int,
        ejercicio_id: int,
    ) -> Optional[Serie]:
        """Obtiene la última serie registrada por el usuario para un ejercicio dado."""
        return (
            db.session.query(Serie)
            .join(Sesion, Serie.sesion_id == Sesion.id)
            .filter(
                Sesion.usuario_id == usuario_id,
                Serie.ejercicio_id == ejercicio_id,
            )
            .order_by(Serie.fecha_hora.desc(), Serie.id.desc())
            .first()
        )

    def finalizar_sesion(self, sesion: Sesion) -> Sesion:
        """Marca una sesión como FINALIZADA registrando su fecha y hora de cierre."""
        sesion.estado = "FINALIZADA"
        sesion.fecha_fin = datetime.now(timezone.utc)
        db.session.commit()
        return sesion

    def listar_activas_anteriores_a(self, usuario_id: int, limite: datetime) -> list[Sesion]:
        """Sesiones ACTIVA del usuario iniciadas antes de ``limite`` (UTC naive)."""
        return (
            db.session.query(Sesion)
            .filter(
                Sesion.usuario_id == usuario_id,
                Sesion.estado == "ACTIVA",
                Sesion.fecha_inicio < limite,
            )
            .all()
        )

    def cerrar_abandonadas(self, sesiones: list[Sesion]) -> None:
        """Cierra sesiones olvidadas: finaliza las que tienen series y elimina las vacías.

        La fecha de cierre es la de la última serie registrada, no el momento del cierre.
        """
        for sesion in sesiones:
            fechas = [s.fecha_hora for s in sesion.series if s.fecha_hora]
            if not fechas:
                db.session.delete(sesion)
                continue
            sesion.estado = "FINALIZADA"
            sesion.fecha_fin = max(fechas)
        db.session.commit()

    def listar_historial_usuario(
        self,
        usuario_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Sesion]:
        """Lista el historial de sesiones de un usuario ordenado de más reciente a más antigua."""
        return (
            db.session.query(Sesion)
            .filter(Sesion.usuario_id == usuario_id)
            .order_by(Sesion.fecha_inicio.desc(), Sesion.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def existe_serie_anterior(self, usuario_id: int, ejercicio_id: int, serie: Serie) -> bool:
        """¿El usuario ya había registrado ese ejercicio antes de la serie indicada?"""
        return (
            db.session.query(Serie.id)
            .join(Sesion, Serie.sesion_id == Sesion.id)
            .filter(
                Sesion.usuario_id == usuario_id,
                Serie.ejercicio_id == ejercicio_id,
                Serie.id != serie.id,
                db.or_(
                    Serie.fecha_hora < serie.fecha_hora,
                    db.and_(Serie.fecha_hora == serie.fecha_hora, Serie.id < serie.id),
                ),
            )
            .first()
            is not None
        )

    def contar_series_por_ejercicio(self, usuario_id: int) -> dict[int, int]:
        """Devuelve {ejercicio_id: total de series registradas} para un usuario."""
        filas = (
            db.session.query(Serie.ejercicio_id, db.func.count(Serie.id))
            .join(Sesion, Serie.sesion_id == Sesion.id)
            .filter(Sesion.usuario_id == usuario_id)
            .group_by(Serie.ejercicio_id)
            .all()
        )
        return {ejercicio_id: total for ejercicio_id, total in filas}

    def listar_series_por_rango_fechas(
        self,
        usuario_id: int,
        fecha_desde: datetime,
        fecha_hasta: Optional[datetime] = None,
    ) -> list[Serie]:
        """Lista todas las series de un usuario dentro de una ventana temporal."""
        query = (
            db.session.query(Serie)
            .join(Sesion, Serie.sesion_id == Sesion.id)
            .filter(
                Sesion.usuario_id == usuario_id,
                Serie.fecha_hora >= fecha_desde,
            )
        )
        if fecha_hasta is not None:
            query = query.filter(Serie.fecha_hora <= fecha_hasta)

        return query.order_by(Serie.fecha_hora.asc(), Serie.id.asc()).all()

    def listar_series_ejercicio_historico(
        self,
        usuario_id: int,
        ejercicio_id: int,
    ) -> list[Serie]:
        """Lista el historial cronológico de series de un usuario para un ejercicio."""
        return (
            db.session.query(Serie)
            .join(Sesion, Serie.sesion_id == Sesion.id)
            .filter(
                Sesion.usuario_id == usuario_id,
                Serie.ejercicio_id == ejercicio_id,
            )
            .order_by(Serie.fecha_hora.asc(), Serie.id.asc())
            .all()
        )

