"""Pruebas de integración del registro directo y el Onboarding Biométrico (Fase V2.2)."""

import pytest


def test_registro_directo_y_onboarding_biometrico(app, client):
    """El registro inicia sesión sin verificación por correo y lleva al onboarding completo."""
    # 1. Registrar nueva usuaria: entra directamente, sin código de verificación.
    resp_reg = client.post(
        "/api/auth/register",
        json={
            "nombre": "Valeria Fitness",
            "email": "valeria@fittracker.local",
            "password": "Password123!",
        },
    )
    assert resp_reg.status_code == 201
    reg_data = resp_reg.get_json()
    assert "codigo_verificacion" not in reg_data
    assert "email_verificado" not in reg_data

    # La verificación por correo se retiró: sus rutas ya no existen.
    assert client.get("/verificar-correo").status_code == 404
    assert client.post("/api/auth/verify-code", json={"codigo": "123456"}).status_code == 404
    assert client.post("/api/auth/resend-code").status_code == 404

    # 6. Vista HTML /onboarding responde 200 como wizard de 4 paneles independientes
    resp_vista_onb = client.get("/onboarding")
    assert resp_vista_onb.status_code == 200
    html_onb = resp_vista_onb.get_data(as_text=True)
    assert "<title>Tu perfil — FitTracker</title>" in html_onb
    for paso in range(1, 5):
        assert f'data-step="{paso}"' in html_onb
        assert f'data-step-tab="{paso}"' in html_onb
    # Solo el Paso 1 visible al cargar: los pasos 2-4 llevan el atributo hidden
    assert html_onb.count('class="onboarding-step-pane"') == 4
    for paso in range(2, 5):
        assert f'class="onboarding-step-pane" data-step="{paso}" hidden' in html_onb
    assert 'class="onboarding-step-pane" data-step="1" hidden' not in html_onb
    assert 'id="btn-wizard-atras"' in html_onb
    assert 'id="btn-wizard-siguiente"' in html_onb

    # 7. Guardar onboarding (PUT /api/perfil) con datos de Valeria y leer en GET /api/perfil
    resp_put_perfil = client.put(
        "/api/perfil",
        json={
            "sexo": "MUJER",
            "peso_kg": 62.5,
            "porcentaje_grasa": 18.0,
            "meta": "DEFINIR",
            "somatotipo": "ECTOMORFO",
        },
    )
    assert resp_put_perfil.status_code == 200
    perfil_guardado = resp_put_perfil.get_json()
    assert perfil_guardado["sexo"] == "MUJER"
    assert perfil_guardado["peso_kg"] == pytest.approx(62.5)
    assert perfil_guardado["porcentaje_grasa"] == pytest.approx(18.0)
    assert perfil_guardado["meta"] == "DEFINIR"
    assert perfil_guardado["somatotipo"] == "ECTOMORFO"
    assert perfil_guardado["onboarding_completado"] is True

    resp_get_perfil = client.get("/api/perfil")
    assert resp_get_perfil.status_code == 200
    perfil_leido = resp_get_perfil.get_json()
    assert perfil_leido["sexo"] == "MUJER"
    assert perfil_leido["peso_kg"] == pytest.approx(62.5)
    assert perfil_leido["meta"] == "DEFINIR"
    assert perfil_leido["somatotipo"] == "ECTOMORFO"

    # 8. Verificar que el Mapa Muscular (/mapa) conecta por defecto el sexo del perfil ("MUJER")
    resp_mapa = client.get("/mapa")
    assert resp_mapa.status_code == 200
    assert 'data-sexo-perfil="MUJER"' in resp_mapa.get_data(as_text=True)


@pytest.mark.parametrize(
    "payload_invalido",
    [
        {
            "sexo": "OTRO_INVALIDO",
            "peso_kg": 70.0,
            "porcentaje_grasa": 15.0,
            "meta": "GANAR_MASA",
            "somatotipo": "MESOMORFO",
        },
        {
            "sexo": "HOMBRE",
            "peso_kg": 70.0,
            "porcentaje_grasa": 15.0,
            "meta": "META_INEXISTENTE",
            "somatotipo": "MESOMORFO",
        },
        {
            "sexo": "HOMBRE",
            "peso_kg": 70.0,
            "porcentaje_grasa": 15.0,
            "meta": "GANAR_MASA",
            "somatotipo": "HIPERMORFO",
        },
        {
            "sexo": "HOMBRE",
            "peso_kg": 10.0,
            "porcentaje_grasa": 15.0,
            "meta": "GANAR_MASA",
            "somatotipo": "MESOMORFO",
        },
        {
            "sexo": "HOMBRE",
            "peso_kg": 70.0,
            "porcentaje_grasa": 85.0,
            "meta": "GANAR_MASA",
            "somatotipo": "MESOMORFO",
        },
    ],
)
def test_onboarding_rechaza_enums_y_rangos_invalidos(app, client, payload_invalido):
    """Verifica que PUT /api/perfil retorne 400 ante metas, somatotipos, sexos o rangos inválidos."""
    client.post(
        "/api/auth/register",
        json={
            "nombre": "Tester Validación",
            "email": "tester_val@fittracker.local",
            "password": "Password123!",
        },
    )
    resp = client.put("/api/perfil", json=payload_invalido)
    assert resp.status_code == 400
    assert resp.get_json()["code"] == "DATOS_INVALIDOS"



def test_base_antigua_con_columnas_otp_sigue_registrando(tmp_path, monkeypatch):
    """Una base creada con la verificación por correo (email_verificado NOT NULL) no rompe el registro."""
    import sqlite3

    from app import create_app, db
    from app.config.settings import DevelopmentConfig
    from app.seeds import seed_database

    ruta = tmp_path / "antigua.db"
    monkeypatch.setattr(DevelopmentConfig, "SQLALCHEMY_DATABASE_URI", f"sqlite:///{ruta}")
    app = create_app("development")
    with app.app_context():
        db.create_all()
        db.session.execute(db.text("ALTER TABLE usuarios ADD COLUMN email_verificado BOOLEAN NOT NULL DEFAULT 0"))
        db.session.execute(db.text("ALTER TABLE usuarios ADD COLUMN codigo_verificacion VARCHAR(6)"))
        db.session.commit()
        seed_database(incluir_demo=False)
        db.session.remove()

    columnas = {fila[1] for fila in sqlite3.connect(ruta).execute("PRAGMA table_info(usuarios)")}
    assert not {"email_verificado", "codigo_verificacion"} & columnas

    resp = app.test_client().post(
        "/api/auth/register",
        json={"nombre": "Antigua", "email": "antigua@fittracker.local", "password": "Password123!"},
    )
    assert resp.status_code == 201
