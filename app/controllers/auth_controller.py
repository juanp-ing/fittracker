"""Controlador REST para autenticación y gestión de sesión de usuarios."""

from flask import Blueprint, jsonify, request
from flask_login import login_required, login_user, logout_user

from app.services.auth_service import AuthService, EmailDuplicadoError

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/register", methods=["POST"])
@auth_bp.route("/api/auth/registro", methods=["POST"])
def register():
    """Registra un nuevo usuario e inicia su sesión."""
    payload = request.get_json(silent=True) or {}
    nombre = payload.get("nombre", "")
    email = payload.get("email", "")
    password = payload.get("password", "")

    service = AuthService()
    try:
        usuario = service.registrar_usuario(
            nombre=nombre,
            email=email,
            password=password,
        )
    except EmailDuplicadoError as exc:
        return (
            jsonify(
                {
                    "error": str(exc),
                    "code": "EMAIL_DUPLICADO",
                }
            ),
            409,
        )
    except ValueError as exc:
        return (
            jsonify(
                {
                    "error": str(exc),
                    "code": "DATOS_INVALIDOS",
                }
            ),
            400,
        )

    login_user(usuario)
    return (
        jsonify(
            {
                "id": usuario.id,
                "nombre": usuario.nombre,
                "email": usuario.email,
                "mensaje": "Usuario registrado exitosamente",
            }
        ),
        201,
    )


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    """Autentica las credenciales del usuario e inicia su sesión."""
    payload = request.get_json(silent=True) or {}
    email = payload.get("email", "")
    password = payload.get("password", "")

    service = AuthService()
    usuario = service.autenticar_usuario(email=email, password=password)
    if usuario is None:
        return (
            jsonify(
                {
                    "error": "Credenciales inválidas.",
                    "code": "CREDENCIALES_INVALIDAS",
                }
            ),
            401,
        )

    login_user(usuario)
    return (
        jsonify(
            {
                "id": usuario.id,
                "nombre": usuario.nombre,
                "email": usuario.email,
                "mensaje": "Sesión iniciada correctamente",
            }
        ),
        200,
    )


@auth_bp.route("/api/auth/logout", methods=["POST"])
@login_required
def logout():
    """Cierra la sesión del usuario autenticado."""
    logout_user()
    return (
        jsonify(
            {
                "mensaje": "Sesión cerrada correctamente",
            }
        ),
        200,
    )

