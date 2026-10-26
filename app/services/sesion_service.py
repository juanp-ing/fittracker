"""Servicio de dominio para el ciclo de vida de Sesiones y registro atómico de Series."""

from typing import Optional

from app.models.sesion import Sesion
from app.patterns.observer import PRDetectionObserver, SerieSubject
from app.patterns.state import SesionState
from app.repositories.ejercicio_repository import EjercicioRepository
from app.repositories.pr_repository import PRRepository
from app.repositories.rutina_repository import RutinaRepository
from app.repositories.sesion_repository import SesionRepository
from app.services.pr_service import PRService


class SesionNoEncontradaError(LookupError):
    """Excepción lanzada cuando una sesión no existe o no pertenece al usuario."""


class SesionService:
    """Gestiona el inicio, registro de series con evaluación de PR y cierre de sesiones."""

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

    def _obtener_descanso_configurado(
        self,
        sesion: Sesion,
        ejercicio_id: int,
    ) -> int:
        if sesion.rutina_id is not None and sesion.rutina is not None:
            for item in sesion.rutina.ejercicios:
                if item.ejercicio_id == ejercicio_id:
                    return int(item.descanso_segundos)
        return 90

    def registrar_serie(
        self,
        usuario_id: int,
        sesion_id: int,
        ejercicio_id: int,
        peso: float,
        repeticiones: int,
    ) -> dict:
        """Registra una serie en la sesión activa y evalúa PRs en una única transacción."""
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

        descanso_segundos = self._obtener_descanso_configurado(sesion, ejercicio_id)
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

