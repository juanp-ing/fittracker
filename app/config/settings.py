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
    # Mostrar el código de verificación en la respuesta y en pantalla anula la verificación
    # por correo: solo se permite en desarrollo y pruebas, donde no hay SMTP.
    EXPONER_CODIGO_OTP = False
    # Segundos mínimos entre dos reenvíos del código (evita usar la app para mandar spam).
    OTP_ESPERA_REENVIO_SEGUNDOS = 60


class DevelopmentConfig(Config):
    """Configuración para desarrollo local con SQLite en archivo."""

    DEBUG = True
    EXPONER_CODIGO_OTP = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'fittracker_dev.db'}",
    )


class TestingConfig(Config):
    """Configuración para pruebas automatizadas con SQLite en memoria."""

    TESTING = True
    EXPONER_CODIGO_OTP = True
    OTP_ESPERA_REENVIO_SEGUNDOS = 0
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Configuración para despliegue en producción."""

    DEBUG = False
    EXPONER_CODIGO_OTP = False
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

