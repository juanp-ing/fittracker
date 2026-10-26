"""Exportación centralizada de los repositorios de FitTracker."""

from app.repositories.ejercicio_repository import EjercicioRepository
from app.repositories.pr_repository import PRRepository
from app.repositories.rutina_repository import RutinaRepository
from app.repositories.sesion_repository import SesionRepository
from app.repositories.usuario_repository import UsuarioRepository

__all__ = [
    "UsuarioRepository",
    "EjercicioRepository",
    "RutinaRepository",
    "SesionRepository",
    "PRRepository",
]

