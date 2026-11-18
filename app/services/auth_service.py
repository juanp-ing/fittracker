"""Servicio de dominio para registro, autenticación y onboarding biométrico."""

import re
from typing import Optional

from app.models.perfil import PerfilUsuario
from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

SEXOS_VALIDOS = {"HOMBRE", "MUJER"}
METAS_VALIDAS = {"BAJAR_PESO", "DEFINIR", "GANAR_MASA"}
SOMATOTIPOS_VALIDOS = {"ECTOMORFO", "MESOMORFO", "ENDOMORFO"}


class EmailDuplicadoError(ValueError):
    """Excepción lanzada cuando se intenta registrar un correo ya existente."""


class AuthService:
    """Lógica de negocio de autenticación, y perfil biométrico desacoplada de HTTP."""

    def __init__(self, usuario_repo: Optional[UsuarioRepository] = None) -> None:
        self.usuario_repo = usuario_repo or UsuarioRepository()

    @staticmethod
    def serializar_perfil(perfil: PerfilUsuario, usuario: Optional[Usuario] = None) -> dict:
        """Convierte una entidad PerfilUsuario en un diccionario serializable a JSON."""
        return {
            "id": perfil.id,
            "usuario_id": perfil.usuario_id,
            "sexo": perfil.sexo,
            "peso_kg": float(perfil.peso_kg),
            "porcentaje_grasa": (
                float(perfil.porcentaje_grasa)
                if perfil.porcentaje_grasa is not None
                else None
            ),
            "meta": perfil.meta,
            "somatotipo": perfil.somatotipo,
            "onboarding_completado": bool(perfil.onboarding_completado),
        }

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

    def obtener_perfil_usuario(self, usuario_id: int) -> dict:
        """Obtiene los datos biométricos y de meta/somatotipo del usuario."""
        usuario = self.usuario_repo.obtener_por_id(usuario_id)
        if usuario is None:
            raise LookupError("Usuario no encontrado.")
        perfil = self.usuario_repo.obtener_perfil(usuario_id)
        return self.serializar_perfil(perfil, usuario)

    def guardar_onboarding_perfil(
        self,
        usuario_id: int,
        sexo: str,
        peso_kg: float,
        porcentaje_grasa: Optional[float],
        meta: str,
        somatotipo: str,
    ) -> dict:
        """Valida los enums y rangos biométricos y persiste el PerfilUsuario con onboarding_completado=True."""
        usuario = self.usuario_repo.obtener_por_id(usuario_id)
        if usuario is None:
            raise LookupError("Usuario no encontrado.")

        sexo_norm = str(sexo or "").strip().upper()
        if sexo_norm not in SEXOS_VALIDOS:
            raise ValueError(
                f"El sexo debe ser uno de: {', '.join(sorted(SEXOS_VALIDOS))}."
            )

        meta_norm = str(meta or "").strip().upper()
        if meta_norm not in METAS_VALIDAS:
            raise ValueError(
                f"La meta debe ser una de: {', '.join(sorted(METAS_VALIDAS))}."
            )

        somatotipo_norm = str(somatotipo or "").strip().upper()
        if somatotipo_norm not in SOMATOTIPOS_VALIDOS:
            raise ValueError(
                f"El somatotipo debe ser uno de: {', '.join(sorted(SOMATOTIPOS_VALIDOS))}."
            )

        if isinstance(peso_kg, bool) or peso_kg is None:
            raise ValueError("El peso corporal es obligatorio.")
        try:
            peso_val = float(peso_kg)
        except (TypeError, ValueError) as exc:
            raise ValueError("El peso corporal debe ser un número válido.") from exc

        if peso_val <= 20.0 or peso_val > 350.0:
            raise ValueError("El peso corporal debe ser mayor a 20 kg y menor o igual a 350 kg.")

        grasa_val: Optional[float] = None
        if porcentaje_grasa is not None and porcentaje_grasa != "":
            if isinstance(porcentaje_grasa, bool):
                raise ValueError("El porcentaje de grasa no es válido.")
            try:
                grasa_val = float(porcentaje_grasa)
            except (TypeError, ValueError) as exc:
                raise ValueError("El porcentaje de grasa debe ser un número válido.") from exc
            if grasa_val < 3.0 or grasa_val > 60.0:
                raise ValueError("El porcentaje de grasa corporal debe estar entre 3% y 60%.")

        perfil = self.usuario_repo.guardar_perfil_usuario(
            usuario_id=usuario_id,
            sexo=sexo_norm,
            peso_kg=round(peso_val, 1),
            porcentaje_grasa=round(grasa_val, 1) if grasa_val is not None else None,
            meta=meta_norm,
            somatotipo=somatotipo_norm,
            onboarding_completado=True,
        )
        return self.serializar_perfil(perfil, usuario)
