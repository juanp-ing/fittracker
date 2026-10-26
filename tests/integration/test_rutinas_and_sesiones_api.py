"""Pruebas de integración para las APIs REST de Rutinas, Sesiones y detección de PRs."""

import pytest
from app.seeds import seed_database


def test_flujo_completo_rutina_sesion_series_prs_cronometro_y_cierre(app, client):
    """Verifica creación de rutina, inicio de sesión, detección de PRs, descanso y bloqueo al finalizar."""
    with app.app_context():
        seed_database()

    # 1. Registrar Usuario A
    client.post(
        "/api/auth/register",
        json={
            "nombre": "Atleta Principal",
            "email": "atleta_a@fittracker.local",
            "password": "Password123",
        },
    )

    # Obtener un ejercicio del catálogo (ej. Press de banca con barra)
    ejercicios = client.get("/api/ejercicios?q=Press de banca").get_json()["ejercicios"]
    ejercicio_id = ejercicios[0]["id"]

    # 2. Crear rutina con descanso personalizado (120s)
    crear_rutina_resp = client.post(
        "/api/rutinas",
        json={
            "nombre": "Torso Fuerza",
            "es_favorita": False,
            "ejercicios": [
                {
                    "ejercicio_id": ejercicio_id,
                    "orden": 1,
                    "descanso_segundos": 120,
                    "series_objetivo": 3,
                }
            ],
        },
    )
    assert crear_rutina_resp.status_code == 201
    rutina = crear_rutina_resp.get_json()
    rutina_id = rutina["id"]
    assert rutina["es_favorita"] is False
    assert rutina["ejercicios"][0]["descanso_segundos"] == 120

    # 3. Marcar rutina como favorita (POST /api/rutinas/<id>/favorita)
    fav_resp = client.post(f"/api/rutinas/{rutina_id}/favorita")
    assert fav_resp.status_code == 200
    assert fav_resp.get_json()["es_favorita"] is True

    # 4. Iniciar sesión vinculada a la rutina (POST /api/sesiones)
    iniciar_resp = client.post(
        "/api/sesiones",
        json={"rutina_id": rutina_id},
    )
    assert iniciar_resp.status_code == 201
    sesion = iniciar_resp.get_json()
    sesion_id = sesion["id"]
    assert sesion["estado"] == "ACTIVA"

    # 5. Primera serie: 80 kg x 8 reps -> Primer PR (es_pr: true) y descanso_segundos: 120
    s1_resp = client.post(
        f"/api/sesiones/{sesion_id}/series",
        json={
            "ejercicio_id": ejercicio_id,
            "peso": 80.0,
            "repeticiones": 8,
        },
    )
    assert s1_resp.status_code == 201
    s1_data = s1_resp.get_json()
    assert s1_data["es_pr"] is True
    assert s1_data["es_pr_peso"] is True
    assert s1_data["es_pr_volumen"] is True
    assert s1_data["descanso_segundos"] == 120

    # 6. Segunda serie: 75 kg x 8 reps -> NO es PR (es_pr: false)
    s2_resp = client.post(
        f"/api/sesiones/{sesion_id}/series",
        json={
            "ejercicio_id": ejercicio_id,
            "peso": 75.0,
            "repeticiones": 8,
        },
    )
    assert s2_resp.status_code == 201
    s2_data = s2_resp.get_json()
    assert s2_data["es_pr"] is False
    assert s2_data["es_pr_peso"] is False

    # 7. Tercera serie: 85 kg x 6 reps -> Nuevo PR de peso (es_pr: true)
    s3_resp = client.post(
        f"/api/sesiones/{sesion_id}/series",
        json={
            "ejercicio_id": ejercicio_id,
            "peso": 85.0,
            "repeticiones": 6,
        },
    )
    assert s3_resp.status_code == 201
    s3_data = s3_resp.get_json()
    assert s3_data["es_pr"] is True
    assert s3_data["es_pr_peso"] is True
    assert s3_data["peso_anterior"] == pytest.approx(80.0)
    assert s3_data["nuevo_pr_peso"] == pytest.approx(85.0)
    # 85 * 6 = 510 < 80 * 8 = 640, por tanto no es PR de volumen
    assert s3_data["es_pr_volumen"] is False

    # 8. Cerrar sesión (PATCH /api/sesiones/<id>/finalizar)
    fin_resp = client.patch(f"/api/sesiones/{sesion_id}/finalizar")
    assert fin_resp.status_code == 200
    fin_data = fin_resp.get_json()
    assert fin_data["estado"] == "FINALIZADA"
    assert fin_data["fecha_fin"] is not None
    assert fin_data["total_series"] == 3

    # 9. Intentar agregar otra serie a la sesión ya cerrada -> 400 Bad Request
    s4_resp = client.post(
        f"/api/sesiones/{sesion_id}/series",
        json={
            "ejercicio_id": ejercicio_id,
            "peso": 90.0,
            "repeticiones": 5,
        },
    )
    assert s4_resp.status_code == 400


def test_seguridad_multiusuario_rutinas_y_sesiones(app, client):
    """Verifica que el Usuario B no pueda modificar rutinas ni registrar series en la sesión del Usuario A."""
    with app.app_context():
        seed_database()

    # 1. Usuario A crea rutina e inicia sesión
    client.post(
        "/api/auth/register",
        json={
            "nombre": "Usuario A",
            "email": "usera_sec@fittracker.local",
            "password": "Password123",
        },
    )
    ej_id = client.get("/api/ejercicios").get_json()["ejercicios"][0]["id"]

    rutina_a = client.post(
        "/api/rutinas",
        json={
            "nombre": "Rutina Privada A",
            "ejercicios": [{"ejercicio_id": ej_id, "orden": 1}],
        },
    ).get_json()

    sesion_a = client.post(
        "/api/sesiones",
        json={"rutina_id": rutina_a["id"]},
    ).get_json()

    # 2. Cambiar a Usuario B
    client.post("/api/auth/logout")
    client.post(
        "/api/auth/register",
        json={
            "nombre": "Usuario B",
            "email": "userb_sec@fittracker.local",
            "password": "Password123",
        },
    )

    # Usuario B intenta modificar o eliminar la rutina de Usuario A -> 403 o 404
    put_rutina = client.put(
        f"/api/rutinas/{rutina_a['id']}",
        json={"nombre": "Hackeada"},
    )
    assert put_rutina.status_code in (403, 404)

    del_rutina = client.delete(f"/api/rutinas/{rutina_a['id']}")
    assert del_rutina.status_code in (403, 404)

    # Usuario B intenta registrar una serie en la sesión de Usuario A -> 403 o 404
    post_serie = client.post(
        f"/api/sesiones/{sesion_a['id']}/series",
        json={
            "ejercicio_id": ej_id,
            "peso": 100.0,
            "repeticiones": 5,
        },
    )
    assert post_serie.status_code in (403, 404)
