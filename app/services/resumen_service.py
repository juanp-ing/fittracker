"""Servicio de dominio para Mapa Muscular, Progreso de Ejercicios e Historial de Sesiones."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from app.repositories.ejercicio_repository import EjercicioRepository
from app.repositories.pr_repository import PRRepository
from app.repositories.sesion_repository import SesionRepository


class ResumenService:
    """Lógica de negocio para analíticas de entrenamiento, mapa muscular y gráficas de progreso."""

    def __init__(
        self,
        sesion_repo: Optional[SesionRepository] = None,
        ejercicio_repo: Optional[EjercicioRepository] = None,
        pr_repo: Optional[PRRepository] = None,
    ) -> None:
        self.sesion_repo = sesion_repo or SesionRepository()
        self.ejercicio_repo = ejercicio_repo or EjercicioRepository()
        self.pr_repo = pr_repo or PRRepository()

    def obtener_mapa_muscular(
        self,
        usuario_id: int,
        dias: int = 7,
        fecha_desde: Optional[datetime] = None,
    ) -> dict:
        """
        Calcula los grupos musculares activados en la ventana de tiempo dada,
        distinguiendo entre músculos primarios (es_primario=True) y secundarios (es_primario=False).
        """
        ahora = datetime.now(timezone.utc)
        if fecha_desde is None:
            dias_limpios = max(1, int(dias))
            fecha_inicio = ahora - timedelta(days=dias_limpios)
        else:
            fecha_inicio = fecha_desde
            dias_limpios = max(1, (ahora - fecha_inicio).days or 7)

        series = self.sesion_repo.listar_series_por_rango_fechas(
            usuario_id=usuario_id,
            fecha_desde=fecha_inicio,
        )

        conteo_grupos: dict[int, dict] = {}
        primarios_nombres: list[str] = []
        secundarios_nombres: list[str] = []

        for serie in series:
            if not serie.ejercicio:
                continue
            for eg in serie.ejercicio.ejercicio_grupos:
                grupo_id = eg.grupo_id
                nombre_grupo = eg.grupo.nombre if eg.grupo else ""
                if grupo_id not in conteo_grupos:
                    conteo_grupos[grupo_id] = {
                        "grupo_id": grupo_id,
                        "nombre": nombre_grupo,
                        "series_primarias": 0,
                        "series_secundarias": 0,
                        "es_primario": False,
                        "nivel_activacion": "SECUNDARIO",
                    }
                if eg.es_primario:
                    conteo_grupos[grupo_id]["series_primarias"] += 1
                    conteo_grupos[grupo_id]["es_primario"] = True
                    conteo_grupos[grupo_id]["nivel_activacion"] = "PRIMARIO"
                    if nombre_grupo and nombre_grupo not in primarios_nombres:
                        primarios_nombres.append(nombre_grupo)
                else:
                    conteo_grupos[grupo_id]["series_secundarias"] += 1
                    if nombre_grupo and nombre_grupo not in secundarios_nombres:
                        secundarios_nombres.append(nombre_grupo)

        # Un grupo activado como primario en algún ejercicio prioriza el color primario,
        # pero también conservamos la lista explícita de secundarios puros y totales.
        secundarios_puros = [g for g in secundarios_nombres if g not in primarios_nombres]
        grupos_lista = sorted(conteo_grupos.values(), key=lambda x: x["nombre"])

        return {
            "dias_ventana": dias_limpios,
            "fecha_desde": fecha_inicio.isoformat(),
            "primarios": sorted(primarios_nombres),
            "secundarios": sorted(secundarios_puros if secundarios_puros else secundarios_nombres),
            "secundarios_todos": sorted(secundarios_nombres),
            "grupos": grupos_lista,
        }

    def obtener_progreso_ejercicio(
        self,
        usuario_id: int,
        ejercicio_id: int,
    ) -> dict:
        """Retorna la serie temporal de fechas, pesos máximos y volúmenes para un ejercicio."""
        ejercicio = self.ejercicio_repo.obtener_visible_por_id(
            ejercicio_id=ejercicio_id,
            usuario_id=usuario_id,
        )
        if ejercicio is None:
            raise LookupError("El ejercicio solicitado no existe o no es visible.")

        series = self.sesion_repo.listar_series_ejercicio_historico(
            usuario_id=usuario_id,
            ejercicio_id=ejercicio_id,
        )

        # Agrupar por fecha (YYYY-MM-DD) conservando también el detalle por serie
        por_fecha: dict[str, dict] = {}
        for s in series:
            fecha_str = (
                s.fecha_hora.strftime("%Y-%m-%d")
                if s.fecha_hora
                else "Sin fecha"
            )
            vol = float(s.volumen)
            peso = float(s.peso)
            if fecha_str not in por_fecha:
                por_fecha[fecha_str] = {
                    "fecha": fecha_str,
                    "peso_maximo": peso,
                    "volumen_serie_max": vol,
                    "volumen_total_dia": vol,
                    "repeticiones": s.repeticiones,
                }
            else:
                registro = por_fecha[fecha_str]
                registro["volumen_total_dia"] += vol
                if peso > registro["peso_maximo"]:
                    registro["peso_maximo"] = peso
                    registro["repeticiones"] = s.repeticiones
                if vol > registro["volumen_serie_max"]:
                    registro["volumen_serie_max"] = vol

        puntos = list(por_fecha.values())
        fechas = [p["fecha"] for p in puntos]
        pesos_maximos = [p["peso_maximo"] for p in puntos]
        volumenes = [p["volumen_serie_max"] for p in puntos]
        pr_historico = self.pr_repo.obtener_max_peso_historico(
            usuario_id=usuario_id,
            ejercicio_id=ejercicio_id,
        )

        return {
            "ejercicio_id": ejercicio.id,
            "ejercicio_nombre": ejercicio.nombre,
            "fechas": fechas,
            "pesos_maximos": pesos_maximos,
            "volumenes": volumenes,
            "puntos": puntos,
            "pr_historico": pr_historico,
        }

    def obtener_historial_sesiones(
        self,
        usuario_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """Retorna el historial paginado de sesiones de entrenamiento del usuario."""
        sesiones = self.sesion_repo.listar_historial_usuario(
            usuario_id=usuario_id,
            limit=limit,
            offset=offset,
        )
        resultado: list[dict] = []
        for sesion in sesiones:
            volumen_total = sum(s.volumen for s in sesion.series)
            series_detalle = [
                {
                    "id": s.id,
                    "ejercicio_id": s.ejercicio_id,
                    "ejercicio_nombre": s.ejercicio.nombre if s.ejercicio else "",
                    "peso": s.peso,
                    "repeticiones": s.repeticiones,
                    "volumen": s.volumen,
                    "fecha_hora": s.fecha_hora.isoformat() if s.fecha_hora else None,
                }
                for s in sesion.series
            ]
            resultado.append(
                {
                    "id": sesion.id,
                    "usuario_id": sesion.usuario_id,
                    "rutina_id": sesion.rutina_id,
                    "rutina_nombre": sesion.rutina.nombre if sesion.rutina else "Entrenamiento Libre",
                    "estado": sesion.estado,
                    "fecha_inicio": sesion.fecha_inicio.isoformat() if sesion.fecha_inicio else None,
                    "fecha_fin": sesion.fecha_fin.isoformat() if sesion.fecha_fin else None,
                    "total_series": len(sesion.series),
                    "volumen_total": float(volumen_total),
                    "series": series_detalle,
                }
            )
        return resultado

