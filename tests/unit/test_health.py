"""Pruebas de humo para el endpoint de diagnóstico y configuración SQLite."""

from sqlalchemy import text
from app import create_app, db


def test_health_endpoint_returns_200(client):
    """Verifica que GET /api/health responda 200 con el payload esperado."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data == {
        "status": "ok",
        "app": "FitTracker",
        "wal_enabled": True,
    }


def test_sqlite_foreign_keys_pragma_enabled(app):
    """Verifica que PRAGMA foreign_keys esté activo en cada conexión SQLite."""
    with app.app_context():
        fk_status = db.session.execute(text("PRAGMA foreign_keys;")).scalar()
        assert fk_status == 1


def test_sqlite_wal_pragma_enabled_on_file_db(tmp_path):
    """Verifica que PRAGMA journal_mode=WAL se active en bases de datos SQLite en archivo."""
    db_file = tmp_path / "test_wal.db"

    class TempFileConfig:
        TESTING = True
        SECRET_KEY = "test-wal-secret"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_file}"
        SQLALCHEMY_TRACK_MODIFICATIONS = False

    temp_app = create_app(TempFileConfig)
    with temp_app.app_context():
        journal_mode = db.session.execute(text("PRAGMA journal_mode;")).scalar()
        fk_status = db.session.execute(text("PRAGMA foreign_keys;")).scalar()
        assert journal_mode.lower() == "wal"
        assert fk_status == 1
        db.session.remove()
        db.engine.dispose()

