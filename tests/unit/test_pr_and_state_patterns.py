"""Pruebas unitarias aisladas para los patrones Strategy (PR) y State (Sesión)."""

import pytest

from app.patterns.state import (
    SesionActivaState,
    SesionCerradaError,
    SesionFinalizadaState,
    SesionState,
)
from app.patterns.strategy import PesoMaximoStrategy, VolumenSerieStrategy


def test_peso_maximo_strategy_evaluacion():
    """Verifica PesoMaximoStrategy ante nuevo récord, empate, peso inferior y peso cero."""
    strategy = PesoMaximoStrategy()
    assert strategy.tipo_pr == "PESO_MAXIMO"

    # Supera el récord previo (incluyendo primer registro contra 0.0)
    assert strategy.es_nuevo_pr(nuevo_peso=80.0, repeticiones=8, valor_historico=0.0) is True
    assert strategy.es_nuevo_pr(nuevo_peso=85.0, repeticiones=5, valor_historico=80.0) is True

    # Empate o peso menor no es PR
    assert strategy.es_nuevo_pr(nuevo_peso=80.0, repeticiones=10, valor_historico=80.0) is False
    assert strategy.es_nuevo_pr(nuevo_peso=75.0, repeticiones=12, valor_historico=80.0) is False

    # Peso 0 o repeticiones 0 nunca es PR de peso máximo
    assert strategy.es_nuevo_pr(nuevo_peso=0.0, repeticiones=10, valor_historico=0.0) is False
    assert strategy.es_nuevo_pr(nuevo_peso=90.0, repeticiones=0, valor_historico=80.0) is False


def test_volumen_serie_strategy_evaluacion():
    """Verifica VolumenSerieStrategy comparando peso * repeticiones contra el máximo histórico."""
    strategy = VolumenSerieStrategy()
    assert strategy.tipo_pr == "VOLUMEN_SERIE"

    # 80 * 10 = 800 > 640
    assert strategy.es_nuevo_pr(nuevo_peso=80.0, repeticiones=10, valor_historico=640.0) is True
    # 85 * 6 = 510 < 640
    assert strategy.es_nuevo_pr(nuevo_peso=85.0, repeticiones=6, valor_historico=640.0) is False
    # Empate exacto 80 * 8 = 640 == 640
    assert strategy.es_nuevo_pr(nuevo_peso=80.0, repeticiones=8, valor_historico=640.0) is False


def test_sesion_state_activa_vs_finalizada():
    """Verifica que SesionFinalizadaState bloquee agregar series y volver a finalizar."""
    estado_activa = SesionState.obtener_estado("ACTIVA")
    assert isinstance(estado_activa, SesionActivaState)
    estado_activa.validar_registro_serie()
    estado_activa.validar_finalizacion()

    estado_finalizada = SesionState.obtener_estado("FINALIZADA")
    assert isinstance(estado_finalizada, SesionFinalizadaState)

    with pytest.raises(SesionCerradaError):
        estado_finalizada.validar_registro_serie()

    with pytest.raises(SesionCerradaError):
        estado_finalizada.validar_finalizacion()

