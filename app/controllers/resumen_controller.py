"""Controlador de vistas HTML y endpoints REST para Historial, Progreso, Mapa Muscular y Resumen."""

from datetime import datetime, timezone
from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from app.patterns.facade import ResumenFacade
from app.services.ejercicio_service import EjercicioService
from app.services.resumen_service import ResumenService

resumen_bp = Blueprint("resumen", __name__)


@resumen_bp.route("/mapa", methods=["GET"])
@login_required
def vista_mapa():
    """Renderiza la vista del Mapa Muscular Bicolor y Gráficas de Progreso/PRs."""
    ej_service = EjercicioService()
    ejercicios = ej_service.buscar_ejercicios_usuario(usuario_id=current_user.id)
    return render_template(
        "resumen/mapa.html",
        active_tab="mapa",
        ejercicios=ejercicios,
    )


@resumen_bp.route("/resumen", methods=["GET"])
@login_required
def vista_resumen():
    """Renderiza la vista del Resumen Mensual de 30 días."""
    return render_template(
        "resumen/index.html",
        active_tab="resumen",
    )


@resumen_bp.route("/api/historial", methods=["GET"])
@login_required
def obtener_historial():
    """Retorna el historial paginado de sesiones de entrenamiento del usuario."""
    try:
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        limit, offset = 20, 0

    service = ResumenService()
    sesiones = service.obtener_historial_sesiones(
        usuario_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return jsonify({"sesiones": sesiones, "historial": sesiones}), 200


@resumen_bp.route("/api/progreso/<int:ejercicio_id>", methods=["GET"])
@login_required
def obtener_progreso_ejercicio(ejercicio_id: int):
    """Retorna la evolución histórica de peso y volumen para un ejercicio."""
    service = ResumenService()
    try:
        progreso = service.obtener_progreso_ejercicio(
            usuario_id=current_user.id,
            ejercicio_id=ejercicio_id,
        )
    except LookupError as exc:
        return jsonify({"error": str(exc), "code": "NO_ENCONTRADO"}), 404

    return jsonify(progreso), 200


@resumen_bp.route("/api/mapa-muscular", methods=["GET"])
@login_required
def obtener_mapa_muscular():
    """Retorna los grupos musculares trabajados (primarios vs. secundarios)."""
    desde_param = request.args.get("desde")
    dias_param = request.args.get("dias", "7")

    fecha_desde = None
    dias = 7

    if desde_param:
        try:
            if desde_param.isdigit():
                dias = int(desde_param)
            else:
                dt = datetime.fromisoformat(desde_param)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                fecha_desde = dt
        except ValueError:
            return (
                jsonify(
                    {
                        "error": "El parámetro 'desde' debe tener formato ISO (YYYY-MM-DD) o entero.",
                        "code": "DATOS_INVALIDOS",
                    }
                ),
                400,
            )
    else:
        try:
            dias = int(dias_param)
        except ValueError:
            dias = 7

    service = ResumenService()
    mapa = service.obtener_mapa_muscular(
        usuario_id=current_user.id,
        dias=dias,
        fecha_desde=fecha_desde,
    )
    return jsonify(mapa), 200


@resumen_bp.route("/api/resumen-mensual", methods=["GET"])
@login_required
def obtener_resumen_mensual():
    """Consolida el Resumen Mensual mediante el patrón ResumenFacade."""
    facade = ResumenFacade()
    resumen = facade.obtener_resumen_mensual(usuario_id=current_user.id)
    return jsonify(resumen), 200
