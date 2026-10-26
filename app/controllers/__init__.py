"""Exportación de Blueprints de la capa de controladores."""

from app.controllers.auth_controller import auth_bp
from app.controllers.ejercicio_controller import ejercicio_bp

__all__ = ["auth_bp", "ejercicio_bp"]
