"""Pruebas de integración para Resumen Mensual (Facade), Mapa Muscular Bicolor, Progreso e Historial."""

from datetime import datetime, timedelta, timezone
import pytest

from app import db
from app.repositories import (
    EjercicioRepository,
    PRRepository,
    SesionRepository,
)
from app.seeds import seed_database


def test_resumen_mensual_mapa_muscular_bicolor_progreso_e_historial(app, client):
    """Valida clasificación MEJORO vs ESTANCADO, mapa muscular bicolor, progreso e historial."""
    with app.app_context():
        seed_database()

    # 1. Registrar y autenticar al usuario
    reg = client.post(
        "/api/auth/register",
        json={
            "nombre": "Atleta Analítico",
            "email": "analitico@fittracker.local",
            "password": "Password123",
        },
    )
    usuario_id = reg.get_json()["id"]

    with app.app_context():
        ej_repo = EjercicioRepository()
        sesion_repo = SesionRepository()
        pr_repo = PRRepository()

        # Buscar dos ejercicios predeterminados:
        # - Press de banca con barra (Primario: Pecho, Secundarios: Tríceps, Hombros) -> MEJORO
        # - Sentadilla libre (Primario: Cuádriceps, Glúteos, Secundarios: Isquiotibiales, Core) -> ESTANCADO
        banca = ej_repo.buscar_visibles_para_usuario(usuario_id, "Press de banca")[0]
        sentadilla = ej_repo.buscar_visibles_para_usuario(usuario_id, "Sentadilla libre")[0]

        ahora = datetime.now(timezone.utc)
        hace_45_dias = ahora - timedelta(days=45)
        hace_10_dias = ahora - timedelta(days=10)
        hace_2_dias = ahora - timedelta(days=2)

        # --- Ventana previa (días 31-60: hace 45 días) ---
        sesion_prev = sesion_repo.iniciar_sesion(usuario_id)
        sesion_prev.fecha_inicio = hace_45_dias
        s_banca_prev = sesion_repo.agregar_serie(
            sesion_prev.id, banca.id, peso=80.0, repeticiones=8
        )
        s_banca_prev.fecha_hora = hace_45_dias

        s_sent_prev = sesion_repo.agregar_serie(
            sesion_prev.id, sentadilla.id, peso=100.0, repeticiones=8
        )
        s_sent_prev.fecha_hora = hace_45_dias
        sesion_repo.finalizar_sesion(sesion_prev)

        # --- Ventana actual (días 0-30: sesión 1 hace 10 días y sesión 2 hace 2 días) ---
        sesion_act_1 = sesion_repo.iniciar_sesion(usuario_id)
        sesion_act_1.fecha_inicio = hace_10_dias
        s_banca_1 = sesion_repo.agregar_serie(
            sesion_act_1.id, banca.id, peso=82.5, repeticiones=8
        )
        s_banca_1.fecha_hora = hace_10_dias
        s_sent_1 = sesion_repo.agregar_serie(
            sesion_act_1.id, sentadilla.id, peso=100.0, repeticiones=8
        )
        s_sent_1.fecha_hora = hace_10_dias
        sesion_repo.finalizar_sesion(sesion_act_1)

        sesion_act_2 = sesion_repo.iniciar_sesion(usuario_id)
        sesion_act_2.fecha_inicio = hace_2_dias
        s_banca_2 = sesion_repo.agregar_serie(
            sesion_act_2.id, banca.id, peso=85.0, repeticiones=8
        )
        s_banca_2.fecha_hora = hace_2_dias
        pr_nuevo = pr_repo.registrar_pr(
            usuario_id=usuario_id,
            ejercicio_id=banca.id,
            serie_id=s_banca_2.id,
            peso=85.0,
        )
        pr_nuevo.fecha = hace_2_dias

        s_sent_2 = sesion_repo.agregar_serie(
            sesion_act_2.id, sentadilla.id, peso=95.0, repeticiones=8
        )
        s_sent_2.fecha_hora = hace_2_dias
        sesion_repo.finalizar_sesion(sesion_act_2)
        db.session.commit()

        banca_id = banca.id
        sentadilla_id = sentadilla.id

    # 2. Verificar GET /api/resumen-mensual
    res_resp = client.get("/api/resumen-mensual")
    assert res_resp.status_code == 200
    resumen = res_resp.get_json()

    assert resumen["total_sesiones"] == 2
    assert resumen["nuevos_prs"] == 1
    ids_mejorados = [e["ejercicio_id"] for e in resumen["ejercicios_mejorados"]]
    ids_estancados = [e["ejercicio_id"] for e in resumen["ejercicios_estancados"]]
    assert banca_id in ids_mejorados
    assert sentadilla_id in ids_estancados

    # 3. Verificar GET /api/mapa-muscular (bicolor: primarios vs secundarios)
    mapa_resp = client.get("/api/mapa-muscular?dias=7")
    assert mapa_resp.status_code == 200
    mapa = mapa_resp.get_json()

    # Pecho, Cuádriceps y Glúteos fueron trabajados como primarios; Tríceps, Hombros, Isquiotibiales y Core como secundarios
    assert "Pecho" in mapa["primarios"]
    assert "Cuádriceps" in mapa["primarios"]
    assert "Tríceps" in mapa["secundarios"]
    assert "Hombros" in mapa["secundarios"]

    # También soporta el query param ?desde=YYYY-MM-DD
    fecha_iso = (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d")
    mapa_desde = client.get(f"/api/mapa-muscular?desde={fecha_iso}")
    assert mapa_desde.status_code == 200
    assert "Pecho" in mapa_desde.get_json()["primarios"]

    # 4. Verificar GET /api/progreso/<ejercicio_id>
    prog_resp = client.get(f"/api/progreso/{banca_id}")
    assert prog_resp.status_code == 200
    progreso = prog_resp.get_json()
    assert progreso["ejercicio_id"] == banca_id
    assert len(progreso["puntos"]) == 3
    assert progreso["pesos_maximos"] == [80.0, 82.5, 85.0]
    assert progreso["pr_historico"] == pytest.approx(85.0)

    # 5. Verificar GET /api/historial
    hist_resp = client.get("/api/historial")
    assert hist_resp.status_code == 200
    historial = hist_resp.get_json()["sesiones"]
    assert len(historial) == 3
    assert historial[0]["total_series"] == 2

    # 6. Verificar GET /api/mapa-muscular/<nombre_grupo> (Detalle + Recomendador de Ejercicios)
    det_pecho_resp = client.get("/api/mapa-muscular/Pecho?dias=7")
    assert det_pecho_resp.status_code == 200
    det_pecho = det_pecho_resp.get_json()
    assert det_pecho["nombre"] == "Pecho"
    assert det_pecho["estado_activacion"] == "PRIMARIO"
    assert det_pecho["series_semana"]["total"] == 1
    assert det_pecho["series_semana"]["primarias"] == 1
    assert det_pecho["pr_actual"] is not None
    assert det_pecho["pr_actual"]["peso"] == pytest.approx(85.0)
    assert len(det_pecho["ejercicios_recientes"]) == 1
    assert det_pecho["ejercicios_recientes"][0]["ejercicio_id"] == banca_id

    # El recomendador debe devolver hasta 4 ejercicios primarios de Pecho, priorizando los NO entrenados esta semana
    recomendados = det_pecho["ejercicios_recomendados"]
    assert 1 <= len(recomendados) <= 4
    assert recomendados[0]["ejercicio_id"] != banca_id
    assert recomendados[0]["entrenado_esta_semana"] is False

    # Grupo inexistente retorna 404
    resp_inexistente = client.get("/api/mapa-muscular/MusculoInexistente")
    assert resp_inexistente.status_code == 404


