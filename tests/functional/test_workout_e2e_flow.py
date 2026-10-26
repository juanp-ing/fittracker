"""Prueba funcional End-to-End (E2E) del flujo completo de entrenamiento de Mateo (Sección 8 del PDR)."""

from app.seeds import seed_database


def test_flujo_completo_mateo_e2e(app, client):
    """Ejecuta de principio a fin el escenario de Mateo desde seed hasta el Resumen Mensual."""
    # 1. Inicializar semillas (10 grupos musculares, 23 ejercicios base y usuario demo)
    with app.app_context():
        res_seed = seed_database(incluir_demo=True)
        assert res_seed["total_grupos"] == 10
        assert res_seed["total_ejercicios"] >= 23
        assert res_seed["demo_email"] == "demo@fittracker.local"

    # Verificar que el usuario de demostración puede iniciar sesión de inmediato
    resp_demo_login = client.post(
        "/api/auth/login",
        json={"email": "demo@fittracker.local", "password": "FitTracker123!"},
    )
    assert resp_demo_login.status_code == 200
    client.post("/api/auth/logout")

    # 2. Registro e inicio de sesión de Mateo
    resp_reg = client.post(
        "/api/auth/register",
        json={
            "nombre": "Mateo Gómez",
            "email": "mateo@fittracker.local",
            "password": "MateoGym2026!",
        },
    )
    assert resp_reg.status_code == 201
    mateo_id = resp_reg.get_json()["id"]
    assert mateo_id > 0

    # Consultar catálogo de grupos musculares y ejercicios predeterminados
    grupos = client.get("/api/grupos-musculares").get_json()["grupos_musculares"]
    mapa_grupos = {g["nombre"]: g["id"] for g in grupos}
    ejercicios_base = client.get("/api/ejercicios?q=Press de banca").get_json()["ejercicios"]
    assert len(ejercicios_base) >= 1
    press_banca_id = ejercicios_base[0]["id"]

    # 3. Crear ejercicio personalizado con músculo primario (Pecho) y secundarios (Hombros, Tríceps)
    resp_custom_ej = client.post(
        "/api/ejercicios",
        json={
            "nombre": "Press Vikingo en Máquina",
            "grupos_primarios_ids": [mapa_grupos["Pecho"]],
            "grupos_secundarios_ids": [mapa_grupos["Hombros"], mapa_grupos["Tríceps"]],
        },
    )
    assert resp_custom_ej.status_code == 201
    custom_ej = resp_custom_ej.get_json()
    custom_ej_id = custom_ej["id"]
    assert custom_ej["es_predeterminado"] is False

    # 4. Crear rutina favorita con descanso personalizado (120s en Press Banca y 150s en Press Vikingo)
    resp_rutina = client.post(
        "/api/rutinas",
        json={
            "nombre": "Empuje Pesado Mateo",
            "es_favorita": True,
            "ejercicios": [
                {
                    "ejercicio_id": press_banca_id,
                    "orden": 1,
                    "series_objetivo": 3,
                    "descanso_segundos": 120,
                },
                {
                    "ejercicio_id": custom_ej_id,
                    "orden": 2,
                    "series_objetivo": 3,
                    "descanso_segundos": 150,
                },
            ],
        },
    )
    assert resp_rutina.status_code == 201
    rutina_data = resp_rutina.get_json()
    rutina_id = rutina_data["id"]
    assert rutina_data["es_favorita"] is True

    # 5. Iniciar sesión de entrenamiento vinculada a la rutina favorita
    resp_sesion = client.post("/api/sesiones", json={"rutina_id": rutina_id})
    assert resp_sesion.status_code == 201
    sesion_data = resp_sesion.get_json()
    sesion_id = sesion_data["id"]
    assert sesion_data["estado"] == "ACTIVA"

    # 6. Guardar 3 series en el ejercicio personalizado subiendo de peso (60 kg -> 70 kg -> 75 kg)
    pesos_y_reps = [(60.0, 10), (70.0, 8), (75.0, 6)]
    for idx, (peso, reps) in enumerate(pesos_y_reps, start=1):
        resp_serie = client.post(
            f"/api/sesiones/{sesion_id}/series",
            json={
                "ejercicio_id": custom_ej_id,
                "peso": peso,
                "repeticiones": reps,
            },
        )
        assert resp_serie.status_code == 201
        serie_json = resp_serie.get_json()
        assert serie_json["peso"] == peso
        assert serie_json["repeticiones"] == reps
        assert serie_json["volumen"] == peso * reps
        assert serie_json["es_pr"] is True
        assert serie_json["nuevo_pr_peso"] == peso
        assert serie_json["descanso_segundos"] == 150

    # 7. Finalizar la sesión y verificar bloqueo de mutación posterior (Patrón State)
    resp_fin = client.patch(f"/api/sesiones/{sesion_id}/finalizar")
    assert resp_fin.status_code == 200
    assert resp_fin.get_json()["estado"] == "FINALIZADA"

    resp_bloqueada = client.post(
        f"/api/sesiones/{sesion_id}/series",
        json={"ejercicio_id": custom_ej_id, "peso": 80.0, "repeticiones": 5},
    )
    assert resp_bloqueada.status_code == 400
    assert "finalizada" in resp_bloqueada.get_json()["error"].lower()

    # 8. Consultar Mapa Muscular Bicolor (/api/mapa-muscular)
    resp_mapa = client.get("/api/mapa-muscular?dias=7")
    assert resp_mapa.status_code == 200
    mapa_json = resp_mapa.get_json()
    assert "Pecho" in mapa_json["primarios"]
    assert "Hombros" in mapa_json["secundarios"]
    assert "Tríceps" in mapa_json["secundarios"]

    # 9. Consultar Progreso del Ejercicio (/api/progreso/<id>)
    resp_prog = client.get(f"/api/progreso/{custom_ej_id}")
    assert resp_prog.status_code == 200
    prog_json = resp_prog.get_json()
    assert prog_json["pr_historico"] == 75.0
    assert prog_json["pesos_maximos"] == [75.0]

    # 10. Consultar Resumen Mensual (/api/resumen-mensual) y Historial (/api/historial)
    resp_resumen = client.get("/api/resumen-mensual")
    assert resp_resumen.status_code == 200
    resumen_json = resp_resumen.get_json()
    assert resumen_json["total_sesiones"] == 1
    assert resumen_json["total_series"] == 3
    assert resumen_json["volumen_total_kg"] == (60.0 * 10 + 70.0 * 8 + 75.0 * 6)
    assert resumen_json["nuevos_prs"] >= 1
    assert any(
        p["ejercicio_id"] == custom_ej_id for p in resumen_json["prs_detalle"]
    )

    resp_hist = client.get("/api/historial")
    assert resp_hist.status_code == 200
    assert len(resp_hist.get_json()["sesiones"]) == 1
