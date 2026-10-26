"""Servicio de dominio para el ciclo de vida de Sesiones, Agenda Diaria y registro atómico de Series."""

from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

from app.models.rutina import Rutina
from app.models.sesion import Sesion
from app.patterns.observer import PRDetectionObserver, SerieSubject
from app.patterns.state import SesionState
from app.repositories.ejercicio_repository import EjercicioRepository
from app.repositories.pr_repository import PRRepository
from app.repositories.rutina_repository import RutinaRepository
from app.repositories.sesion_repository import SesionRepository
from app.services.pr_service import PRService

MESES_ES = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}

# Semana de domingo (0) a sábado (6)
DIAS_SEMANA_CONFIG = [
    ("dom", "DOM"),
    ("lun", "LUN"),
    ("mar", "MAR"),
    ("mié", "MIE"),
    ("jue", "JUE"),
    ("vie", "VIE"),
    ("sáb", "SAB"),
]


class SesionNoEncontradaError(LookupError):
    """Excepción lanzada cuando una sesión no existe o no pertenece al usuario."""


class SesionService:
    """Gestiona el inicio, agenda semanal/diaria, registro de series con PR y cierre de sesiones."""

    def __init__(
        self,
        sesion_repo: Optional[SesionRepository] = None,
        rutina_repo: Optional[RutinaRepository] = None,
        ejercicio_repo: Optional[EjercicioRepository] = None,
        pr_repo: Optional[PRRepository] = None,
        pr_service: Optional[PRService] = None,
    ) -> None:
        self.sesion_repo = sesion_repo or SesionRepository()
        self.rutina_repo = rutina_repo or RutinaRepository()
        self.ejercicio_repo = ejercicio_repo or EjercicioRepository()
        self.pr_repo = pr_repo or PRRepository()
        self.pr_service = pr_service or PRService(pr_repo=self.pr_repo)

        self.subject = SerieSubject()
        self.subject.suscribir(PRDetectionObserver(self.pr_service))

    @staticmethod
    def _serializar_sesion(sesion: Sesion) -> dict:
        volumen_total = sum(s.volumen for s in sesion.series)
        return {
            "id": sesion.id,
            "usuario_id": sesion.usuario_id,
            "rutina_id": sesion.rutina_id,
            "estado": sesion.estado,
            "fecha_inicio": sesion.fecha_inicio.isoformat() if sesion.fecha_inicio else None,
            "fecha_fin": sesion.fecha_fin.isoformat() if sesion.fecha_fin else None,
            "total_series": len(sesion.series),
            "volumen_total": float(volumen_total),
        }

    @staticmethod
    def _extraer_codigos_dias(dias_semana_str: Optional[str]) -> set[str]:
        if not dias_semana_str:
            return {"LUN", "MIE", "VIE"}
        return {
            d.strip().upper()
            for d in dias_semana_str.split(",")
            if d.strip()
        }

    def _resolver_rutina_para_usuario(
        self,
        usuario_id: int,
        codigo_dia: Optional[str] = None,
        rutina_id: Optional[int] = None,
    ) -> Optional[Rutina]:
        if rutina_id is not None:
            especifica = self.rutina_repo.obtener_por_id_y_usuario(
                rutina_id=rutina_id,
                usuario_id=usuario_id,
            )
            if especifica is not None:
                return especifica

        rutinas = self.rutina_repo.listar_por_usuario(usuario_id=usuario_id)
        if not rutinas:
            return None

        favoritas = [r for r in rutinas if r.es_favorita]
        if codigo_dia:
            for r in favoritas:
                if codigo_dia in self._extraer_codigos_dias(r.dias_semana):
                    return r
        if favoritas:
            return favoritas[0]

        if codigo_dia:
            for r in rutinas:
                if codigo_dia in self._extraer_codigos_dias(r.dias_semana):
                    return r
        return rutinas[0]

    def obtener_agenda_diaria(
        self,
        usuario_id: int,
        fecha_str: Optional[str] = None,
        rutina_id: Optional[int] = None,
    ) -> dict:
        """Devuelve la tira semanal de 7 días con puntos y el checklist de ejercicios del día."""
        hoy_utc = datetime.now(timezone.utc).date()
        if fecha_str and fecha_str.strip():
            try:
                fecha_obj = date.fromisoformat(fecha_str.strip())
            except ValueError as exc:
                raise ValueError("Formato de fecha inválido. Usa YYYY-MM-DD.") from exc
        else:
            fecha_obj = hoy_utc

        # Domingo como primer día de la tira semanal (0 = dom ... 6 = sáb)
        offset_domingo = (fecha_obj.weekday() + 1) % 7
        inicio_semana = fecha_obj - timedelta(days=offset_domingo)
        fin_semana = inicio_semana + timedelta(days=6)

        _, codigo_dia_seleccionado = DIAS_SEMANA_CONFIG[offset_domingo]
        rutina_activa = self._resolver_rutina_para_usuario(
            usuario_id=usuario_id,
            codigo_dia=codigo_dia_seleccionado,
            rutina_id=rutina_id,
        )

        dias_rutina_set = (
            self._extraer_codigos_dias(rutina_activa.dias_semana)
            if rutina_activa is not None
            else {"LUN", "MIE", "VIE"}
        )

        # Consultar todas las series registradas por el usuario en la semana de 7 días
        dt_inicio_semana = datetime.combine(inicio_semana, time.min)
        dt_fin_semana = datetime.combine(fin_semana, time.max)
        series_semana = self.sesion_repo.listar_series_por_rango_fechas(
            usuario_id=usuario_id,
            fecha_desde=dt_inicio_semana,
            fecha_hasta=dt_fin_semana,
        )

        series_por_fecha: dict[date, list] = {}
        for s in series_semana:
            if s.fecha_hora:
                f_serie = s.fecha_hora.date()
                series_por_fecha.setdefault(f_serie, []).append(s)

        dias_semana_lista: list[dict] = []
        for idx in range(7):
            dia_actual = inicio_semana + timedelta(days=idx)
            abrev, cod = DIAS_SEMANA_CONFIG[idx]
            series_del_dia = series_por_fecha.get(dia_actual, [])
            toca_entrenar = cod in dias_rutina_set

            if toca_entrenar and len(series_del_dia) > 0:
                puntos = 2
            elif len(series_del_dia) >= 4:
                puntos = 2
            elif toca_entrenar or len(series_del_dia) > 0:
                puntos = 1
            else:
                puntos = 0

            dias_semana_lista.append(
                {
                    "fecha": dia_actual.isoformat(),
                    "dia_numero": dia_actual.day,
                    "numero": dia_actual.day,
                    "abreviatura": abrev,
                    "codigo_dia": cod,
                    "seleccionado": dia_actual == fecha_obj,
                    "es_seleccionado": dia_actual == fecha_obj,
                    "es_hoy": dia_actual == hoy_utc,
                    "toca_entrenar": toca_entrenar,
                    "series_registradas": len(series_del_dia),
                    "puntos": puntos,
                }
            )

        # Calcular progreso por ejercicio en la fecha consultada
        series_fecha_seleccionada = series_por_fecha.get(fecha_obj, [])
        conteo_por_ejercicio: dict[int, int] = {}
        for s in series_fecha_seleccionada:
            conteo_por_ejercicio[s.ejercicio_id] = (
                conteo_por_ejercicio.get(s.ejercicio_id, 0) + 1
            )

        ejercicios_agenda: list[dict] = []
        if rutina_activa is not None:
            for item in sorted(rutina_activa.ejercicios, key=lambda x: x.orden):
                completadas_hoy = conteo_por_ejercicio.get(item.ejercicio_id, 0)
                objetivo = int(item.series_objetivo or 3)
                ultima_serie = self.sesion_repo.obtener_ultima_serie_ejercicio(
                    usuario_id=usuario_id,
                    ejercicio_id=item.ejercicio_id,
                )
                nombre_ej = item.ejercicio.nombre if item.ejercicio else ""
                ejercicios_agenda.append(
                    {
                        "ejercicio_id": item.ejercicio_id,
                        "ejercicio_nombre": nombre_ej,
                        "nombre": nombre_ej,
                        "orden": item.orden,
                        "series_objetivo": objetivo,
                        "descanso_segundos": int(item.descanso_segundos or 90),
                        "series_completadas_hoy": completadas_hoy,
                        "completado": completadas_hoy >= objetivo,
                        "ultimo_peso": float(ultima_serie.peso) if ultima_serie else 20.0,
                        "ultimas_repeticiones": (
                            int(ultima_serie.repeticiones) if ultima_serie else 10
                        ),
                    }
                )

        return {
            "fecha": fecha_obj.isoformat(),
            "mes_nombre": MESES_ES.get(fecha_obj.month, "octubre"),
            "anio": fecha_obj.year,
            "rutina": (
                {
                    "id": rutina_activa.id,
                    "nombre": rutina_activa.nombre,
                    "dias_semana": rutina_activa.dias_semana or "LUN,MIE,VIE",
                }
                if rutina_activa is not None
                else None
            ),
            "dias_semana": dias_semana_lista,
            "dias": dias_semana_lista,
            "ejercicios": ejercicios_agenda,
            "total_ejercicios": len(ejercicios_agenda),
            "ejercicios_completados": sum(
                1 for ej in ejercicios_agenda if ej["completado"]
            ),
        }

    def iniciar_sesion(
        self,
        usuario_id: int,
        rutina_id: Optional[int] = None,
    ) -> dict:
        """Inicia una sesión de entrenamiento libre o asociada a una rutina del usuario."""
        if rutina_id is not None:
            rutina = self.rutina_repo.obtener_por_id_y_usuario(
                rutina_id=rutina_id,
                usuario_id=usuario_id,
            )
            if rutina is None:
                raise LookupError("La rutina indicada no existe o no pertenece al usuario.")

        sesion = self.sesion_repo.iniciar_sesion(
            usuario_id=usuario_id,
            rutina_id=rutina_id,
        )
        return self._serializar_sesion(sesion)

    def _obtener_rutina_contexto_sesion(
        self,
        usuario_id: int,
        sesion: Sesion,
    ) -> Optional[Rutina]:
        if sesion.rutina_id is not None and sesion.rutina is not None:
            return sesion.rutina
        return self._resolver_rutina_para_usuario(usuario_id=usuario_id)

    def _obtener_descanso_configurado(
        self,
        rutina_ref: Optional[Rutina],
        ejercicio_id: int,
    ) -> int:
        if rutina_ref is not None:
            for item in rutina_ref.ejercicios:
                if item.ejercicio_id == ejercicio_id:
                    return int(item.descanso_segundos)
        return 90

    def _calcular_progreso_ejercicio_en_rutina(
        self,
        usuario_id: int,
        sesion: Sesion,
        rutina_ref: Optional[Rutina],
        ejercicio_id: int,
    ) -> dict:
        """Calcula series completadas, meta, si se completó ahora y cuál es el siguiente ejercicio."""
        series_sesion_ej = sum(
            1 for s in sesion.series if s.ejercicio_id == ejercicio_id
        )

        series_objetivo = 3
        orden_actual = 0
        if rutina_ref is not None:
            for item in rutina_ref.ejercicios:
                if item.ejercicio_id == ejercicio_id:
                    series_objetivo = int(item.series_objetivo or 3)
                    orden_actual = int(item.orden or 0)
                    break

        ejercicio_completado_ahora = bool(series_sesion_ej == series_objetivo)

        siguiente_ejercicio = None
        if rutina_ref is not None:
            # Contar series hechas hoy + en la sesión actual por ejercicio
            hoy_utc = datetime.now(timezone.utc).date()
            series_hoy = self.sesion_repo.listar_series_por_rango_fechas(
                usuario_id=usuario_id,
                fecha_desde=datetime.combine(hoy_utc, time.min),
                fecha_hasta=datetime.combine(hoy_utc, time.max),
            )
            conteo_total_por_ej: dict[int, int] = {}
            for s in series_hoy:
                conteo_total_por_ej[s.ejercicio_id] = (
                    conteo_total_por_ej.get(s.ejercicio_id, 0) + 1
                )
            for s in sesion.series:
                conteo_total_por_ej[s.ejercicio_id] = max(
                    conteo_total_por_ej.get(s.ejercicio_id, 0),
                    sum(1 for x in sesion.series if x.ejercicio_id == s.ejercicio_id),
                )

            items_ordenados = sorted(rutina_ref.ejercicios, key=lambda x: x.orden)
            posteriores = [x for x in items_ordenados if x.orden > orden_actual]
            anteriores = [x for x in items_ordenados if x.orden < orden_actual]

            for candidato in posteriores + anteriores:
                if candidato.ejercicio_id == ejercicio_id:
                    continue
                hechas_cand = conteo_total_por_ej.get(candidato.ejercicio_id, 0)
                meta_cand = int(candidato.series_objetivo or 3)
                if hechas_cand < meta_cand:
                    ultima_s = self.sesion_repo.obtener_ultima_serie_ejercicio(
                        usuario_id=usuario_id,
                        ejercicio_id=candidato.ejercicio_id,
                    )
                    siguiente_ejercicio = {
                        "id": candidato.ejercicio_id,
                        "ejercicio_id": candidato.ejercicio_id,
                        "nombre": (
                            candidato.ejercicio.nombre if candidato.ejercicio else ""
                        ),
                        "series_objetivo": meta_cand,
                        "descanso_segundos": int(candidato.descanso_segundos or 90),
                        "ultimo_peso": float(ultima_s.peso) if ultima_s else 20.0,
                        "ultimas_repeticiones": (
                            int(ultima_s.repeticiones) if ultima_s else 10
                        ),
                    }
                    break

        return {
            "series_completadas_ejercicio": series_sesion_ej,
            "series_objetivo_ejercicio": series_objetivo,
            "ejercicio_completado_ahora": ejercicio_completado_ahora,
            "siguiente_ejercicio": siguiente_ejercicio,
        }

    def registrar_serie(
        self,
        usuario_id: int,
        sesion_id: int,
        ejercicio_id: int,
        peso: float,
        repeticiones: int,
    ) -> dict:
        """Registra una serie en la sesión activa, evalúa PRs y calcula avance del checklist diario."""
        sesion = self.sesion_repo.obtener_por_id_y_usuario(
            sesion_id=sesion_id,
            usuario_id=usuario_id,
        )
        if sesion is None:
            raise SesionNoEncontradaError("Sesión no encontrada o acceso denegado.")

        # Validar estado de la sesión mediante el patrón State
        estado_actual = SesionState.obtener_estado(sesion.estado)
        estado_actual.validar_registro_serie()

        # Validar visibilidad del ejercicio y valores numéricos
        ejercicio = self.ejercicio_repo.obtener_visible_por_id(
            ejercicio_id=ejercicio_id,
            usuario_id=usuario_id,
        )
        if ejercicio is None:
            raise ValueError("El ejercicio especificado no existe o no es visible.")

        if not isinstance(peso, (int, float)) or isinstance(peso, bool) or float(peso) < 0:
            raise ValueError("El peso debe ser un número mayor o igual a 0.")
        if not isinstance(repeticiones, int) or isinstance(repeticiones, bool) or repeticiones <= 0:
            raise ValueError("Las repeticiones deben ser un entero mayor a 0.")

        # Consultar récords históricos antes de insertar la nueva serie
        max_peso_previo = self.pr_repo.obtener_max_peso_historico(
            usuario_id=usuario_id,
            ejercicio_id=ejercicio_id,
        )
        max_volumen_previo = self.pr_repo.obtener_max_volumen_historico(
            usuario_id=usuario_id,
            ejercicio_id=ejercicio_id,
        )

        # Insertar serie sin commit y notificar al PRDetectionObserver en la misma transacción
        serie = self.sesion_repo.agregar_serie(
            sesion_id=sesion.id,
            ejercicio_id=ejercicio_id,
            peso=float(peso),
            repeticiones=int(repeticiones),
            commit=False,
        )
        resultado_pr = self.subject.notificar(
            usuario_id=usuario_id,
            serie=serie,
            max_peso_previo=max_peso_previo,
            max_volumen_previo=max_volumen_previo,
        )
        self.sesion_repo.confirmar_transaccion()

        rutina_ref = self._obtener_rutina_contexto_sesion(usuario_id, sesion)
        descanso_segundos = self._obtener_descanso_configurado(rutina_ref, ejercicio_id)
        progreso_rutina = self._calcular_progreso_ejercicio_en_rutina(
            usuario_id=usuario_id,
            sesion=sesion,
            rutina_ref=rutina_ref,
            ejercicio_id=ejercicio_id,
        )

        serie_dict = {
            "id": serie.id,
            "sesion_id": serie.sesion_id,
            "ejercicio_id": serie.ejercicio_id,
            "peso": serie.peso,
            "repeticiones": serie.repeticiones,
            "volumen": serie.volumen,
            "fecha_hora": serie.fecha_hora.isoformat() if serie.fecha_hora else None,
        }

        return {
            **serie_dict,
            "serie": serie_dict,
            **resultado_pr,
            "descanso_segundos": descanso_segundos,
            "descanso_sugerido_segundos": descanso_segundos,
            **progreso_rutina,
        }

    def finalizar_sesion(self, usuario_id: int, sesion_id: int) -> dict:
        """Transiciona la sesión a estado FINALIZADA registrando su fecha de cierre."""
        sesion = self.sesion_repo.obtener_por_id_y_usuario(
            sesion_id=sesion_id,
            usuario_id=usuario_id,
        )
        if sesion is None:
            raise SesionNoEncontradaError("Sesión no encontrada o acceso denegado.")

        estado_actual = SesionState.obtener_estado(sesion.estado)
        estado_actual.validar_finalizacion()

        sesion_cerrada = self.sesion_repo.finalizar_sesion(sesion)
        return self._serializar_sesion(sesion_cerrada)
