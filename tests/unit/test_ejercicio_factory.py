"""Pruebas unitarias aisladas para el patrón EjercicioFactory."""

import pytest
from app.patterns.factory import EjercicioFactory


def test_crear_predeterminado_exito_y_normalizacion():
    """Verifica que crear_predeterminado normalice el nombre, fuerce flags y depure grupos."""
    datos = EjercicioFactory.crear_predeterminado(
        nombre="  Press   de Banca   con Barra  ",
        grupos_primarios_ids=[1, 1],
        grupos_secundarios_ids=[1, 3, 4, 3],
    )

    assert datos == {
        "nombre": "Press de Banca con Barra",
        "es_predeterminado": True,
        "creado_por": None,
        "grupos_primarios_ids": [1],
        "grupos_secundarios_ids": [3, 4],
    }


def test_crear_personalizado_exito():
    """Verifica que crear_personalizado fuerce es_predeterminado=False y asigne creado_por."""
    datos = EjercicioFactory.crear_personalizado(
        nombre="Press Vikingo",
        usuario_id=7,
        grupos_primarios_ids=[3],
        grupos_secundarios_ids=[5],
    )

    assert datos == {
        "nombre": "Press Vikingo",
        "es_predeterminado": False,
        "creado_por": 7,
        "grupos_primarios_ids": [3],
        "grupos_secundarios_ids": [5],
    }


@pytest.mark.parametrize("nombre_invalido", ["", "   ", None, "A" * 121])
def test_factory_rechaza_nombres_invalidos(nombre_invalido):
    """Verifica que nombres vacíos, nulos o mayores a 120 caracteres lancen ValueError."""
    with pytest.raises(ValueError):
        EjercicioFactory.crear_predeterminado(
            nombre=nombre_invalido,
            grupos_primarios_ids=[1],
        )


@pytest.mark.parametrize("grupos_invalidos", [[], None, [0], [-1], ["1"], [True]])
def test_factory_exige_al_menos_un_grupo_primario_valido(grupos_invalidos):
    """Verifica que se exija al menos un ID entero positivo en grupos_primarios_ids."""
    with pytest.raises(ValueError):
        EjercicioFactory.crear_predeterminado(
            nombre="Sentadilla",
            grupos_primarios_ids=grupos_invalidos,
        )


@pytest.mark.parametrize("usuario_invalido", [None, 0, -5, "1", True])
def test_crear_personalizado_exige_usuario_id_valido(usuario_invalido):
    """Verifica que crear_personalizado valide el identificador de usuario."""
    with pytest.raises(ValueError):
        EjercicioFactory.crear_personalizado(
            nombre="Remo Unilateral",
            usuario_id=usuario_invalido,
            grupos_primarios_ids=[2],
        )

