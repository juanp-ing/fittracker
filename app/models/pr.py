"""Modelo de Récord Personal (PR)."""

from datetime import datetime, timezone
from app import db


class PR(db.Model):
    """Récord personal alcanzado por un usuario en un ejercicio."""

    __tablename__ = "prs"
    __table_args__ = (
        db.Index(
            "ix_pr_usuario_ejercicio_fecha",
            "usuario_id",
            "ejercicio_id",
            "fecha",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    ejercicio_id = db.Column(
        db.Integer,
        db.ForeignKey("ejercicios.id", ondelete="CASCADE"),
        nullable=False,
    )
    peso = db.Column(db.Float, nullable=False)
    serie_id = db.Column(
        db.Integer,
        db.ForeignKey("series.id", ondelete="CASCADE"),
        nullable=False,
    )
    tipo_pr = db.Column(db.String(30), default="PESO_MAXIMO", nullable=False)
    fecha = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    usuario = db.relationship("Usuario", back_populates="prs")
    ejercicio = db.relationship("Ejercicio", back_populates="prs")
    serie = db.relationship("Serie", back_populates="prs")

    def __repr__(self) -> str:
        return (
            f"<PR id={self.id} usuario_id={self.usuario_id} "
            f"ejercicio_id={self.ejercicio_id} peso={self.peso}>"
        )

