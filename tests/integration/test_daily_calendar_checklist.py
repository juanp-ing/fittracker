"""Pruebas de integración para el Mini-Calendario Semanal, Checklist Diario y Progreso por Ejercicio (Fase V2.4)."""

from app import create_app, db
from app.seeds.initial_data import seed_database


def _autenticar_usuario_con_rutina(client):
    """Registra usuario, verifica OTP y crea una rutina favorita de 2 ejercicios (3 series c/u)."""
    resp_reg = client.post(
        "/api/auth/register",
        json={
            "nombre": "Atleta Calendario",
            "email": "calendario@fittracker.local",
            "password": "Password123!",
        },
    )
    assert resp_reg.status_code == 201
    otp = resp_reg.get_json()["codigo_verificacion"]

    resp_ver = client.post("/api/auth/verify-code", json={"codigo": otp})
    assert resp_ver.status_code == 200

    ejercicios_cat = client.get("/api/ejercicios").get_json()["ejercicios"]
    ej_1 = ejercicios_cat[0]
    ej_2 = ejercicios_cat[1]

    resp_rutina = client.post(
        "/api/rutinas",
        json={
            "nombre": "Rutina Calendario Test",
            "es_favorita": True,
            "dias_semana": "LUN,MIE,VIE",
            "ejercicios": [
                {
                    "ejercicio_id": ej_1["id"],
                    "orden": 1,
                    "series_objetivo": 3,
                    "descanso_segundos": 90,
                },
                {
                    "ejercicio_id": ej_2["id"],
                    "orden": 2,
                    "series_objetivo": 3,
                    "descanso_segundos": 120,
                },
            ],
        },
    )
    assert resp_rutina.status_code == 201
    return resp_rutina.get_json(), ej_1, ej_2


def test_get_agenda_diaria_devuelve_7_dias_puntos_y_checklist_favorita():
    """Verifica que GET /api/sesiones/agenda-diaria retorne los 7 días con puntos y los ejercicios."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        seed_database(incluir_demo=False)
        client = app.test_client()

        rutina, ej_1, ej_2 = _autenticar_usuario_con_rutina(client)

        # Consultar una fecha fija (lunes 2026-10-26)
        resp = client.get("/api/sesiones/agenda-diaria?fecha=2026-10-26")
        assert resp.status_code == 200
        agenda = resp.get_json()

        assert agenda["fecha"] == "2026-10-26"
        assert agenda["mes_nombre"] == "octubre"
        assert agenda["rutina"]["id"] == rutina["id"]
        assert agenda["rutina"]["nombre"] == "Rutina Calendario Test"

        dias = agenda["dias_semana"]
        assert len(dias) == 7
        assert [d["abreviatura"] for d in dias] == [
            "dom",
            "lun",
            "mar",
            "mié",
            "jue",
            "vie",
            "sáb",
        ]

        # Verificar que lunes, miércoles y viernes llevan puntos indicadores >= 1
        mapa_dias = {d["codigo_dia"]: d for d in dias}
        assert mapa_dias["LUN"]["seleccionado"] is True
        assert mapa_dias["LUN"]["puntos"] >= 1
        assert mapa_dias["MIE"]["puntos"] >= 1
        assert mapa_dias["VIE"]["puntos"] >= 1
        assert mapa_dias["DOM"]["puntos"] == 0

        # Verificar lista de ejercicios del checklist diario
        ejercicios_hoy = agenda["ejercicios"]
        assert len(ejercicios_hoy) == 2
        assert ejercicios_hoy[0]["ejercicio_id"] == ej_1["id"]
        assert ejercicios_hoy[0]["series_objetivo"] == 3
        assert ejercicios_hoy[0]["series_completadas_hoy"] == 0
        assert ejercicios_hoy[0]["completado"] is False

        assert ejercicios_hoy[1]["ejercicio_id"] == ej_2["id"]
        assert ejercicios_hoy[1]["series_objetivo"] == 3
        assert ejercicios_hoy[1]["completado"] is False

        # Verificar que fecha inválida retorna 400
        resp_bad = client.get("/api/sesiones/agenda-diaria?fecha=fecha-invalida")
        assert resp_bad.status_code == 400

        db.drop_all()


def test_registrar_series_dispara_ejercicio_completado_ahora_y_siguiente_ejercicio():
    """Verifica que al completar 3 de 3 series devuelva ejercicio_completado_ahora=True y siguiente_ejercicio."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        seed_database(incluir_demo=False)
        client = app.test_client()

        rutina, ej_1, ej_2 = _autenticar_usuario_con_rutina(client)

        resp_sesion = client.post("/api/sesiones", json={"rutina_id": rutina["id"]})
        assert resp_sesion.status_code == 201
        sesion_id = resp_sesion.get_json()["id"]

        # Serie 1 de 3 del Ejercicio 1 -> aún no completado
        r1 = client.post(
            f"/api/sesiones/{sesion_id}/series",
            json={"ejercicio_id": ej_1["id"], "peso": 60.0, "repeticiones": 10},
        )
        assert r1.status_code == 201
        d1 = r1.get_json()
        assert d1["series_completadas_ejercicio"] == 1
        assert d1["series_objetivo_ejercicio"] == 3
        assert d1["ejercicio_completado_ahora"] is False
        assert d1["siguiente_ejercicio"]["id"] == ej_2["id"]

        # Serie 2 de 3 del Ejercicio 1 -> aún no completado
        r2 = client.post(
            f"/api/sesiones/{sesion_id}/series",
            json={"ejercicio_id": ej_1["id"], "peso": 62.5, "repeticiones": 10},
        )
        assert r2.status_code == 201
        d2 = r2.get_json()
        assert d2["series_completadas_ejercicio"] == 2
        assert d2["ejercicio_completado_ahora"] is False

        # Serie 3 de 3 del Ejercicio 1 -> ¡EJERCICIO COMPLETADO AHORA! + siguiente_ejercicio == ej_2
        r3 = client.post(
            f"/api/sesiones/{sesion_id}/series",
            json={"ejercicio_id": ej_1["id"], "peso": 65.0, "repeticiones": 8},
        )
        assert r3.status_code == 201
        d3 = r3.get_json()
        assert d3["series_completadas_ejercicio"] == 3
        assert d3["series_objetivo_ejercicio"] == 3
        assert d3["ejercicio_completado_ahora"] is True
        assert d3["siguiente_ejercicio"] is not None
        assert d3["siguiente_ejercicio"]["id"] == ej_2["id"]
        assert d3["siguiente_ejercicio"]["nombre"] == ej_2["nombre"]
        assert d3["siguiente_ejercicio"]["series_objetivo"] == 3
        assert d3["siguiente_ejercicio"]["descanso_segundos"] == 120

        # Verificar que GET /api/sesiones/agenda-diaria ahora marca el Ejercicio 1 como completado=True
        agenda_actualizada = client.get("/api/sesiones/agenda-diaria").get_json()
        ej_agenda_1 = agenda_actualizada["ejercicios"][0]
        ej_agenda_2 = agenda_actualizada["ejercicios"][1]
        assert ej_agenda_1["series_completadas_hoy"] == 3
        assert ej_agenda_1["completado"] is True
        assert ej_agenda_2["completado"] is False

        # Completar las 3 series del Ejercicio 2 -> al terminar toda la rutina, siguiente_ejercicio es None
        for _ in range(2):
            client.post(
                f"/api/sesiones/{sesion_id}/series",
                json={"ejercicio_id": ej_2["id"], "peso": 40.0, "repeticiones": 12},
            )
        r_final = client.post(
            f"/api/sesiones/{sesion_id}/series",
            json={"ejercicio_id": ej_2["id"], "peso": 42.5, "repeticiones": 12},
        )
        assert r_final.status_code == 201
        d_final = r_final.get_json()
        assert d_final["ejercicio_completado_ahora"] is True
        assert d_final["siguiente_ejercicio"] is None

        # Verificar elementos de UI en la vista principal /
        html_index = client.get("/").get_data(as_text=True)
        assert "Mostrar completados" in html_index
        assert "modal-ejercicio-terminado" in html_index
        assert "Recuerda tomar agua: hidrátate bien antes de tu siguiente bloque" in html_index

        db.drop_all()

