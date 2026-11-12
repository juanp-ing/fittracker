"""El código de verificación no debe salir del servidor fuera de desarrollo y pruebas."""

from datetime import datetime, timedelta, timezone

from app.config.settings import DevelopmentConfig, ProductionConfig, TestingConfig
from app.models.usuario import Usuario
from app import db


def _registrar(client, email="otp.privado@fittracker.local"):
    return client.post(
        "/api/auth/register",
        json={"nombre": "Otp Privado", "email": email, "password": "Secreta123"},
    )


def test_solo_desarrollo_y_pruebas_exponen_el_codigo():
    assert DevelopmentConfig.EXPONER_CODIGO_OTP is True
    assert TestingConfig.EXPONER_CODIGO_OTP is True
    assert ProductionConfig.EXPONER_CODIGO_OTP is False


def test_sin_exponer_el_registro_no_devuelve_el_codigo(app, client):
    app.config["EXPONER_CODIGO_OTP"] = False

    resp = _registrar(client)

    assert resp.status_code == 201
    assert "codigo_verificacion" not in resp.get_json()
    codigo = db.session.query(Usuario).filter_by(email="otp.privado@fittracker.local").one().codigo_verificacion
    assert codigo and len(codigo) == 6


def test_sin_exponer_la_pantalla_no_muestra_el_codigo(app, client):
    app.config["EXPONER_CODIGO_OTP"] = False
    _registrar(client)
    codigo = db.session.query(Usuario).one().codigo_verificacion

    html = client.get("/verificar-correo").get_data(as_text=True)

    assert codigo not in html
    assert 'id="otp-demo-banner"' not in html


def test_sin_exponer_el_reenvio_no_devuelve_el_codigo(app, client):
    app.config["EXPONER_CODIGO_OTP"] = False
    _registrar(client)

    resp = client.post("/api/auth/resend-code")

    assert resp.status_code == 200
    assert "codigo_verificacion" not in resp.get_json()


def test_en_desarrollo_la_pantalla_muestra_el_codigo(app, client):
    _registrar(client)
    codigo = db.session.query(Usuario).one().codigo_verificacion

    html = client.get("/verificar-correo").get_data(as_text=True)

    assert codigo in html


def test_el_reenvio_tiene_una_espera_minima(app, client):
    app.config["OTP_ESPERA_REENVIO_SEGUNDOS"] = 60
    _registrar(client)

    resp = client.post("/api/auth/resend-code")

    assert resp.status_code == 429
    datos = resp.get_json()
    assert datos["code"] == "REENVIO_DEMASIADO_PRONTO"
    assert 0 < datos["segundos_restantes"] <= 60


def test_el_reenvio_se_permite_pasada_la_espera(app, client):
    app.config["OTP_ESPERA_REENVIO_SEGUNDOS"] = 60
    _registrar(client)
    usuario = db.session.query(Usuario).one()
    # El código se generó hace 2 minutos: caduca dentro de 8.
    usuario.codigo_expiracion = datetime.now(timezone.utc) + timedelta(minutes=8)
    db.session.commit()

    assert client.post("/api/auth/resend-code").status_code == 200


def test_sin_smtp_avisa_en_el_log(app, client, caplog, monkeypatch):
    for variable in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"):
        monkeypatch.delenv(variable, raising=False)
    app.config["EXPONER_CODIGO_OTP"] = False

    with caplog.at_level("WARNING"):
        _registrar(client)

    assert any("SMTP" in registro.getMessage() for registro in caplog.records)
