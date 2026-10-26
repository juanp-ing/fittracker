"""Pruebas unitarias aisladas para la estrategia de clasificación del Resumen Mensual."""

from app.patterns.strategy import ComparacionMensualStrategy


def test_resumen_strategy_clasifica_mejoro_por_peso_y_por_volumen():
    """Verifica que clasificar_ejercicio devuelva 'MEJORO' por mayor peso o mayor volumen a igual peso."""
    strategy = ComparacionMensualStrategy()

    # 1. Mayor peso máximo en días 0-30 que en días 31-60
    assert (
        strategy.clasificar_ejercicio(
            sesiones_actual=2,
            max_peso_actual=90.0,
            max_volumen_actual=720.0,
            sesiones_previo=2,
            max_peso_previo=85.0,
            max_volumen_previo=850.0,
        )
        == "MEJORO"
    )

    # 2. Mismo peso máximo pero mayor volumen por serie en días 0-30
    assert (
        strategy.clasificar_ejercicio(
            sesiones_actual=2,
            max_peso_actual=85.0,
            max_volumen_actual=850.0,
            sesiones_previo=2,
            max_peso_previo=85.0,
            max_volumen_previo=680.0,
        )
        == "MEJORO"
    )


def test_resumen_strategy_clasifica_estancado_con_dos_o_mas_sesiones():
    """Verifica que devuelva 'ESTANCADO' cuando tiene >= 2 sesiones en el mes y no supera días 31-60."""
    strategy = ComparacionMensualStrategy()

    # Igual peso e igual volumen con 2 sesiones en el mes actual
    assert (
        strategy.clasificar_ejercicio(
            sesiones_actual=2,
            max_peso_actual=80.0,
            max_volumen_actual=640.0,
            sesiones_previo=2,
            max_peso_previo=80.0,
            max_volumen_previo=640.0,
        )
        == "ESTANCADO"
    )

    # Menor peso en 3 sesiones del mes actual
    assert (
        strategy.clasificar_ejercicio(
            sesiones_actual=3,
            max_peso_actual=75.0,
            max_volumen_actual=600.0,
            sesiones_previo=2,
            max_peso_previo=80.0,
            max_volumen_previo=640.0,
        )
        == "ESTANCADO"
    )


def test_resumen_strategy_clasifica_sin_datos():
    """Verifica que devuelva 'SIN_DATOS' cuando hay < 2 sesiones en el mes o sin datos previos."""
    strategy = ComparacionMensualStrategy()

    # Sin registros en el mes anterior (días 31-60)
    assert (
        strategy.clasificar_ejercicio(
            sesiones_actual=3,
            max_peso_actual=100.0,
            max_volumen_actual=800.0,
            sesiones_previo=0,
            max_peso_previo=0.0,
            max_volumen_previo=0.0,
        )
        == "SIN_DATOS"
    )

    # Solo 1 sesión en el mes actual sin batir la marca anterior
    assert (
        strategy.clasificar_ejercicio(
            sesiones_actual=1,
            max_peso_actual=80.0,
            max_volumen_actual=640.0,
            sesiones_previo=2,
            max_peso_previo=80.0,
            max_volumen_previo=640.0,
        )
        == "SIN_DATOS"
    )
