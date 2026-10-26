"""Repositorio para operaciones de persistencia de Usuario y PerfilUsuario."""

from datetime import datetime
from typing import Optional
from sqlalchemy import func

from app import db
from app.models.perfil import PerfilUsuario
from app.models.usuario import Usuario


class UsuarioRepository:
    """Gestiona las consultas y persistencia de usuarios, códigos OTP y perfiles biométricos."""

    def crear(
        self,
        nombre: str,
        email: str,
        password: str,
        email_verificado: bool = False,
        codigo_verificacion: Optional[str] = None,
        codigo_expiracion: Optional[datetime] = None,
    ) -> Usuario:
        """Crea y persiste un nuevo usuario con contraseña hasheada y su perfil inicial."""
        usuario = Usuario(
            nombre=nombre.strip(),
            email=email.strip().lower(),
            email_verificado=email_verificado,
            codigo_verificacion=codigo_verificacion,
            codigo_expiracion=codigo_expiracion,
        )
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.flush()

        perfil = PerfilUsuario(usuario_id=usuario.id)
        db.session.add(perfil)
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

    def actualizar_codigo_verificacion(
        self,
        usuario_id: int,
        codigo: str,
        expiracion: datetime,
    ) -> Optional[Usuario]:
        """Guarda o regenera el código OTP de 6 dígitos y su fecha de expiración."""
        usuario = self.obtener_por_id(usuario_id)
        if usuario is None:
            return None
        usuario.codigo_verificacion = codigo
        usuario.codigo_expiracion = expiracion
        db.session.commit()
        return usuario

    def marcar_email_verificado(self, usuario_id: int) -> Optional[Usuario]:
        """Marca el correo del usuario como verificado y limpia el código OTP temporal."""
        usuario = self.obtener_por_id(usuario_id)
        if usuario is None:
            return None
        usuario.email_verificado = True
        usuario.codigo_verificacion = None
        usuario.codigo_expiracion = None
        db.session.commit()
        return usuario

    def obtener_perfil(self, usuario_id: int) -> PerfilUsuario:
        """Obtiene el PerfilUsuario asociado al usuario o lo inicializa si no existía."""
        perfil = (
            db.session.query(PerfilUsuario)
            .filter(PerfilUsuario.usuario_id == usuario_id)
            .first()
        )
        if perfil is None:
            perfil = PerfilUsuario(usuario_id=usuario_id)
            db.session.add(perfil)
            db.session.commit()
        return perfil

    def guardar_perfil_usuario(
        self,
        usuario_id: int,
        sexo: str,
        peso_kg: float,
        porcentaje_grasa: Optional[float],
        meta: str,
        somatotipo: str,
        onboarding_completado: bool = True,
    ) -> PerfilUsuario:
        """Crea o actualiza los datos biométricos y de meta/somatotipo del usuario."""
        perfil = (
            db.session.query(PerfilUsuario)
            .filter(PerfilUsuario.usuario_id == usuario_id)
            .first()
        )
        if perfil is None:
            perfil = PerfilUsuario(usuario_id=usuario_id)
            db.session.add(perfil)

        perfil.sexo = sexo
        perfil.peso_kg = float(peso_kg)
        perfil.porcentaje_grasa = (
            float(porcentaje_grasa) if porcentaje_grasa is not None else None
        )
        perfil.meta = meta
        perfil.somatotipo = somatotipo
        perfil.onboarding_completado = onboarding_completado
        db.session.commit()
        return perfil
