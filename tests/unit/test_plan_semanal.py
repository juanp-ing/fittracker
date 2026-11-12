"""Reglas del plan semanal: qué ejercicios tocan cada día y qué se propone en un día de descanso."""

from types import SimpleNamespace

import pytest

from app.services.plan_semanal import (
    codigos_dias,
    ejercicios_del_dia,
    resolver_dia_plan,
    tiene_plan_por_dias,
)


def _rutina(dias_semana, items):
    ejercicios = [
        SimpleNamespace(ejercicio_id=eid, orden=orden, dia_semana=dia)
        for orden, (eid, dia) in enumerate(items, start=1)
    ]
    return SimpleNamespace(dias_semana=dias_semana, ejercicios=ejercicios, dias=[])


def test_codigos_dias_ordena_y_limpia():
    assert codigos_dias("vie, LUN,xx") == ["LUN", "VIE"]
    assert codigos_dias(None) == ["LUN", "MIE", "VIE"]


def test_lista_unica_se_hace_todos_los_dias():
    rutina = _rutina("LUN,MIE", [(1, None), (2, None)])

    assert tiene_plan_por_dias(rutina) is False
    assert [i.ejercicio_id for i in ejercicios_del_dia(rutina, "LUN")] == [1, 2]
    assert [i.ejercicio_id for i in ejercicios_del_dia(rutina, "MIE")] == [1, 2]


def test_cada_dia_suma_sus_ejercicios_a_los_comunes():
    rutina = _rutina("LUN,MIE", [(1, "LUN"), (2, None), (3, "MIE")])

    assert tiene_plan_por_dias(rutina) is True
    assert [i.ejercicio_id for i in ejercicios_del_dia(rutina, "LUN")] == [1, 2]
    assert [i.ejercicio_id for i in ejercicios_del_dia(rutina, "MIE")] == [2, 3]


@pytest.mark.parametrize(
    "dia, esperado",
    [("LUN", "LUN"), ("MAR", "JUE"), ("JUE", "JUE"), ("VIE", "LUN"), ("DOM", "LUN")],
)
def test_en_descanso_se_adelanta_el_siguiente_dia_de_entrenamiento(dia, esperado):
    rutina = _rutina("LUN,JUE", [(1, "LUN"), (2, "JUE")])

    assert resolver_dia_plan(rutina, dia) == esperado
