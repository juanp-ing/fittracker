"""Controlador de vistas HTML y endpoints REST para Sesiones de entrenamiento, Agenda Diaria y Series."""

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from app.patterns.state import SesionCerradaError
from app.services.rutina_service import RutinaService
from app.services.sesion_service import SesionNoEncontradaError, SesionService
from app.services.zona_horaria import COOKIE_ZONA_HORARIA

sesion_bp = Blueprint("sesion", __name__)


# La ruta canónica va última: Flask la registra primero y url_for() la usa.
@sesion_bp.route("/entrenar", methods=["GET"])
@sesion_bp.route("/", methods=["GET"])
@login_required
def vista_entrenar():
    """Renderiza la pantalla principal de entrenamiento rápido con Mini-Calendario Semanal y Checklist."""
    rutina_service = RutinaService()
    sesion_service = SesionService()
    rutinas = rutina_service.listar_rutinas_usuario(usuario_id=current_user.id)
    agenda_hoy = sesion_service.obtener_agenda_diaria(
        usuario_id=current_user.id,
        # «Entrenar esta rutina» (desde Rutinas) llega como ?rutina_id=; si no es del
        # usuario, el servicio cae en su rutina principal.
        rutina_id=request.args.get("rutina_id", type=int),
        zona_horaria=request.cookies.get(COOKIE_ZONA_HORARIA),
    )
    sesion_activa = sesion_service.obtener_sesion_activa(usuario_id=current_user.id)
    return render_template(
        "index.html",
        active_tab="entrenar",
        rutinas=rutinas,
        agenda_hoy=agenda_hoy,
        sesion_activa=sesion_activa,
    )


@sesion_bp.route("/api/sesiones/agenda-diaria", methods=["GET"])
@login_required
def obtener_agenda_diaria():
    """Devuelve los 7 días de la semana con puntos indicadores y el checklist de ejercicios del día."""
    fecha = request.args.get("fecha")
    rutina_id = request.args.get("rutina_id", type=int)
    service = SesionService()
    try:
        agenda = service.obtener_agenda_diaria(
            usuario_id=current_user.id,
            fecha_str=fecha,
            rutina_id=rutina_id,
            zona_horaria=request.cookies.get(COOKIE_ZONA_HORARIA),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "FECHA_INVALIDA"}), 400

    return jsonify(agenda), 200


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
    """Registra una serie en la sesión activa, evalúa PRs y devuelve el descanso y progreso diario."""
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
            zona_horaria=request.cookies.get(COOKIE_ZONA_HORARIA),
        )
    except SesionNoEncontradaError as exc:
        return jsonify({"error": str(exc), "code": "NO_ENCONTRADO"}), 404
    except (SesionCerradaError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "DATOS_INVALIDOS"}), 400

    return jsonify(resultado), 201


@sesion_bp.route("/api/sesiones/<int:sesion_id>/series/<int:serie_id>", methods=["DELETE"])
@login_required
def eliminar_serie(sesion_id: int, serie_id: int):
    """Deshace una serie registrada por error en una sesión activa."""
    service = SesionService()
    try:
        resultado = service.eliminar_serie(
            usuario_id=current_user.id,
            sesion_id=sesion_id,
            serie_id=serie_id,
        )
    except SesionNoEncontradaError as exc:
        return jsonify({"error": str(exc), "code": "NO_ENCONTRADO"}), 404
    except SesionCerradaError as exc:
        return jsonify({"error": str(exc), "code": "SESION_CERRADA"}), 400

    return jsonify(resultado), 200


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
