"""Patrón Strategy para clasificar la progresión mensual por ejercicio (días 0-30 vs 31-60)."""

from abc import ABC, abstractmethod


class ResumenClasificacionStrategy(ABC):
    """Interfaz para estrategias de clasificación de progreso en el resumen mensual."""

    @abstractmethod
    def clasificar_ejercicio(
        self,
        sesiones_actual: int,
        max_peso_actual: float,
        max_volumen_actual: float,
        sesiones_previo: int = 1,
        max_peso_previo: float = 0.0,
        max_volumen_previo: float = 0.0,
    ) -> str:
        """Retorna 'MEJORO', 'ESTANCADO' o 'SIN_DATOS' según la evolución entre ventanas."""


class ComparacionMensualStrategy(ResumenClasificacionStrategy):
    """Compara el desempeño de los últimos 30 días contra la ventana previa (días 31-60)."""

    MEJORO = "MEJORO"
    ESTANCADO = "ESTANCADO"
    SIN_DATOS = "SIN_DATOS"

    def clasificar_ejercicio(
        self,
        sesiones_actual: int,
        max_peso_actual: float,
        max_volumen_actual: float,
        sesiones_previo: int = 1,
        max_peso_previo: float = 0.0,
        max_volumen_previo: float = 0.0,
    ) -> str:
        """
        Reglas de clasificación:
        - 'MEJORO': peso máximo (o volumen máximo a igual peso) en días 0-30 > días 31-60.
        - 'ESTANCADO': entrenado en >= 2 sesiones en días 0-30 y su peso/volumen máximo <= días 31-60.
        - 'SIN_DATOS': menos de 2 sesiones en el mes actual o sin datos previos.
        """
        sin_datos_previos = (
            sesiones_previo <= 0
            or (float(max_peso_previo) <= 0.0 and float(max_volumen_previo) <= 0.0)
        )
        sin_datos_actuales = (
            sesiones_actual <= 0
            or (float(max_peso_actual) <= 0.0 and float(max_volumen_actual) <= 0.0)
        )

        if sin_datos_previos or sin_datos_actuales:
            return self.SIN_DATOS

        peso_act = float(max_peso_actual)
        peso_prev = float(max_peso_previo)
        vol_act = float(max_volumen_actual)
        vol_prev = float(max_volumen_previo)

        # Evaluar si mejoró respecto al periodo anterior (días 31-60)
        mejoro_peso = peso_act > peso_prev
        mejoro_volumen_mismo_peso = (peso_act == peso_prev) and (vol_act > vol_prev)

        if mejoro_peso or mejoro_volumen_mismo_peso:
            return self.MEJORO

        # Si no superó la marca previa, requiere >= 2 sesiones en el mes actual para ser ESTANCADO
        if sesiones_actual >= 2:
            return self.ESTANCADO

        return self.SIN_DATOS


# Alias de conveniencia
ResumenStrategy = ComparacionMensualStrategy
ResumenMensualStrategy = ComparacionMensualStrategy
