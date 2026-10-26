"""Pruebas de integración para el catálogo de 40 ejercicios comerciales y el motor de 12 Rutinas Famosas."""

from app import create_app, db
from app.seeds.initial_data import seed_database


def _registrar_y_configurar_perfil(
    client,
    email: str,
    sexo: str = "HOMBRE",
    peso_kg: float = 64.0,
    porcentaje_grasa: float = 12.0,
    meta: str = "GANAR_MASA",
    somatotipo: str = "ECTOMORFO",
):
    resp_reg = client.post(
        "/api/auth/register",
        json={
            "nombre": "Atleta Test",
            "email": email,
            "password": "Password123!",
        },
    )
    assert resp_reg.status_code == 201
    codigo_otp = resp_reg.get_json()["codigo_verificacion"]

    resp_ver = client.post(
        "/api/auth/verify-code",
        json={"codigo": codigo_otp},
    )
    assert resp_ver.status_code == 200

    resp_perfil = client.put(
        "/api/perfil",
        json={
            "sexo": sexo,
            "peso_kg": peso_kg,
            "porcentaje_grasa": porcentaje_grasa,
            "meta": meta,
            "somatotipo": somatotipo,
        },
    )
    assert resp_perfil.status_code == 200
    return resp_perfil.get_json()


def test_seed_database_crea_al_menos_38_ejercicios_y_12_rutinas_famosas():
    """Verifica que seed_database() cree >= 38 ejercicios comerciales y las 12 rutinas famosas."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        resumen_seed = seed_database(incluir_demo=True)
        assert resumen_seed["total_grupos"] == 10
        assert resumen_seed["total_ejercicios"] >= 38
        assert resumen_seed["total_rutinas_famosas"] == 12

        # Segunda ejecución idempotente no duplica registros
        segundo_seed = seed_database(incluir_demo=True)
        assert segundo_seed["ejercicios_creados"] == 0
        assert segundo_seed["rutinas_famosas_creadas"] == 0
        assert segundo_seed["total_rutinas_famosas"] == 12
        db.drop_all()


def test_get_rutinas_famosas_prioriza_ectomorfo_ganar_masa():
    """Verifica que GET /api/rutinas/famosas priorice ECTOMORFO + GANAR_MASA para ese perfil."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        seed_database(incluir_demo=False)
        client = app.test_client()

        _registrar_y_configurar_perfil(
            client,
            email="ectomorfo@fittracker.local",
            sexo="HOMBRE",
            peso_kg=62.0,
            porcentaje_grasa=10.0,
            meta="GANAR_MASA",
            somatotipo="ECTOMORFO",
        )

        resp = client.get("/api/rutinas/famosas")
        assert resp.status_code == 200
        datos = resp.get_json()
        famosas = datos["rutinas_famosas"]
        assert len(famosas) == 12

        # Las dos primeras deben ser las de ECTOMORFO + GANAR_MASA con match_score == 100
        top_1 = famosas[0]
        top_2 = famosas[1]
        assert top_1["somatotipo_ideal"] == "ECTOMORFO"
        assert top_1["meta_objetivo"] == "GANAR_MASA"
        assert top_1["recomendada_para_ti"] is True
        assert top_1["match_score"] == 100

        assert top_2["somatotipo_ideal"] == "ECTOMORFO"
        assert top_2["meta_objetivo"] == "GANAR_MASA"
        assert top_2["recomendada_para_ti"] is True
        assert top_2["match_score"] == 100

        # Probar filtro opcional ?somatotipo=ENDOMORFO&meta=BAJAR_PESO
        resp_filtro = client.get("/api/rutinas/famosas?somatotipo=ENDOMORFO&meta=BAJAR_PESO")
        assert resp_filtro.status_code == 200
        filtradas = resp_filtro.get_json()["rutinas_famosas"]
        assert len(filtradas) == 2
        assert all(r["somatotipo_ideal"] == "ENDOMORFO" for r in filtradas)
        assert all(r["meta_objetivo"] == "BAJAR_PESO" for r in filtradas)

        db.drop_all()


def test_post_clonar_rutina_famosa_copia_ejercicios_y_dias_semana():
    """Verifica que POST /api/rutinas/famosas/<id>/clonar clone la plantilla al usuario."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        seed_database(incluir_demo=False)
        client = app.test_client()

        _registrar_y_configurar_perfil(
            client,
            email="clonador@fittracker.local",
            sexo="MUJER",
            peso_kg=58.0,
            porcentaje_grasa=22.0,
            meta="DEFINIR",
            somatotipo="MESOMORFO",
        )

        # Inicialmente el usuario no tiene rutinas personales
        resp_mis_inicial = client.get("/api/rutinas")
        assert resp_mis_inicial.status_code == 200
        assert len(resp_mis_inicial.get_json()["rutinas"]) == 0

        # Obtener catálogo de famosas y elegir Strong Curves o la primera recomendada
        famosas = client.get("/api/rutinas/famosas").get_json()["rutinas_famosas"]
        plantilla_elegida = famosas[0]

        resp_clon = client.post(f"/api/rutinas/famosas/{plantilla_elegida['id']}/clonar")
        assert resp_clon.status_code == 201
        rutina_clonada = resp_clon.get_json()

        assert rutina_clonada["id"] != plantilla_elegida["id"]
        assert rutina_clonada["nombre"] == plantilla_elegida["nombre"]
        assert rutina_clonada["es_favorita"] is True
        assert rutina_clonada["es_plantilla_famosa"] is False
        assert rutina_clonada["dias_semana"] == plantilla_elegida["dias_semana"]
        assert len(rutina_clonada["ejercicios"]) == len(plantilla_elegida["ejercicios"])
        assert len(rutina_clonada["ejercicios"]) >= 5

        # Verificar que ahora aparece en GET /api/rutinas del usuario
        mis_rutinas = client.get("/api/rutinas").get_json()["rutinas"]
        assert len(mis_rutinas) == 1
        assert mis_rutinas[0]["nombre"] == plantilla_elegida["nombre"]
        assert mis_rutinas[0]["dias_semana"] == plantilla_elegida["dias_semana"]

        # Verificar vistas HTML de Onboarding (Guía Visual Grasa) y Rutinas (Pestañas)
        html_onb = client.get("/onboarding").get_data(as_text=True)
        assert "Atlético / Muy Definido" in html_onb
        assert "Fitness / Saludable" in html_onb
        assert "Promedio / Normal" in html_onb
        assert "Alto / Sobrepeso Inicial" in html_onb

        html_rutinas = client.get("/rutinas").get_data(as_text=True)
        assert "Rutinas Famosas (12)" in html_rutinas
        assert "IDEAL PARA TU PERFIL" in html_rutinas

        db.drop_all()
