"""Configuración centralizada de FitTracker para los distintos entornos."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


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
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Configuración para despliegue en producción."""

    DEBUG = False
    # Sin valor por defecto: create_app() se niega a arrancar si falta.
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'fittracker.db'}",
    )


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

