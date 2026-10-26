"""Pruebas unitarias exhaustivas para los modelos SQLAlchemy de FitTracker."""

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app import db, load_user
from app.models import (
    PR,
    Ejercicio,
    EjercicioGrupo,
    GrupoMuscular,
    Rutina,
    RutinaEjercicio,
    Serie,
    Sesion,
    Usuario,
)


def test_all_nine_tables_and_composite_index_created(app):
    """Verifica la creación de las 9 tablas del esquema y el índice compuesto de PR."""
    with app.app_context():
        inspector = inspect(db.engine)
        tables = set(inspector.get_table_names())
        expected_tables = {
            "usuarios",
            "grupos_musculares",
            "ejercicios",
            "ejercicio_grupos",
            "rutinas",
            "rutina_ejercicios",
            "sesiones",
            "series",
            "prs",
        }
        assert expected_tables.issubset(tables)
        assert len(expected_tables) == 9

        pr_indexes = {idx["name"] for idx in inspector.get_indexes("prs")}
        assert "ix_pr_usuario_ejercicio_fecha" in pr_indexes


def test_usuario_password_hashing_and_user_loader(app):
    """Verifica el hash de contraseñas (nunca texto plano) y el user_loader de Flask-Login."""
    with app.app_context():
        user = Usuario(nombre="Juan Pérez", email="juan@fittracker.local")
        raw_password = "MiPasswordSegura123!"
        user.set_password(raw_password)

        assert user.password_hash != raw_password
        assert user.check_password(raw_password) is True
        assert user.check_password("PasswordIncorrecta") is False

        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.fecha_registro is not None
        assert user.is_authenticated is True

        loaded = load_user(str(user.id))
        assert loaded is not None
        assert loaded.email == "juan@fittracker.local"
        assert load_user("invalido") is None


def test_ejercicio_grupo_many_to_many_primario_secundario(app):
    """Verifica la relación M:N explícita EjercicioGrupo con músculo primario y secundario."""
    with app.app_context():
        pecho = GrupoMuscular(nombre="Pecho")
        triceps = GrupoMuscular(nombre="Tríceps")
        press_banca = Ejercicio(nombre="Press de Banca", es_predeterminado=True)

        db.session.add_all([pecho, triceps, press_banca])
        db.session.flush()

        asoc_primaria = EjercicioGrupo(
            ejercicio_id=press_banca.id,
            grupo_id=pecho.id,
            es_primario=True,
        )
        asoc_secundaria = EjercicioGrupo(
            ejercicio_id=press_banca.id,
            grupo_id=triceps.id,
            es_primario=False,
        )
        db.session.add_all([asoc_primaria, asoc_secundaria])
        db.session.commit()

        grupos_asociados = {
            eg.grupo.nombre: eg.es_primario for eg in press_banca.ejercicio_grupos
        }
        assert grupos_asociados == {"Pecho": True, "Tríceps": False}


def test_rutina_sesion_serie_volumen_and_pr_workflow(app):
    """Verifica la creación de Rutina, RutinaEjercicio, Sesion, Serie (.volumen) y PR."""
    with app.app_context():
        user = Usuario(nombre="Carlos", email="carlos@fittracker.local")
        user.set_password("clave123")
        sentadilla = Ejercicio(nombre="Sentadilla Libre", es_predeterminado=True)
        db.session.add_all([user, sentadilla])
        db.session.flush()

        rutina = Rutina(usuario_id=user.id, nombre="Día de Pierna", es_favorita=True)
        db.session.add(rutina)
        db.session.flush()

        rutina_ej = RutinaEjercicio(
            rutina_id=rutina.id,
            ejercicio_id=sentadilla.id,
            orden=1,
        )
        db.session.add(rutina_ej)
        db.session.flush()

        # Verificar valores por defecto en RutinaEjercicio
        assert rutina_ej.descanso_segundos == 90
        assert rutina_ej.series_objetivo == 3

        sesion = Sesion(usuario_id=user.id, rutina_id=rutina.id)
        db.session.add(sesion)
        db.session.flush()

        assert sesion.estado == "ACTIVA"
        assert sesion.fecha_inicio is not None
        assert sesion.fecha_fin is None

        serie = Serie(
            sesion_id=sesion.id,
            ejercicio_id=sentadilla.id,
            peso=100.0,
            repeticiones=8,
        )
        db.session.add(serie)
        db.session.flush()

        # Verificar propiedad calculada volumen
        assert serie.volumen == pytest.approx(800.0)

        pr = PR(
            usuario_id=user.id,
            ejercicio_id=sentadilla.id,
            peso=100.0,
            serie_id=serie.id,
        )
        db.session.add(pr)
        db.session.commit()

        assert pr.tipo_pr == "PESO_MAXIMO"
        assert pr.fecha is not None
        assert len(sesion.series) == 1
        assert len(user.prs) == 1


def test_foreign_key_integrity_and_cascade_rules(app):
    """Verifica la integridad referencial (FK inválida, RESTRICT, SET NULL y CASCADE)."""
    with app.app_context():
        # 1. Intentar insertar una Rutina con un usuario_id inexistente debe fallar
        rutina_invalida = Rutina(usuario_id=9999, nombre="Rutina Huérfana")
        db.session.add(rutina_invalida)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # 2. Preparar datos válidos para probar RESTRICT, SET NULL y CASCADE
        user = Usuario(nombre="Ana", email="ana@fittracker.local")
        user.set_password("ana123")
        ejercicio = Ejercicio(nombre="Peso Muerto", es_predeterminado=True)
        db.session.add_all([user, ejercicio])
        db.session.flush()

        rutina = Rutina(usuario_id=user.id, nombre="Tirón")
        db.session.add(rutina)
        db.session.flush()

        rutina_ej = RutinaEjercicio(
            rutina_id=rutina.id,
            ejercicio_id=ejercicio.id,
            orden=1,
        )
        sesion = Sesion(usuario_id=user.id, rutina_id=rutina.id)
        db.session.add_all([rutina_ej, sesion])
        db.session.flush()

        serie = Serie(
            sesion_id=sesion.id,
            ejercicio_id=ejercicio.id,
            peso=120.0,
            repeticiones=5,
        )
        db.session.add(serie)
        db.session.flush()

        pr = PR(
            usuario_id=user.id,
            ejercicio_id=ejercicio.id,
            peso=120.0,
            serie_id=serie.id,
        )
        db.session.add(pr)
        db.session.commit()

        # 3. Intentar eliminar un Ejercicio en uso por Serie/RutinaEjercicio (RESTRICT)
        db.session.delete(ejercicio)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # 4. Eliminar Rutina debe poner sesion.rutina_id en NULL (ON DELETE SET NULL)
        rutina_db = db.session.get(Rutina, rutina.id)
        db.session.delete(rutina_db)
        db.session.commit()

        sesion_db = db.session.get(Sesion, sesion.id)
        db.session.refresh(sesion_db)
        assert sesion_db.rutina_id is None
        assert db.session.query(RutinaEjercicio).count() == 0

        # 5. Eliminar Usuario debe eliminar en cascada Sesion, Serie y PR (ON DELETE CASCADE)
        user_db = db.session.get(Usuario, user.id)
        db.session.delete(user_db)
        db.session.commit()

        assert db.session.query(Sesion).count() == 0
        assert db.session.query(Serie).count() == 0
        assert db.session.query(PR).count() == 0

