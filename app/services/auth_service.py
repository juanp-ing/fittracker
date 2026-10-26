"""Servicio de dominio para registro y autenticación de usuarios."""

import re
from typing import Optional

from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EmailDuplicadoError(ValueError):
    """Excepción lanzada cuando se intenta registrar un correo ya existente."""


class AuthService:
    """Lógica de negocio de autenticación desacoplada de HTTP/Flask."""

    def __init__(self, usuario_repo: Optional[UsuarioRepository] = None) -> None:
        self.usuario_repo = usuario_repo or UsuarioRepository()

    def registrar_usuario(self, nombre: str, email: str, password: str) -> Usuario:
        """Valida las reglas de negocio y registra un nuevo usuario."""
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("El nombre del usuario es obligatorio.")

        if not isinstance(email, str) or not EMAIL_REGEX.match(email.strip()):
            raise ValueError("El formato del correo electrónico no es válido.")

        if not isinstance(password, str) or len(password) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres.")

        existente = self.usuario_repo.obtener_por_email(email)
        if existente is not None:
            raise EmailDuplicadoError("El correo electrónico ya está registrado.")

        return self.usuario_repo.crear(
            nombre=nombre.strip(),
            email=email.strip().lower(),
            password=password,
        )

    def autenticar_usuario(self, email: str, password: str) -> Optional[Usuario]:
        """Verifica las credenciales de acceso y retorna el Usuario si son válidas."""
        if not isinstance(email, str) or not email.strip():
            return None
        if not isinstance(password, str) or not password:
            return None

        usuario = self.usuario_repo.obtener_por_email(email)
        if usuario is not None and usuario.check_password(password):
            return usuario
        return None

