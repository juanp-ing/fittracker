"""Servicio de dominio para el catálogo, búsqueda y creación de ejercicios."""

from typing import Optional

from app.models.ejercicio import Ejercicio
from app.patterns.factory import EjercicioFactory
from app.repositories.ejercicio_repository import EjercicioRepository
from app.repositories.sesion_repository import SesionRepository
from app.repositories.usuario_repository import UsuarioRepository


class EjercicioService:
    """Lógica de negocio para gestionar grupos musculares y ejercicios."""

    def __init__(
        self,
        ejercicio_repo: Optional[EjercicioRepository] = None,
        sesion_repo: Optional[SesionRepository] = None,
        usuario_repo: Optional[UsuarioRepository] = None,
    ) -> None:
        self.ejercicio_repo = ejercicio_repo or EjercicioRepository()
        self.sesion_repo = sesion_repo or SesionRepository()
        self.usuario_repo = usuario_repo or UsuarioRepository()

    def listar_grupos_musculares(self) -> list[dict]:
        """Retorna el catálogo completo de grupos musculares serializados."""
        grupos = self.ejercicio_repo.listar_grupos_musculares()
        return [{"id": g.id, "nombre": g.nombre} for g in grupos]

    def _serializar_ejercicio(
        self,
        ejercicio: Ejercicio,
        usuario_id: Optional[int] = None,
    ) -> dict:
        grupos_musculares = []
        grupos_primarios = []
        grupos_secundarios = []

        for eg in ejercicio.ejercicio_grupos:
            nombre_grupo = eg.grupo.nombre if eg.grupo else ""
            grupos_musculares.append(
                {
                    "id": eg.grupo_id,
                    "nombre": nombre_grupo,
                    "es_primario": eg.es_primario,
                }
            )
            if eg.es_primario:
                grupos_primarios.append({"id": eg.grupo_id, "nombre": nombre_grupo})
            else:
                grupos_secundarios.append({"id": eg.grupo_id, "nombre": nombre_grupo})

        ultimo_peso = None
        ultimas_repeticiones = None
        if usuario_id is not None and usuario_id > 0:
            ultima_serie = self.sesion_repo.obtener_ultima_serie_ejercicio(
                usuario_id=usuario_id,
                ejercicio_id=ejercicio.id,
            )
            if ultima_serie is not None:
                ultimo_peso = ultima_serie.peso
                ultimas_repeticiones = ultima_serie.repeticiones

        return {
            "id": ejercicio.id,
            "nombre": ejercicio.nombre,
            "es_predeterminado": ejercicio.es_predeterminado,
            "creado_por": ejercicio.creado_por,
            "grupos_musculares": grupos_musculares,
            "grupos_primarios": grupos_primarios,
            "grupos_secundarios": grupos_secundarios,
            "grupos_primarios_ids": [g["id"] for g in grupos_primarios],
            "grupos_secundarios_ids": [g["id"] for g in grupos_secundarios],
            "ultimo_peso": ultimo_peso,
            "ultimas_repeticiones": ultimas_repeticiones,
        }

    def buscar_ejercicios_usuario(
        self,
        usuario_id: int,
        query_texto: Optional[str] = None,
    ) -> list[dict]:
        """Busca y serializa los ejercicios visibles para el usuario junto con su último registro."""
        ejercicios = self.ejercicio_repo.buscar_visibles_para_usuario(
            usuario_id=usuario_id,
            query_texto=query_texto,
        )
        return [self._serializar_ejercicio(ej, usuario_id=usuario_id) for ej in ejercicios]

    def crear_ejercicio_personalizado(
        self,
        usuario_id: int,
        nombre: str,
        grupos_primarios_ids: list[int],
        grupos_secundarios_ids: Optional[list[int]] = None,
    ) -> dict:
        """Valida mediante EjercicioFactory y persiste un ejercicio personalizado para el usuario."""
        datos = EjercicioFactory.crear_personalizado(
            nombre=nombre,
            usuario_id=usuario_id,
            grupos_primarios_ids=grupos_primarios_ids,
            grupos_secundarios_ids=grupos_secundarios_ids,
        )

        usuario = self.usuario_repo.obtener_por_id(usuario_id)
        if usuario is None:
            raise ValueError("El usuario especificado no existe.")

        ids_existentes = {g.id for g in self.ejercicio_repo.listar_grupos_musculares()}
        todos_ids = set(datos["grupos_primarios_ids"]) | set(datos["grupos_secundarios_ids"])
        if not todos_ids.issubset(ids_existentes):
            raise ValueError("Uno o más grupos musculares indicados no existen.")

        ejercicio = self.ejercicio_repo.crear_ejercicio(
            nombre=datos["nombre"],
            es_predeterminado=datos["es_predeterminado"],
            creado_por=datos["creado_por"],
            grupos_primarios_ids=datos["grupos_primarios_ids"],
            grupos_secundarios_ids=datos["grupos_secundarios_ids"],
        )
        return self._serializar_ejercicio(ejercicio, usuario_id=usuario_id)

