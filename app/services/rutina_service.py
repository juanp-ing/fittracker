"""Servicio de dominio para la gestión de rutinas personalizadas y catálogo de Rutinas Famosas."""

from typing import Optional

from app.models.rutina import Rutina
from app.patterns.strategy.rutina_recomendacion_strategy import (
    RutinaRecomendacionStrategy,
)
from app.repositories.ejercicio_repository import EjercicioRepository
from app.repositories.rutina_repository import RutinaRepository
from app.repositories.usuario_repository import UsuarioRepository


class RutinaNoEncontradaError(LookupError):
    """Excepción lanzada cuando una rutina no existe o no pertenece al usuario."""


class RutinaService:
    """Lógica de negocio para crear, listar, actualizar, recomendar y clonar rutinas."""

    def __init__(
        self,
        rutina_repo: Optional[RutinaRepository] = None,
        ejercicio_repo: Optional[EjercicioRepository] = None,
        usuario_repo: Optional[UsuarioRepository] = None,
        recomendacion_strategy: Optional[RutinaRecomendacionStrategy] = None,
    ) -> None:
        self.rutina_repo = rutina_repo or RutinaRepository()
        self.ejercicio_repo = ejercicio_repo or EjercicioRepository()
        self.usuario_repo = usuario_repo or UsuarioRepository()
        self.recomendacion_strategy = (
            recomendacion_strategy or RutinaRecomendacionStrategy()
        )

    def _validar_items_ejercicios(
        self,
        usuario_id: int,
        ejercicios_items: list[dict],
    ) -> list[dict]:
        if not isinstance(ejercicios_items, list) or len(ejercicios_items) == 0:
            raise ValueError("La rutina debe incluir al menos un ejercicio.")

        items_limpios: list[dict] = []
        for idx, item in enumerate(ejercicios_items, start=1):
            if not isinstance(item, dict) or "ejercicio_id" not in item:
                raise ValueError("Cada elemento de la rutina debe contener ejercicio_id.")

            ejercicio_id = item["ejercicio_id"]
            if not isinstance(ejercicio_id, int) or ejercicio_id <= 0:
                raise ValueError("ejercicio_id debe ser un entero positivo.")

            ejercicio = self.ejercicio_repo.obtener_visible_por_id(
                ejercicio_id=ejercicio_id,
                usuario_id=usuario_id,
            )
            if ejercicio is None:
                raise ValueError(
                    f"El ejercicio con ID {ejercicio_id} no existe o no es visible para el usuario."
                )

            orden = int(item.get("orden", idx))
            descanso_segundos = int(item.get("descanso_segundos", 90))
            series_objetivo = int(item.get("series_objetivo", 3))

            if orden <= 0:
                raise ValueError("El orden del ejercicio debe ser mayor a 0.")
            if descanso_segundos <= 0:
                raise ValueError("El tiempo de descanso debe ser mayor a 0 segundos.")
            if series_objetivo <= 0:
                raise ValueError("Las series objetivo deben ser mayores a 0.")

            items_limpios.append(
                {
                    "ejercicio_id": ejercicio_id,
                    "orden": orden,
                    "descanso_segundos": descanso_segundos,
                    "series_objetivo": series_objetivo,
                }
            )
        return items_limpios

    @staticmethod
    def _serializar_rutina(rutina: Rutina) -> dict:
        ejercicios_serializados = []
        for re_item in sorted(rutina.ejercicios, key=lambda x: x.orden):
            ejercicios_serializados.append(
                {
                    "id": re_item.id,
                    "ejercicio_id": re_item.ejercicio_id,
                    "nombre": re_item.ejercicio.nombre if re_item.ejercicio else "",
                    "orden": re_item.orden,
                    "descanso_segundos": re_item.descanso_segundos,
                    "series_objetivo": re_item.series_objetivo,
                }
            )
        return {
            "id": rutina.id,
            "usuario_id": rutina.usuario_id,
            "nombre": rutina.nombre,
            "es_favorita": rutina.es_favorita,
            "es_plantilla_famosa": bool(rutina.es_plantilla_famosa),
            "descripcion": rutina.descripcion,
            "meta_objetivo": rutina.meta_objetivo,
            "somatotipo_ideal": rutina.somatotipo_ideal,
            "nivel": rutina.nivel or "INTERMEDIO",
            "dias_semana": rutina.dias_semana or "LUN,MIE,VIE",
            "ejercicios": ejercicios_serializados,
        }

    def crear_rutina(
        self,
        usuario_id: int,
        nombre: str,
        ejercicios_items: list[dict],
        es_favorita: bool = False,
        dias_semana: Optional[str] = "LUN,MIE,VIE",
        descripcion: Optional[str] = None,
    ) -> dict:
        """Valida y crea una nueva rutina personalizada para el usuario."""
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("El nombre de la rutina es obligatorio.")

        items_validados = self._validar_items_ejercicios(usuario_id, ejercicios_items)
        rutina = self.rutina_repo.crear(
            usuario_id=usuario_id,
            nombre=nombre.strip(),
            es_favorita=bool(es_favorita),
            ejercicios_items=items_validados,
            dias_semana=dias_semana or "LUN,MIE,VIE",
            descripcion=descripcion,
        )
        return self._serializar_rutina(rutina)

    def listar_rutinas_usuario(
        self,
        usuario_id: int,
        solo_favoritas: bool = False,
    ) -> list[dict]:
        """Lista todas las rutinas del usuario ordenadas con favoritas primero."""
        rutinas = self.rutina_repo.listar_por_usuario(
            usuario_id=usuario_id,
            solo_favoritas=solo_favoritas,
        )
        return [self._serializar_rutina(r) for r in rutinas]

    def listar_rutinas_famosas(
        self,
        usuario_id: int,
        meta: Optional[str] = None,
        somatotipo: Optional[str] = None,
    ) -> list[dict]:
        """Devuelve las 12 rutinas famosas puntuadas y ordenadas según el perfil del usuario."""
        perfil_obj = self.usuario_repo.obtener_perfil(usuario_id)
        perfil_dict = {
            "sexo": perfil_obj.sexo if perfil_obj else "HOMBRE",
            "meta": perfil_obj.meta if perfil_obj else "GANAR_MASA",
            "somatotipo": perfil_obj.somatotipo if perfil_obj else "MESOMORFO",
        }
        plantillas = self.rutina_repo.listar_plantillas_famosas()
        serializadas = [self._serializar_rutina(p) for p in plantillas]
        return self.recomendacion_strategy.ordenar_y_filtrar(
            rutinas=serializadas,
            perfil=perfil_dict,
            filtro_meta=meta,
            filtro_somatotipo=somatotipo,
        )

    def clonar_rutina_famosa(self, usuario_id: int, plantilla_id: int) -> dict:
        """Clona una de las 12 rutinas famosas en las rutinas personales del usuario."""
        plantilla = self.rutina_repo.obtener_plantilla_famosa_por_id(plantilla_id)
        if plantilla is None:
            raise RutinaNoEncontradaError("Plantilla de rutina famosa no encontrada.")

        clonada = self.rutina_repo.clonar_plantilla_para_usuario(
            plantilla=plantilla,
            usuario_id=usuario_id,
            es_favorita=True,
        )
        return self._serializar_rutina(clonada)

    def obtener_rutina(self, usuario_id: int, rutina_id: int) -> dict:
        """Obtiene el detalle de una rutina verificando la propiedad del usuario."""
        rutina = self.rutina_repo.obtener_por_id_y_usuario(
            rutina_id=rutina_id,
            usuario_id=usuario_id,
        )
        if rutina is None:
            raise RutinaNoEncontradaError("Rutina no encontrada o acceso denegado.")
        return self._serializar_rutina(rutina)

    def actualizar_rutina(
        self,
        usuario_id: int,
        rutina_id: int,
        nombre: Optional[str] = None,
        ejercicios_items: Optional[list[dict]] = None,
    ) -> dict:
        """Actualiza el nombre y/o los ejercicios de una rutina del usuario."""
        rutina = self.rutina_repo.obtener_por_id_y_usuario(
            rutina_id=rutina_id,
            usuario_id=usuario_id,
        )
        if rutina is None:
            raise RutinaNoEncontradaError("Rutina no encontrada o acceso denegado.")

        if nombre is not None and (not isinstance(nombre, str) or not nombre.strip()):
            raise ValueError("El nombre de la rutina no puede estar vacío.")

        items_validados = None
        if ejercicios_items is not None:
            items_validados = self._validar_items_ejercicios(usuario_id, ejercicios_items)

        actualizada = self.rutina_repo.actualizar(
            rutina=rutina,
            nombre=nombre.strip() if nombre is not None else None,
            ejercicios_items=items_validados,
        )
        return self._serializar_rutina(actualizada)

    def alternar_favorita(self, usuario_id: int, rutina_id: int) -> dict:
        """Alterna el estado de favorita de una rutina del usuario."""
        rutina = self.rutina_repo.obtener_por_id_y_usuario(
            rutina_id=rutina_id,
            usuario_id=usuario_id,
        )
        if rutina is None:
            raise RutinaNoEncontradaError("Rutina no encontrada o acceso denegado.")

        actualizada = self.rutina_repo.alternar_favorita(rutina)
        return self._serializar_rutina(actualizada)

    def eliminar_rutina(self, usuario_id: int, rutina_id: int) -> None:
        """Elimina una rutina verificando que pertenezca al usuario."""
        rutina = self.rutina_repo.obtener_por_id_y_usuario(
            rutina_id=rutina_id,
            usuario_id=usuario_id,
        )
        if rutina is None:
            raise RutinaNoEncontradaError("Rutina no encontrada o acceso denegado.")

        self.rutina_repo.eliminar(rutina)
