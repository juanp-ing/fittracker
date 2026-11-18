"""Configuración centralizada de FitTracker para los distintos entornos."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def normalizar_url_bd(url):
    """Adapta la URL de Postgres de Neon/Vercel (postgres://) al driver psycopg 3 de SQLAlchemy."""
    if not url:
        return None
    for prefijo in ("postgres://", "postgresql://"):
        if url.startswith(prefijo):
            return "postgresql+psycopg://" + url[len(prefijo):]
    return url


# Clave solo para desarrollo y pruebas. El repositorio es público, así que esta clave no
# protege nada: producción debe recibir SECRET_KEY por variable de entorno.
DEV_SECRET_KEY = "fittracker-dev-secret-key"


class Config:
    """Configuración base compartida por todos los entornos."""

    SECRET_KEY = os.environ.get("SECRET_KEY", DEV_SECRET_KEY)
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    """Configuración para desarrollo local con SQLite en archivo."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'fittracker_dev.db'}",
    )


class TestingConfig(Config):
    """Configuración para pruebas automatizadas con SQLite en memoria."""

    TESTING = True
    # TEST_DATABASE_URL permite pasar la batería contra Postgres antes de desplegar.
    SQLALCHEMY_DATABASE_URI = normalizar_url_bd(os.environ.get("TEST_DATABASE_URL")) or "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Configuración para despliegue en producción."""

    DEBUG = False
    # Sin valor por defecto: create_app() se niega a arrancar si falta.
    SECRET_KEY = os.environ.get("SECRET_KEY")
    # En Vercel, DATABASE_URL la inyecta la integración de Neon (Postgres). En Vercel el disco
    # es efímero: SQLite solo sirve para Docker con volumen.
    SQLALCHEMY_DATABASE_URI = normalizar_url_bd(os.environ.get("DATABASE_URL")) or (
        f"sqlite:///{BASE_DIR / 'fittracker.db'}"
    )
    # Neon cierra las conexiones inactivas: comprobar antes de reutilizar una del pool.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

