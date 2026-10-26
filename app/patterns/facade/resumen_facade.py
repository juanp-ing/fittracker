"""Patrón Facade para consolidar el Resumen Mensual y analíticas del Dashboard."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from app.patterns.strategy.resumen_strategy import (
    ComparacionMensualStrategy,
    ResumenClasificacionStrategy,
)
from app.repositories.ejercicio_repository import EjercicioRepository
from app.repositories.pr_repository import PRRepository
from app.repositories.sesion_repository import SesionRepository
from app.services.resumen_service import ResumenService


class ResumenFacade:
    """Fachada que orquesta repositorios, servicios y estrategias para el Resumen Mensual (RF-14)."""

    def __init__(
        self,
        sesion_repo: Optional[SesionRepository] = None,
        pr_repo: Optional[PRRepository] = None,
        ejercicio_repo: Optional[EjercicioRepository] = None,
        resumen_service: Optional[ResumenService] = None,
        strategy: Optional[ResumenClasificacionStrategy] = None,
    ) -> None:
        self.sesion_repo = sesion_repo or SesionRepository()
        self.pr_repo = pr_repo or PRRepository()
        self.ejercicio_repo = ejercicio_repo or EjercicioRepository()
        self.resumen_service = resumen_service or ResumenService(
            sesion_repo=self.sesion_repo,
            ejercicio_repo=self.ejercicio_repo,
            pr_repo=self.pr_repo,
        )
        self.strategy = strategy or ComparacionMensualStrategy()

    @staticmethod
    def _agrupar_metricas_por_ejercicio(series: list) -> dict[int, dict]:
        metricas: dict[int, dict] = {}
        for s in series:
            ej_id = s.ejercicio_id
            nombre = s.ejercicio.nombre if s.ejercicio else f"Ejercicio #{ej_id}"
            peso = float(s.peso)
            vol = float(s.volumen)
            if ej_id not in metricas:
                metricas[ej_id] = {
                    "ejercicio_id": ej_id,
                    "nombre": nombre,
                    "sesiones_ids": {s.sesion_id},
                    "max_peso": peso,
                    "max_volumen": vol,
                    "total_series": 1,
                }
            else:
                m = metricas[ej_id]
                m["sesiones_ids"].add(s.sesion_id)
                m["total_series"] += 1
                if peso > m["max_peso"]:
                    m["max_peso"] = peso
                if vol > m["max_volumen"]:
                    m["max_volumen"] = vol
        return metricas

    def obtener_resumen_mensual(self, usuario_id: int) -> dict:
        """
        Agrega PRs logrados en los últimos 30 días, ejercicios mejorados,
        ejercicios estancados y total de sesiones (comparando días 0-30 vs 31-60).
        """
        ahora = datetime.now(timezone.utc)
        hace_30_dias = ahora - timedelta(days=30)
        hace_60_dias = ahora - timedelta(days=60)

        series_actuales = self.sesion_repo.listar_series_por_rango_fechas(
            usuario_id=usuario_id,
            fecha_desde=hace_30_dias,
            fecha_hasta=ahora,
        )
        series_previas = self.sesion_repo.listar_series_por_rango_fechas(
            usuario_id=usuario_id,
            fecha_desde=hace_60_dias,
            fecha_hasta=hace_30_dias,
        )
        prs_mes = self.pr_repo.listar_prs_usuario_rango(
            usuario_id=usuario_id,
            fecha_desde=hace_30_dias,
            fecha_hasta=ahora,
        )

        metricas_act = self._agrupar_metricas_por_ejercicio(series_actuales)
        metricas_prev = self._agrupar_metricas_por_ejercicio(series_previas)

        ejercicios_mejorados: list[dict] = []
        ejercicios_estancados: list[dict] = []
        ejercicios_sin_datos: list[dict] = []
        clasificacion_por_ejercicio: dict[int, str] = {}

        for ej_id, act in metricas_act.items():
            prev = metricas_prev.get(ej_id)
            sesiones_actual = len(act["sesiones_ids"])
            sesiones_previo = len(prev["sesiones_ids"]) if prev else 0
            max_peso_previo = prev["max_peso"] if prev else 0.0
            max_volumen_previo = prev["max_volumen"] if prev else 0.0

            estado = self.strategy.clasificar_ejercicio(
                sesiones_actual=sesiones_actual,
                max_peso_actual=act["max_peso"],
                max_volumen_actual=act["max_volumen"],
                sesiones_previo=sesiones_previo,
                max_peso_previo=max_peso_previo,
                max_volumen_previo=max_volumen_previo,
            )
            clasificacion_por_ejercicio[ej_id] = estado

            item_resumen = {
                "ejercicio_id": ej_id,
                "nombre": act["nombre"],
                "estado": estado,
                "sesiones_actual": sesiones_actual,
                "max_peso_actual": act["max_peso"],
                "max_volumen_actual": act["max_volumen"],
                "max_peso_previo": max_peso_previo,
                "max_volumen_previo": max_volumen_previo,
            }
            if estado == "MEJORO":
                ejercicios_mejorados.append(item_resumen)
            elif estado == "ESTANCADO":
                ejercicios_estancados.append(item_resumen)
            else:
                ejercicios_sin_datos.append(item_resumen)

        sesiones_unicas_ids = {s.sesion_id for s in series_actuales}
        volumen_total_kg = sum(float(s.volumen) for s in series_actuales)

        prs_detalle = [
            {
                "id": pr.id,
                "ejercicio_id": pr.ejercicio_id,
                "ejercicio_nombre": pr.ejercicio.nombre if pr.ejercicio else "",
                "peso": pr.peso,
                "tipo_pr": pr.tipo_pr,
                "fecha": pr.fecha.isoformat() if pr.fecha else None,
            }
            for pr in prs_mes
        ]

        mapa_muscular = self.resumen_service.obtener_mapa_muscular(
            usuario_id=usuario_id,
            dias=30,
        )

        return {
            "ventana_dias": 30,
            "total_sesiones": len(sesiones_unicas_ids),
            "sesiones_completadas": len(sesiones_unicas_ids),
            "total_series": len(series_actuales),
            "volumen_total_kg": float(volumen_total_kg),
            "nuevos_prs": len(prs_detalle),
            "prs_logrados": prs_detalle,
            "prs_detalle": prs_detalle,
            "ejercicios_mejorados": ejercicios_mejorados,
            "ejercicios_estancados": ejercicios_estancados,
            "ejercicios_sin_datos": ejercicios_sin_datos,
            "clasificacion_ejercicios": clasificacion_por_ejercicio,
            "mapa_muscular": mapa_muscular,
        }


# Alias de conveniencia
ResumenMensualFacade = ResumenFacade

