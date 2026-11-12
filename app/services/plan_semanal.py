"""Reglas de dominio del plan semanal de una rutina: qué ejercicios tocan cada día.

Un ejercicio de rutina con ``dia_semana`` vacío se hace todos los días de la rutina; con un
código (LUN…DOM) solo ese día. Así conviven las rutinas de lista única con las de plan por días.
"""

from typing import Optional

from app.models.rutina import Rutina, RutinaEjercicio

DIAS_SEMANA = ("LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM")
DIAS_POR_DEFECTO = "LUN,MIE,VIE"


def codigos_dias(dias_semana: Optional[str]) -> list[str]:
    """«mie, LUN» → ["LUN", "MIE"] (en orden de semana; sin valor, lunes-miércoles-viernes)."""
    codigos = {c.strip().upper() for c in (dias_semana or DIAS_POR_DEFECTO).split(",") if c.strip()}
    return [d for d in DIAS_SEMANA if d in codigos]


def tiene_plan_por_dias(rutina: Rutina) -> bool:
    """Indica si algún ejercicio de la rutina está asignado a un día concreto."""
    return any(item.dia_semana for item in rutina.ejercicios)


def nombres_de_dias(rutina: Rutina) -> dict[str, str]:
    """Nombres que el usuario o la plantilla dieron a cada día («LUN» → «Empuje»)."""
    return {d.dia_semana: d.nombre for d in rutina.dias}


def ejercicios_del_dia(rutina: Rutina, codigo_dia: Optional[str]) -> list[RutinaEjercicio]:
    """Ejercicios que tocan ese día, en orden: los de todos los días más los propios del día."""
    return sorted(
        (i for i in rutina.ejercicios if not i.dia_semana or i.dia_semana == codigo_dia),
        key=lambda i: i.orden,
    )


def resolver_dia_plan(rutina: Rutina, codigo_dia: Optional[str]) -> Optional[str]:
    """Día cuyo plan se usa en ``codigo_dia``.

    Si ese día toca entrenar, es él mismo. Si es de descanso, se adelanta el siguiente día de
    entrenamiento (un domingo libre propone el plan del lunes), de modo que «entrenar de todos
    modos» nunca muestre una lista vacía.
    """
    dias = codigos_dias(rutina.dias_semana)
    if not dias:
        return None
    if codigo_dia in dias:
        return codigo_dia
    if codigo_dia not in DIAS_SEMANA:
        return dias[0]
    posicion = DIAS_SEMANA.index(codigo_dia)
    for salto in range(1, 8):
        candidato = DIAS_SEMANA[(posicion + salto) % 7]
        if candidato in dias:
            return candidato
    return None
