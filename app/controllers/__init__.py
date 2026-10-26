"""Exportación de Blueprints de la capa de controladores."""

from app.controllers.auth_controller import auth_bp
from app.controllers.ejercicio_controller import ejercicio_bp
from app.controllers.resumen_controller import resumen_bp
from app.controllers.rutina_controller import rutina_bp
from app.controllers.sesion_controller import sesion_bp

__all__ = [
    "auth_bp",
    "ejercicio_bp",
    "rutina_bp",
    "sesion_bp",
    "resumen_bp",
]
