"""Servicio de dominio para la gestión de rutinas personalizadas y catálogo de Rutinas Famosas."""

from typing import Optional

from app.models.rutina import Rutina
from app.patterns.strategy.rutina_recomendacion_strategy import (
    RutinaRecomendacionStrategy,
)
from app.repositories.ejercicio_repository import EjercicioRepository
from app.repositories.rutina_repository import RutinaRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.plan_semanal import (
    DIAS_SEMANA,
    codigos_dias,
    ejercicios_del_dia,
    nombres_de_dias,
    tiene_plan_por_dias,
)


class RutinaNoEncontradaError(LookupError):
    """Excepción lanzada cuando una rutina no existe o no pertenece al usuario."""


DIAS_SEMANA_VALIDOS = DIAS_SEMANA
LONGITUD_MAXIMA_NOMBRE_DIA = 60


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

    @staticmethod
    def _normalizar_dias_semana(dias_semana) -> str:
        """Devuelve los días como «LUN,MIE,VIE» (en orden de semana) o lanza ValueError."""
        if not isinstance(dias_semana, str):
            raise ValueError("Los días de la rutina deben ser un texto como «LUN,MIE,VIE».")
        codigos = {c.strip().upper() for c in dias_semana.split(",") if c.strip()}
        if not codigos:
            raise ValueError("Elige al menos un día para la rutina.")
        if not codigos <= set(DIAS_SEMANA_VALIDOS):
            raise ValueError("Días no válidos: usa LUN, MAR, MIE, JUE, VIE, SAB o DOM.")
        return ",".join(d for d in DIAS_SEMANA_VALIDOS if d in codigos)

    @staticmethod
    def _normalizar_dia_ejercicio(dia_semana) -> Optional[str]:
        """Día de un ejercicio: None (todos los días) o un código LUN…DOM; si no, ValueError."""
        if dia_semana is None or dia_semana == "":
            return None
        codigo = dia_semana.strip().upper() if isinstance(dia_semana, str) else None
        if codigo not in DIAS_SEMANA_VALIDOS:
            raise ValueError("El día de cada ejercicio debe ser LUN, MAR, MIE, JUE, VIE, SAB o DOM.")
        return codigo

    @staticmethod
    def _normalizar_nombres_dias(nombres_dias) -> dict[str, str]:
        """Nombres de los días («LUN» → «Empuje») limpios; los vacíos se descartan."""
        if nombres_dias is None:
            return {}
        if not isinstance(nombres_dias, dict):
            raise ValueError("Los nombres de los días deben ir como {\"LUN\": \"Empuje\"}.")
        limpios: dict[str, str] = {}
        for codigo, nombre in nombres_dias.items():
            clave = str(codigo).strip().upper()
            if clave not in DIAS_SEMANA_VALIDOS:
                raise ValueError("Días no válidos: usa LUN, MAR, MIE, JUE, VIE, SAB o DOM.")
            texto = " ".join(str(nombre or "").split())
            if len(texto) > LONGITUD_MAXIMA_NOMBRE_DIA:
                raise ValueError(
                    f"El nombre de un día no puede superar los {LONGITUD_MAXIMA_NOMBRE_DIA} caracteres."
                )
            if texto:
                limpios[clave] = texto
        return limpios

    def _dias_con_los_de_los_ejercicios(self, dias_semana: str, items: list[dict]) -> str:
        """Días de la rutina más los que tengan ejercicios propios (un día con plan siempre toca)."""
        codigos = set(codigos_dias(dias_semana)) | {i["dia_semana"] for i in items if i["dia_semana"]}
        return ",".join(d for d in DIAS_SEMANA_VALIDOS if d in codigos)

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
                    "dia_semana": self._normalizar_dia_ejercicio(item.get("dia_semana")),
                    "descanso_segundos": descanso_segundos,
                    "series_objetivo": series_objetivo,
                }
            )
        return items_limpios

    @staticmethod
    def _serializar_rutina(rutina: Rutina) -> dict:
        def serializar_item(re_item) -> dict:
            return {
                "id": re_item.id,
                "ejercicio_id": re_item.ejercicio_id,
                "nombre": re_item.ejercicio.nombre if re_item.ejercicio else "",
                "orden": re_item.orden,
                "dia_semana": re_item.dia_semana,
                "descanso_segundos": re_item.descanso_segundos,
                "series_objetivo": re_item.series_objetivo,
            }

        ejercicios_serializados = [
            serializar_item(i) for i in sorted(rutina.ejercicios, key=lambda x: x.orden)
        ]
        nombres = nombres_de_dias(rutina)
        # Plan de cada día de entrenamiento: sus ejercicios más los comunes a todos los días.
        dias = []
        for codigo in codigos_dias(rutina.dias_semana):
            del_dia = [serializar_item(i) for i in ejercicios_del_dia(rutina, codigo)]
            dias.append(
                {
                    "codigo": codigo,
                    "nombre": nombres.get(codigo),
                    "ejercicios": del_dia,
                    "total_series": sum(i["series_objetivo"] for i in del_dia),
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
            "por_dias": tiene_plan_por_dias(rutina),
            "nombres_dias": nombres,
            "dias": dias,
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
        nombres_dias: Optional[dict] = None,
    ) -> dict:
        """Valida y crea una nueva rutina personalizada (de lista única o con plan por días)."""
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("El nombre de la rutina es obligatorio.")

        items_validados = self._validar_items_ejercicios(usuario_id, ejercicios_items)
        dias_finales = self._dias_con_los_de_los_ejercicios(
            dias_semana or "LUN,MIE,VIE", items_validados
        )
        nombres = self._normalizar_nombres_dias(nombres_dias)
        rutina = self.rutina_repo.crear(
            usuario_id=usuario_id,
            nombre=nombre.strip(),
            es_favorita=bool(es_favorita),
            ejercicios_items=items_validados,
            dias_semana=dias_finales,
            descripcion=descripcion,
            nombres_dias={c: n for c, n in nombres.items() if c in dias_finales.split(",")},
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

        # Solo la primera rutina del usuario nace como principal: si ya tiene una, clonar otra
        # no debe competir con ella en «Hoy» (se puede marcar después desde Rutinas).
        ya_tiene_principal = bool(
            self.rutina_repo.listar_por_usuario(usuario_id=usuario_id, solo_favoritas=True)
        )
        clonada = self.rutina_repo.clonar_plantilla_para_usuario(
            plantilla=plantilla,
            usuario_id=usuario_id,
            es_favorita=not ya_tiene_principal,
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
        dias_semana: Optional[str] = None,
        nombres_dias: Optional[dict] = None,
    ) -> dict:
        """Actualiza el nombre, los días (y sus nombres) y/o los ejercicios de una rutina."""
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

        dias_validados = None
        if dias_semana is not None:
            dias_validados = self._normalizar_dias_semana(dias_semana)
        if items_validados is not None:
            # Un día con ejercicios propios siempre es día de entrenamiento.
            dias_validados = self._dias_con_los_de_los_ejercicios(
                dias_validados or rutina.dias_semana or "LUN,MIE,VIE", items_validados
            )

        nombres_validados = None
        if nombres_dias is not None:
            dias_vigentes = codigos_dias(dias_validados or rutina.dias_semana)
            nombres_validados = {
                c: n
                for c, n in self._normalizar_nombres_dias(nombres_dias).items()
                if c in dias_vigentes
            }

        actualizada = self.rutina_repo.actualizar(
            rutina=rutina,
            nombre=nombre.strip() if nombre is not None else None,
            ejercicios_items=items_validados,
            dias_semana=dias_validados,
            nombres_dias=nombres_validados,
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
