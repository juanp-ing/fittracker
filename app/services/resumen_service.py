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

    def obtener_detalle_grupo_muscular(
        self,
        usuario_id: int,
        nombre_grupo: str,
        dias: int = 7,
    ) -> dict:
        """
        Retorna el detalle analítico y recomendador de ejercicios para un grupo muscular:
        - series_semana (totales, primarias y secundarias)
        - pr_actual (mayor PR en ejercicios donde el grupo es primario)
        - ejercicios_recientes (entrenados en la ventana de días)
        - ejercicios_recomendados (hasta 4 ejercicios donde el grupo es primario, priorizando no entrenados)
        """
        grupo = self.ejercicio_repo.obtener_grupo_por_nombre(nombre_grupo)
        if grupo is None:
            raise LookupError(f"El grupo muscular '{nombre_grupo}' no existe.")

        dias_limpios = max(1, int(dias))
        ahora = datetime.now(timezone.utc)
        fecha_inicio = ahora - timedelta(days=dias_limpios)

        series_ventana = self.sesion_repo.listar_series_por_rango_fechas(
            usuario_id=usuario_id,
            fecha_desde=fecha_inicio,
        )

        series_primarias = 0
        series_secundarias = 0
        recientes_por_ej: dict[int, dict] = {}

        for serie in series_ventana:
            if not serie.ejercicio:
                continue
            relacion_grupo = next(
                (eg for eg in serie.ejercicio.ejercicio_grupos if eg.grupo_id == grupo.id),
                None,
            )
            if relacion_grupo is None:
                continue

            if relacion_grupo.es_primario:
                series_primarias += 1
            else:
                series_secundarias += 1

            ej_id = serie.ejercicio_id
            peso = float(serie.peso)
            vol = float(serie.volumen)
            if ej_id not in recientes_por_ej:
                recientes_por_ej[ej_id] = {
                    "ejercicio_id": ej_id,
                    "nombre": serie.ejercicio.nombre,
                    "es_primario": bool(relacion_grupo.es_primario),
                    "series": 1,
                    "peso_maximo": peso,
                    "volumen_total": vol,
                }
            else:
                item = recientes_por_ej[ej_id]
                item["series"] += 1
                item["volumen_total"] += vol
                if peso > item["peso_maximo"]:
                    item["peso_maximo"] = peso
                if relacion_grupo.es_primario:
                    item["es_primario"] = True

        ejercicios_recientes = sorted(
            recientes_por_ej.values(),
            key=lambda x: (-int(x["es_primario"]), -x["series"], x["nombre"]),
        )

        # Ejercicios visibles donde este grupo muscular es primario
        ejercicios_primarios = self.ejercicio_repo.listar_visibles_por_grupo_primario(
            usuario_id=usuario_id,
            grupo_id=grupo.id,
        )
        ids_primarios = [e.id for e in ejercicios_primarios]

        # Mayor PR registrado por el usuario en ejercicios donde este grupo es primario
        mejor_pr = self.pr_repo.obtener_mejor_pr_por_ejercicios(
            usuario_id=usuario_id,
            ejercicios_ids=ids_primarios,
        )
        pr_actual = None
        if mejor_pr is not None:
            nombre_ej_pr = mejor_pr.ejercicio.nombre if mejor_pr.ejercicio else ""
            pr_actual = {
                "id": mejor_pr.id,
                "ejercicio_id": mejor_pr.ejercicio_id,
                "ejercicio": nombre_ej_pr,
                "ejercicio_nombre": nombre_ej_pr,
                "peso": float(mejor_pr.peso),
                "fecha": mejor_pr.fecha.isoformat() if mejor_pr.fecha else None,
            }
        else:
            # Respaldo si existen series históricas sin fila en tabla PR
            mejor_peso_hist = 0.0
            mejor_ej_obj = None
            for ej_prim in ejercicios_primarios:
                max_p = self.pr_repo.obtener_max_peso_historico(
                    usuario_id=usuario_id,
                    ejercicio_id=ej_prim.id,
                )
                if max_p > mejor_peso_hist:
                    mejor_peso_hist = max_p
                    mejor_ej_obj = ej_prim
            if mejor_ej_obj is not None and mejor_peso_hist > 0:
                pr_actual = {
                    "id": None,
                    "ejercicio_id": mejor_ej_obj.id,
                    "ejercicio": mejor_ej_obj.nombre,
                    "ejercicio_nombre": mejor_ej_obj.nombre,
                    "peso": float(mejor_peso_hist),
                    "fecha": None,
                }

        # Recomendador: hasta 4 ejercicios donde el grupo sea primario, priorizando no entrenados esta semana
        entrenados_ids = set(recientes_por_ej.keys())
        candidatos_ordenados = sorted(
            ejercicios_primarios,
            key=lambda e: (e.id in entrenados_ids, e.nombre.lower()),
        )[:4]

        ejercicios_recomendados: list[dict] = []
        for ej in candidatos_ordenados:
            ultima = self.sesion_repo.obtener_ultima_serie_ejercicio(
                usuario_id=usuario_id,
                ejercicio_id=ej.id,
            )
            ejercicios_recomendados.append(
                {
                    "id": ej.id,
                    "ejercicio_id": ej.id,
                    "nombre": ej.nombre,
                    "es_predeterminado": ej.es_predeterminado,
                    "entrenado_esta_semana": ej.id in entrenados_ids,
                    "ultimo_peso": float(ultima.peso) if ultima else None,
                    "ultimas_repeticiones": int(ultima.repeticiones) if ultima else None,
                }
            )

        total_series = series_primarias + series_secundarias
        if series_primarias > 0:
            estado_activacion = "PRIMARIO"
        elif series_secundarias > 0:
            estado_activacion = "SECUNDARIO"
        else:
            estado_activacion = "DESCANSADO"

        return {
            "grupo_id": grupo.id,
            "nombre": grupo.nombre,
            "dias_ventana": dias_limpios,
            "estado_activacion": estado_activacion,
            "series_semana": {
                "total": total_series,
                "primarias": series_primarias,
                "secundarias": series_secundarias,
            },
            "total_series_semana": total_series,
            "series_primarias": series_primarias,
            "series_secundarias": series_secundarias,
            "pr_actual": pr_actual,
            "ejercicios_recientes": ejercicios_recientes,
            "ejercicios_recomendados": ejercicios_recomendados,
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

