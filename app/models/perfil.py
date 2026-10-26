"""Modelo de Perfil Biométrico y de Onboarding del Usuario."""

from app import db


class PerfilUsuario(db.Model):
    """Almacena sexo biológico, métricas corporales, meta y somatotipo del usuario (1 a 1)."""

    __tablename__ = "perfiles_usuarios"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    sexo = db.Column(db.String(15), default="HOMBRE", nullable=False)
    peso_kg = db.Column(db.Float, default=70.0, nullable=False)
    porcentaje_grasa = db.Column(db.Float, nullable=True)
    meta = db.Column(db.String(30), default="GANAR_MASA", nullable=False)
    somatotipo = db.Column(db.String(20), default="ECTOMORFO", nullable=False)
    onboarding_completado = db.Column(db.Boolean, default=False, nullable=False)

    usuario = db.relationship("Usuario", back_populates="perfil", uselist=False)

    def __repr__(self) -> str:
        return (
            f"<PerfilUsuario usuario_id={self.usuario_id} "
            f"sexo={self.sexo!r} meta={self.meta!r} somatotipo={self.somatotipo!r}>"
        )
