"""Modelo de Usuario con soporte de autenticación para FitTracker."""

from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class Usuario(UserMixin, db.Model):
    """Representa un usuario registrado en la aplicación."""

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    fecha_registro = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    ejercicios_creados = db.relationship(
        "Ejercicio",
        back_populates="creador",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    rutinas = db.relationship(
        "Rutina",
        back_populates="usuario",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    sesiones = db.relationship(
        "Sesion",
        back_populates="usuario",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    prs = db.relationship(
        "PR",
        back_populates="usuario",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def set_password(self, password: str) -> None:
        """Genera y almacena el hash seguro de la contraseña."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifica si la contraseña en texto plano coincide con el hash almacenado."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<Usuario id={self.id} email={self.email!r}>"

