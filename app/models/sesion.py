"""Modelos de Sesion y Serie de entrenamiento."""

from datetime import datetime, timezone
from app import db


class Sesion(db.Model):
    """Sesión de entrenamiento ejecutada por un usuario."""

    __tablename__ = "sesiones"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rutina_id = db.Column(
        db.Integer,
        db.ForeignKey("rutinas.id", ondelete="SET NULL"),
        nullable=True,
    )
    fecha_inicio = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    fecha_fin = db.Column(db.DateTime, nullable=True)
    estado = db.Column(db.String(20), default="ACTIVA", nullable=False)

    usuario = db.relationship("Usuario", back_populates="sesiones")
    rutina = db.relationship("Rutina", back_populates="sesiones")
    series = db.relationship(
        "Serie",
        back_populates="sesion",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Serie.fecha_hora",
    )

    def __repr__(self) -> str:
        return f"<Sesion id={self.id} usuario_id={self.usuario_id} estado={self.estado!r}>"


class Serie(db.Model):
    """Serie individual registrada dentro de una sesión de entrenamiento."""

    __tablename__ = "series"

    id = db.Column(db.Integer, primary_key=True)
    sesion_id = db.Column(
        db.Integer,
        db.ForeignKey("sesiones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ejercicio_id = db.Column(
        db.Integer,
        db.ForeignKey("ejercicios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    peso = db.Column(db.Float, nullable=False)
    repeticiones = db.Column(db.Integer, nullable=False)
    fecha_hora = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    sesion = db.relationship("Sesion", back_populates="series")
    ejercicio = db.relationship("Ejercicio", back_populates="series")
    prs = db.relationship(
        "PR",
        back_populates="serie",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def volumen(self) -> float:
        """Retorna el volumen desplazado en la serie (peso * repeticiones)."""
        return self.peso * self.repeticiones

    def __repr__(self) -> str:
        return (
            f"<Serie id={self.id} ejercicio_id={self.ejercicio_id} "
            f"peso={self.peso} repeticiones={self.repeticiones}>"
        )

