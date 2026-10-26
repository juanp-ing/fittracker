"""Controlador REST para Sesiones de entrenamiento y registro rápido de Series."""

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.patterns.state import SesionCerradaError
from app.services.sesion_service import SesionNoEncontradaError, SesionService

sesion_bp = Blueprint("sesion", __name__)


@sesion_bp.route("/api/sesiones", methods=["POST"])
@login_required
def iniciar_sesion():
    """Inicia una nueva sesión de entrenamiento libre o asociada a una rutina."""
    payload = request.get_json(silent=True) or {}
    rutina_id = payload.get("rutina_id")

    service = SesionService()
    try:
        sesion = service.iniciar_sesion(
            usuario_id=current_user.id,
            rutina_id=rutina_id,
        )
    except LookupError as exc:
        return jsonify({"error": str(exc), "code": "NO_ENCONTRADO"}), 404
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "DATOS_INVALIDOS"}), 400

    return jsonify(sesion), 201


@sesion_bp.route("/api/sesiones/<int:sesion_id>/series", methods=["POST"])
@login_required
def registrar_serie(sesion_id: int):
    """Registra una serie en la sesión activa, evalúa PRs y devuelve el descanso sugerido."""
    payload = request.get_json(silent=True) or {}
    ejercicio_id = payload.get("ejercicio_id")
    peso = payload.get("peso")
    repeticiones = payload.get("repeticiones")

    if not isinstance(ejercicio_id, int) or isinstance(ejercicio_id, bool):
        return (
            jsonify(
                {
                    "error": "ejercicio_id es obligatorio y debe ser un entero.",
                    "code": "DATOS_INVALIDOS",
                }
            ),
            400,
        )

    service = SesionService()
    try:
        resultado = service.registrar_serie(
            usuario_id=current_user.id,
            sesion_id=sesion_id,
            ejercicio_id=ejercicio_id,
            peso=peso,
            repeticiones=repeticiones,
        )
    except SesionNoEncontradaError as exc:
        return jsonify({"error": str(exc), "code": "NO_ENCONTRADO"}), 404
    except (SesionCerradaError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "DATOS_INVALIDOS"}), 400

    return jsonify(resultado), 201


@sesion_bp.route("/api/sesiones/<int:sesion_id>/finalizar", methods=["PATCH", "POST"])
@login_required
def finalizar_sesion(sesion_id: int):
    """Finaliza una sesión activa registrando su hora de cierre."""
    service = SesionService()
    try:
        resultado = service.finalizar_sesion(
            usuario_id=current_user.id,
            sesion_id=sesion_id,
        )
    except SesionNoEncontradaError as exc:
        return jsonify({"error": str(exc), "code": "NO_ENCONTRADO"}), 404
    except (SesionCerradaError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "SESION_CERRADA"}), 400

    return jsonify(resultado), 200
