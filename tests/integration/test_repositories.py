"""Pruebas de integración para la capa de repositorios de FitTracker."""

from datetime import datetime, timedelta, timezone
import pytest

from app import db
from app.repositories import (
    EjercicioRepository,
    PRRepository,
    RutinaRepository,
    SesionRepository,
    UsuarioRepository,
)


def test_usuario_repository_crear_y_busquedas(app):
    """Verifica creación y búsqueda por ID y por email (case-insensitive) en UsuarioRepository."""
    with app.app_context():
        repo = UsuarioRepository()
        usuario = repo.crear(
            nombre="  María Gómez ",
            email="Maria.Gomez@FitTracker.Local",
            password="Password123!",
        )

        assert usuario.id is not None
        assert usuario.nombre == "María Gómez"
        assert usuario.email == "maria.gomez@fittracker.local"
        assert usuario.check_password("Password123!") is True

        por_id = repo.obtener_por_id(usuario.id)
        assert por_id is not None
        assert por_id.id == usuario.id

        por_email = repo.obtener_por_email("MARIA.GOMEZ@fittracker.local")
        assert por_email is not None
        assert por_email.id == usuario.id
        assert repo.obtener_por_email("inexistente@fittracker.local") is None


def test_ejercicio_repository_aislamiento_y_busqueda_case_insensitive(app):
    """Verifica que Usuario A vea predeterminados + propios, nunca los de Usuario B, y búsqueda ilike."""
    with app.app_context():
        user_repo = UsuarioRepository()
        ej_repo = EjercicioRepository()

        user_a = user_repo.crear("Usuario A", "a@test.com", "clave123")
        user_b = user_repo.crear("Usuario B", "b@test.com", "clave123")

        pecho = ej_repo.crear_grupo_muscular("Pecho")
        triceps = ej_repo.crear_grupo_muscular("Tríceps")
        espalda = ej_repo.crear_grupo_muscular("Espalda")

        grupos = ej_repo.listar_grupos_musculares()
        assert [g.nombre for g in grupos] == ["Espalda", "Pecho", "Tríceps"]

        ej_sistema = ej_repo.crear_ejercicio(
            nombre="Press de Banca con Barra",
            es_predeterminado=True,
            creado_por=None,
            grupos_primarios_ids=[pecho.id],
            grupos_secundarios_ids=[triceps.id],
        )
        ej_privado_a = ej_repo.crear_ejercicio(
            nombre="Press Guillotina A",
            es_predeterminado=False,
            creado_por=user_a.id,
            grupos_primarios_ids=[pecho.id],
        )
        ej_privado_b = ej_repo.crear_ejercicio(
            nombre="Remo Pendlay Especial B",
            es_predeterminado=False,
            creado_por=user_b.id,
            grupos_primarios_ids=[espalda.id],
        )

        # 1. Visibilidad para Usuario A
        visibles_a = ej_repo.buscar_visibles_para_usuario(user_a.id)
        ids_visibles_a = {e.id for e in visibles_a}
        assert ids_visibles_a == {ej_sistema.id, ej_privado_a.id}
        assert ej_privado_b.id not in ids_visibles_a

        # 2. Visibilidad por ID directo
        assert ej_repo.obtener_visible_por_id(ej_sistema.id, user_a.id) is not None
        assert ej_repo.obtener_visible_por_id(ej_privado_a.id, user_a.id) is not None
        assert ej_repo.obtener_visible_por_id(ej_privado_b.id, user_a.id) is None

        # 3. Búsqueda parcial insensible a mayúsculas/minúsculas
        busqueda_press = ej_repo.buscar_visibles_para_usuario(user_a.id, query_texto="pReSs")
        assert len(busqueda_press) == 2

        busqueda_guillotina = ej_repo.buscar_visibles_para_usuario(
            user_a.id, query_texto="guillotina"
        )
        assert [e.id for e in busqueda_guillotina] == [ej_privado_a.id]


def test_rutina_repository_crud_y_aislamiento_por_usuario(app):
    """Verifica creación, listado, actualización, alternar favorita y aislamiento en RutinaRepository."""
    with app.app_context():
        user_repo = UsuarioRepository()
        ej_repo = EjercicioRepository()
        rutina_repo = RutinaRepository()

        user_a = user_repo.crear("Usuario A", "ua@test.com", "123456")
        user_b = user_repo.crear("Usuario B", "ub@test.com", "123456")
        pierna = ej_repo.crear_grupo_muscular("Cuádriceps")
        sentadilla = ej_repo.crear_ejercicio("Sentadilla", True, None, [pierna.id])
        prensa = ej_repo.crear_ejercicio("Prensa 45", True, None, [pierna.id])

        rutina = rutina_repo.crear(
            usuario_id=user_a.id,
            nombre="Pierna Pesada",
            es_favorita=False,
            ejercicios_items=[
                {
                    "ejercicio_id": sentadilla.id,
                    "orden": 1,
                    "descanso_segundos": 120,
                    "series_objetivo": 4,
                },
                {
                    "ejercicio_id": prensa.id,
                    "orden": 2,
                    "descanso_segundos": 90,
                    "series_objetivo": 3,
                },
            ],
        )

        assert len(rutina.ejercicios) == 2
        assert rutina.ejercicios[0].descanso_segundos == 120

        # Usuario B no puede acceder a la rutina de Usuario A
        assert rutina_repo.obtener_por_id_y_usuario(rutina.id, user_b.id) is None
        assert rutina_repo.obtener_por_id_y_usuario(rutina.id, user_a.id) is not None

        # Alternar favorita y filtrar solo favoritas
        rutina_repo.alternar_favorita(rutina)
        assert rutina.es_favorita is True
        assert len(rutina_repo.listar_por_usuario(user_a.id, solo_favoritas=True)) == 1

        # Actualizar nombre y ejercicios
        rutina_repo.actualizar(
            rutina,
            nombre="Pierna Express",
            ejercicios_items=[{"ejercicio_id": sentadilla.id, "orden": 1}],
        )
        assert rutina.nombre == "Pierna Express"
        assert len(rutina.ejercicios) == 1

        # Eliminar rutina
        rutina_repo.eliminar(rutina)
        assert rutina_repo.listar_por_usuario(user_a.id) == []


def test_sesion_y_pr_repositories_ultima_serie_maximos_y_rango_fechas(app):
    """Verifica obtener_ultima_serie_ejercicio, máximos históricos y filtros por ventana de fechas."""
    with app.app_context():
        user_repo = UsuarioRepository()
        ej_repo = EjercicioRepository()
        sesion_repo = SesionRepository()
        pr_repo = PRRepository()

        user = user_repo.crear("Atleta", "atleta@test.com", "123456")
        otro_user = user_repo.crear("Otro", "otro@test.com", "123456")
        pecho = ej_repo.crear_grupo_muscular("Pecho")
        banca = ej_repo.crear_ejercicio("Press Banca", True, None, [pecho.id])

        # Sin registros previos debe retornar None y 0.0
        assert sesion_repo.obtener_ultima_serie_ejercicio(user.id, banca.id) is None
        assert pr_repo.obtener_max_peso_historico(user.id, banca.id) == 0.0
        assert pr_repo.obtener_max_volumen_historico(user.id, banca.id) == 0.0

        ahora = datetime.now(timezone.utc)
        hace_40_dias = ahora - timedelta(days=40)
        hace_5_dias = ahora - timedelta(days=5)

        # Sesión antigua (hace 40 días)
        sesion_antigua = sesion_repo.iniciar_sesion(user.id)
        s1 = sesion_repo.agregar_serie(sesion_antigua.id, banca.id, peso=70.0, repeticiones=10)
        s1.fecha_hora = hace_40_dias
        pr1 = pr_repo.registrar_pr(user.id, banca.id, s1.id, peso=70.0)
        pr1.fecha = hace_40_dias
        sesion_repo.finalizar_sesion(sesion_antigua)
        assert sesion_antigua.estado == "FINALIZADA"
        assert sesion_antigua.fecha_fin is not None

        # Sesión reciente (hace 5 días y hoy)
        sesion_reciente = sesion_repo.iniciar_sesion(user.id)
        s2 = sesion_repo.agregar_serie(sesion_reciente.id, banca.id, peso=80.0, repeticiones=8)
        s2.fecha_hora = hace_5_dias
        s3 = sesion_repo.agregar_serie(sesion_reciente.id, banca.id, peso=85.0, repeticiones=6)
        s3.fecha_hora = ahora
        pr2 = pr_repo.registrar_pr(user.id, banca.id, s3.id, peso=85.0)
        pr2.fecha = ahora

        # Serie de otro usuario con más peso (no debe contaminar al usuario principal)
        sesion_otro = sesion_repo.iniciar_sesion(otro_user.id)
        sesion_repo.agregar_serie(sesion_otro.id, banca.id, peso=150.0, repeticiones=10)
        db.session.commit()

        # 1. Última serie para precargar botones +/-
        ultima = sesion_repo.obtener_ultima_serie_ejercicio(user.id, banca.id)
        assert ultima is not None
        assert ultima.id == s3.id
        assert ultima.peso == pytest.approx(85.0)
        assert ultima.repeticiones == 6

        # 2. Máximo peso histórico (85.0 kg) y máximo volumen histórico (70 * 10 = 700.0 kg)
        assert pr_repo.obtener_max_peso_historico(user.id, banca.id) == pytest.approx(85.0)
        assert pr_repo.obtener_max_volumen_historico(user.id, banca.id) == pytest.approx(700.0)

        # 3. Filtrado por ventana de fechas (últimos 30 días)
        hace_30_dias = ahora - timedelta(days=30)
        series_mes = sesion_repo.listar_series_por_rango_fechas(user.id, hace_30_dias)
        assert [s.id for s in series_mes] == [s2.id, s3.id]

        prs_mes = pr_repo.listar_prs_usuario_rango(user.id, hace_30_dias)
        assert [p.id for p in prs_mes] == [pr2.id]

        # 4. Historial completo de series del ejercicio
        historico_banca = sesion_repo.listar_series_ejercicio_historico(user.id, banca.id)
        assert [s.id for s in historico_banca] == [s1.id, s2.id, s3.id]

        # 5. Historial de sesiones del usuario
        historial_sesiones = sesion_repo.listar_historial_usuario(user.id)
        assert len(historial_sesiones) == 2
