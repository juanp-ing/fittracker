"""Controlador REST para el catálogo, búsqueda y creación de ejercicios."""

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.services.ejercicio_service import EjercicioService

ejercicio_bp = Blueprint("ejercicio", __name__)


@ejercicio_bp.route("/api/grupos-musculares", methods=["GET"])
@login_required
def listar_grupos_musculares():
    """Devuelve el catálogo de grupos musculares para el formulario de creación rápida."""
    service = EjercicioService()
    grupos = service.listar_grupos_musculares()
    return jsonify({"grupos_musculares": grupos}), 200


@ejercicio_bp.route("/api/ejercicios", methods=["GET"])
@login_required
def listar_ejercicios():
    """Lista y filtra los ejercicios visibles para el usuario autenticado."""
    query_texto = request.args.get("q")
    service = EjercicioService()
    ejercicios = service.buscar_ejercicios_usuario(
        usuario_id=current_user.id,
        query_texto=query_texto,
    )
    return jsonify({"ejercicios": ejercicios}), 200


@ejercicio_bp.route("/api/ejercicios", methods=["POST"])
@login_required
def crear_ejercicio():
    """Crea un nuevo ejercicio personalizado al vuelo para el usuario autenticado."""
    payload = request.get_json(silent=True) or {}
    nombre = payload.get("nombre", "")
    grupos_primarios_ids = payload.get("grupos_primarios_ids", [])
    grupos_secundarios_ids = payload.get("grupos_secundarios_ids")

    service = EjercicioService()
    try:
        creado = service.crear_ejercicio_personalizado(
            usuario_id=current_user.id,
            nombre=nombre,
            grupos_primarios_ids=grupos_primarios_ids,
            grupos_secundarios_ids=grupos_secundarios_ids,
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

    return jsonify(creado), 201
