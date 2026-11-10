"""La app no debe arrancar en producción con la clave de desarrollo, que es pública."""

import pytest

from app import create_app
from app.config.settings import DEV_SECRET_KEY, ProductionConfig


@pytest.mark.parametrize("clave", [None, "", DEV_SECRET_KEY])
def test_produccion_exige_secret_key_propia(monkeypatch, clave):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", clave)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(ProductionConfig)


def test_produccion_arranca_con_secret_key_propia(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "clave-de-prueba-larga-y-aleatoria")
    monkeypatch.setattr(ProductionConfig, "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

    app = create_app(ProductionConfig)

    assert app.config["SECRET_KEY"] == "clave-de-prueba-larga-y-aleatoria"


def test_produccion_por_nombre_tambien_se_valida(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", None)

    with pytest.raises(RuntimeError):
        create_app("production")
