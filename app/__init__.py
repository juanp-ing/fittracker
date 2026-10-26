"""Application Factory e inicialización de extensiones de FitTracker."""

import sqlite3
from flask import Flask, jsonify
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.config.settings import (
    DevelopmentConfig,
    ProductionConfig,
    TestingConfig,
    config_by_name,
)

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Activa el modo WAL y la integridad referencial en cada conexión SQLite."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


@login_manager.user_loader
def load_user(user_id: str):
    """Carga un usuario por su ID primario para la sesión de Flask-Login."""
    from app.models.usuario import Usuario

    try:
        return db.session.get(Usuario, int(user_id))
    except (TypeError, ValueError):
        return None


def _resolve_config(config_name):
    """Resuelve el objeto de configuración a partir de su nombre o clase."""
    if isinstance(config_name, str):
        class_map = {
            "developmentconfig": DevelopmentConfig,
            "testingconfig": TestingConfig,
            "productionconfig": ProductionConfig,
        }
        key = config_name.lower()
        return config_by_name.get(key) or class_map.get(key, DevelopmentConfig)
    return config_name


def create_app(config_name="default") -> Flask:
    """Crea y configura una instancia de la aplicación Flask FitTracker."""
    app = Flask(__name__)
    config_obj = _resolve_config(config_name)
    app.config.from_object(config_obj)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Importar modelos para que SQLAlchemy y Flask-Migrate los registren
    from app import models  # noqa: F401

    @app.route("/api/health", methods=["GET"])
    def health_check():
        return (
            jsonify(
                {
                    "status": "ok",
                    "app": "FitTracker",
                    "wal_enabled": True,
                }
            ),
            200,
        )

    return app
