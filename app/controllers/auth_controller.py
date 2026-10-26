"""Controlador de vistas HTML y endpoints REST para autenticación, OTP y onboarding biométrico."""

from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.services.auth_service import AuthService, EmailDuplicadoError

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET"])
def vista_login():
    """Renderiza la vista mobile-first de inicio de sesión."""
    if current_user.is_authenticated:
        return redirect(url_for("sesion.vista_entrenar"))
    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET"])
@auth_bp.route("/registro", methods=["GET"])
def vista_registro():
    """Renderiza la vista mobile-first de registro de cuenta."""
    if current_user.is_authenticated:
        return redirect(url_for("sesion.vista_entrenar"))
    return render_template("auth/register.html")


@auth_bp.route("/verificar-correo", methods=["GET"])
@login_required
def vista_verificar_correo():
    """Renderiza la pantalla de verificación de correo con código OTP de 6 dígitos."""
    return render_template(
        "auth/verify_email.html",
        codigo_demo=current_user.codigo_verificacion,
        email_usuario=current_user.email,
    )


@auth_bp.route("/onboarding", methods=["GET"])
@login_required
def vista_onboarding():
    """Renderiza el wizard interactivo de 4 pasos de onboarding biométrico estilo Duolingo."""
    service = AuthService()
    perfil = service.obtener_perfil_usuario(current_user.id)
    return render_template("auth/onboarding.html", perfil=perfil)


@auth_bp.route("/api/auth/register", methods=["POST"])
@auth_bp.route("/api/auth/registro", methods=["POST"])
def register():
    """Registra un nuevo usuario, genera su código OTP de 6 dígitos e inicia su sesión."""
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
                "email_verificado": usuario.email_verificado,
                "codigo_verificacion": usuario.codigo_verificacion,
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
                "email_verificado": usuario.email_verificado,
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


@auth_bp.route("/api/auth/verify-code", methods=["POST"])
@login_required
def verify_code():
    """Verifica el código OTP de 6 dígitos del usuario autenticado."""
    payload = request.get_json(silent=True) or {}
    codigo = payload.get("codigo") or payload.get("code") or ""

    service = AuthService()
    try:
        resultado = service.verificar_codigo_email(
            usuario_id=current_user.id,
            codigo=str(codigo),
        )
    except ValueError as exc:
        return (
            jsonify(
                {
                    "error": str(exc),
                    "code": "CODIGO_INVALIDO",
                }
            ),
            400,
        )

    return jsonify(resultado), 200


@auth_bp.route("/api/auth/resend-code", methods=["POST"])
@login_required
def resend_code():
    """Regenera y reenvía un nuevo código OTP de 6 dígitos al usuario autenticado."""
    service = AuthService()
    nuevo_codigo = service.reenviar_codigo_email(usuario_id=current_user.id)
    return (
        jsonify(
            {
                "mensaje": "Nuevo código de verificación enviado.",
                "codigo_verificacion": nuevo_codigo,
            }
        ),
        200,
    )


@auth_bp.route("/api/perfil", methods=["GET"])
@login_required
def obtener_perfil():
    """Retorna el perfil biométrico y estado de onboarding del usuario autenticado."""
    service = AuthService()
    perfil = service.obtener_perfil_usuario(usuario_id=current_user.id)
    return jsonify(perfil), 200


@auth_bp.route("/api/perfil", methods=["PUT", "POST"])
@login_required
def actualizar_perfil():
    """Valida y guarda los datos biométricos, meta y somatotipo del usuario autenticado."""
    payload = request.get_json(silent=True) or {}
    service = AuthService()
    try:
        perfil = service.guardar_onboarding_perfil(
            usuario_id=current_user.id,
            sexo=payload.get("sexo", "HOMBRE"),
            peso_kg=payload.get("peso_kg", 70.0),
            porcentaje_grasa=payload.get("porcentaje_grasa"),
            meta=payload.get("meta", "GANAR_MASA"),
            somatotipo=payload.get("somatotipo", "ECTOMORFO"),
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

    return jsonify(perfil), 200
