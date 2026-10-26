"""Controlador de vistas HTML y endpoints REST para la gestión de rutinas personalizadas y famosas."""

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from app.services.ejercicio_service import EjercicioService
from app.services.rutina_service import RutinaNoEncontradaError, RutinaService

rutina_bp = Blueprint("rutina", __name__)


@rutina_bp.route("/rutinas", methods=["GET"])
@login_required
def vista_rutinas():
    """Renderiza la vista de gestión de rutinas personalizadas y catálogo de 12 Rutinas Famosas."""
    rutina_service = RutinaService()
    ej_service = EjercicioService()
    rutinas = rutina_service.listar_rutinas_usuario(usuario_id=current_user.id)
    rutinas_famosas = rutina_service.listar_rutinas_famosas(usuario_id=current_user.id)
    ejercicios = ej_service.buscar_ejercicios_usuario(usuario_id=current_user.id)
    return render_template(
        "rutinas/index.html",
        active_tab="rutinas",
        rutinas=rutinas,
        rutinas_famosas=rutinas_famosas,
        ejercicios=ejercicios,
    )


@rutina_bp.route("/api/rutinas/famosas", methods=["GET"])
@login_required
def listar_rutinas_famosas():
    """Devuelve las 12 rutinas famosas ordenadas por afinidad con el perfil del usuario."""
    meta = request.args.get("meta")
    somatotipo = request.args.get("somatotipo")
    service = RutinaService()
    rutinas = service.listar_rutinas_famosas(
        usuario_id=current_user.id,
        meta=meta,
        somatotipo=somatotipo,
    )
    return jsonify({"rutinas_famosas": rutinas, "rutinas": rutinas}), 200


@rutina_bp.route("/api/rutinas/famosas/<int:plantilla_id>/clonar", methods=["POST"])
@login_required
def clonar_rutina_famosa(plantilla_id: int):
    """Clona la rutina famosa elegida dentro de las rutinas personales del usuario."""
    service = RutinaService()
    try:
        clonada = service.clonar_rutina_famosa(
            usuario_id=current_user.id,
            plantilla_id=plantilla_id,
        )
    except RutinaNoEncontradaError as exc:
        return jsonify({"error": str(exc), "code": "NO_ENCONTRADO"}), 404

    return jsonify(clonada), 201


@rutina_bp.route("/api/rutinas", methods=["GET"])
@login_required
def listar_rutinas():
    """Lista las rutinas del usuario autenticado (con filtro opcional de favoritas)."""
    favoritas_param = (request.args.get("favoritas") or "").lower()
    solo_favoritas = favoritas_param in ("true", "1", "yes")
    service = RutinaService()
    rutinas = service.listar_rutinas_usuario(
        usuario_id=current_user.id,
        solo_favoritas=solo_favoritas,
    )
    return jsonify({"rutinas": rutinas}), 200


@rutina_bp.route("/api/rutinas", methods=["POST"])
@login_required
def crear_rutina():
    """Crea una nueva rutina personalizada con sus ejercicios y tiempos de descanso."""
    payload = request.get_json(silent=True) or {}
    nombre = payload.get("nombre", "")
    es_favorita = bool(payload.get("es_favorita", False))
    ejercicios_items = payload.get("ejercicios", [])
    dias_semana = payload.get("dias_semana", "LUN,MIE,VIE")
    descripcion = payload.get("descripcion")

    service = RutinaService()
    try:
        creada = service.crear_rutina(
            usuario_id=current_user.id,
            nombre=nombre,
            ejercicios_items=ejercicios_items,
            es_favorita=es_favorita,
            dias_semana=dias_semana,
            descripcion=descripcion,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "DATOS_INVALIDOS"}), 400

    return jsonify(creada), 201


@rutina_bp.route("/api/rutinas/<int:rutina_id>", methods=["GET"])
@login_required
def obtener_rutina(rutina_id: int):
    """Obtiene el detalle de una rutina perteneciente al usuario autenticado."""
    service = RutinaService()
    try:
        rutina = service.obtener_rutina(
            usuario_id=current_user.id,
            rutina_id=rutina_id,
        )
    except RutinaNoEncontradaError as exc:
        return jsonify({"error": str(exc), "code": "NO_ENCONTRADO"}), 404

    return jsonify(rutina), 200


@rutina_bp.route("/api/rutinas/<int:rutina_id>", methods=["PUT"])
@login_required
def actualizar_rutina(rutina_id: int):
    """Actualiza el nombre y/o los ejercicios de una rutina del usuario."""
    payload = request.get_json(silent=True) or {}
    nombre = payload.get("nombre")
    ejercicios_items = payload.get("ejercicios")

    service = RutinaService()
    try:
        actualizada = service.actualizar_rutina(
            usuario_id=current_user.id,
            rutina_id=rutina_id,
            nombre=nombre,
            ejercicios_items=ejercicios_items,
        )
    except RutinaNoEncontradaError as exc:
        return jsonify({"error": str(exc), "code": "NO_ENCONTRADO"}), 404
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "DATOS_INVALIDOS"}), 400

    return jsonify(actualizada), 200


@rutina_bp.route("/api/rutinas/<int:rutina_id>", methods=["DELETE"])
@login_required
def eliminar_rutina(rutina_id: int):
    """Elimina una rutina perteneciente al usuario autenticado."""
    service = RutinaService()
    try:
        service.eliminar_rutina(
            usuario_id=current_user.id,
            rutina_id=rutina_id,
        )
    except RutinaNoEncontradaError as exc:
        return jsonify({"error": str(exc), "code": "NO_ENCONTRADO"}), 404

    return jsonify({"mensaje": "Rutina eliminada correctamente"}), 200


@rutina_bp.route("/api/rutinas/<int:rutina_id>/favorita", methods=["POST", "PATCH"])
@login_required
def alternar_favorita(rutina_id: int):
    """Alterna el estado de favorita de una rutina del usuario."""
    service = RutinaService()
    try:
        actualizada = service.alternar_favorita(
            usuario_id=current_user.id,
            rutina_id=rutina_id,
        )
    except RutinaNoEncontradaError as exc:
        return jsonify({"error": str(exc), "code": "NO_ENCONTRADO"}), 404

    return jsonify(actualizada), 200
