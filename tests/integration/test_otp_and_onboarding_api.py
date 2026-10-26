"""Pruebas de integración para Verificación OTP de 6 dígitos y Onboarding Biométrico (Fase V2.2)."""

import pytest


def test_flujo_otp_6_digitos_y_onboarding_biometrico(app, client):
    """Verifica generación OTP, rechazo de código inválido, éxito con código real y onboarding completo."""
    # 1. Registrar nueva usuaria y verificar generación de código OTP de 6 dígitos
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
    assert reg_data["email_verificado"] is False
    codigo_otp = reg_data["codigo_verificacion"]
    assert isinstance(codigo_otp, str)
    assert len(codigo_otp) == 6
    assert codigo_otp.isdigit()

    # 2. Vista HTML /verificar-correo responde 200 y muestra el código en modo demo
    resp_vista_otp = client.get("/verificar-correo")
    assert resp_vista_otp.status_code == 200
    assert codigo_otp in resp_vista_otp.get_data(as_text=True)

    # 3. Intentar verificar con un código incorrecto retorna 400
    codigo_incorrecto = "000000" if codigo_otp != "000000" else "999999"
    resp_bad_otp = client.post(
        "/api/auth/verify-code",
        json={"codigo": codigo_incorrecto},
    )
    assert resp_bad_otp.status_code == 400
    assert resp_bad_otp.get_json()["code"] == "CODIGO_INVALIDO"

    # 4. Probar reenvío de código OTP (POST /api/auth/resend-code)
    resp_resend = client.post("/api/auth/resend-code")
    assert resp_resend.status_code == 200
    nuevo_otp = resp_resend.get_json()["codigo_verificacion"]
    assert len(nuevo_otp) == 6
    assert nuevo_otp.isdigit()

    # 5. Verificar con el código correcto retorna 200 y marca email_verificado = True
    resp_ok_otp = client.post(
        "/api/auth/verify-code",
        json={"codigo": nuevo_otp},
    )
    assert resp_ok_otp.status_code == 200
    ok_data = resp_ok_otp.get_json()
    assert ok_data["email_verificado"] is True

    # 6. Vista HTML /onboarding responde 200 como wizard de 4 paneles independientes
    resp_vista_onb = client.get("/onboarding")
    assert resp_vista_onb.status_code == 200
    html_onb = resp_vista_onb.get_data(as_text=True)
    assert "Perfil Biométrico" in html_onb
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
    assert perfil_guardado["email_verificado"] is True

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

