"""Repositorio para operaciones de persistencia del modelo Usuario."""

from typing import Optional
from sqlalchemy import func

from app import db
from app.models.usuario import Usuario


class UsuarioRepository:
    """Gestiona las consultas y persistencia de usuarios en la base de datos."""

    def crear(self, nombre: str, email: str, password: str) -> Usuario:
        """Crea y persiste un nuevo usuario con contraseña hasheada."""
        usuario = Usuario(
            nombre=nombre.strip(),
            email=email.strip().lower(),
        )
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()
        return usuario

    def obtener_por_id(self, usuario_id: int) -> Optional[Usuario]:
        """Obtiene un usuario por su clave primaria."""
        return db.session.get(Usuario, usuario_id)

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        """Obtiene un usuario por su correo electrónico (insensible a mayúsculas)."""
        email_normalizado = email.strip().lower()
        return (
            db.session.query(Usuario)
            .filter(func.lower(Usuario.email) == email_normalizado)
            .first()
        )
