"""Exportación centralizada de todos los modelos SQLAlchemy de FitTracker."""

from app.models.ejercicio import Ejercicio, EjercicioGrupo, GrupoMuscular
from app.models.perfil import PerfilUsuario
from app.models.pr import PR
from app.models.rutina import Rutina, RutinaEjercicio
from app.models.sesion import Serie, Sesion
from app.models.usuario import Usuario

__all__ = [
    "Usuario",
    "PerfilUsuario",
    "GrupoMuscular",
    "Ejercicio",
    "EjercicioGrupo",
    "Rutina",
    "RutinaEjercicio",
    "Sesion",
    "Serie",
    "PR",
]
