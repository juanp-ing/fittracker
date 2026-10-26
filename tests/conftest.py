"""Configuración y fixtures globales de pytest para FitTracker."""

import pytest
from app import create_app, db as _db
from app.config.settings import TestingConfig


@pytest.fixture(scope="function")
def app():
    """Crea y configura una instancia de la aplicación usando TestingConfig."""
    application = create_app(TestingConfig)
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Proporciona un cliente de pruebas HTTP para la aplicación."""
    return app.test_client()

