"""Repositorio para operaciones de persistencia de GrupoMuscular y Ejercicio."""

from typing import Optional
from sqlalchemy import or_

from app import db
from app.models.ejercicio import Ejercicio, EjercicioGrupo, GrupoMuscular


class EjercicioRepository:
    """Gestiona el catálogo de grupos musculares y ejercicios respetando la visibilidad."""

    def crear_grupo_muscular(self, nombre: str) -> GrupoMuscular:
        """Crea y persiste un nuevo grupo muscular."""
        grupo = GrupoMuscular(nombre=nombre.strip())
        db.session.add(grupo)
        db.session.commit()
        return grupo

    def listar_grupos_musculares(self) -> list[GrupoMuscular]:
        """Retorna todos los grupos musculares ordenados alfabéticamente."""
        return (
            db.session.query(GrupoMuscular)
            .order_by(GrupoMuscular.nombre.asc())
            .all()
        )

    def crear_ejercicio(
        self,
        nombre: str,
        es_predeterminado: bool,
        creado_por: Optional[int],
        grupos_primarios_ids: list[int],
        grupos_secundarios_ids: Optional[list[int]] = None,
    ) -> Ejercicio:
        """Crea un ejercicio y sus asociaciones con grupos musculares primarios y secundarios."""
        ejercicio = Ejercicio(
            nombre=nombre.strip(),
            es_predeterminado=es_predeterminado,
            creado_por=creado_por,
        )
        db.session.add(ejercicio)
        db.session.flush()

        primarios_set = set(grupos_primarios_ids)
        for grupo_id in primarios_set:
            db.session.add(
                EjercicioGrupo(
                    ejercicio_id=ejercicio.id,
                    grupo_id=grupo_id,
                    es_primario=True,
                )
            )

        secundarios_set = set(grupos_secundarios_ids or []) - primarios_set
        for grupo_id in secundarios_set:
            db.session.add(
                EjercicioGrupo(
                    ejercicio_id=ejercicio.id,
                    grupo_id=grupo_id,
                    es_primario=False,
                )
            )

        db.session.commit()
        return ejercicio

    def buscar_visibles_para_usuario(
        self,
        usuario_id: int,
        query_texto: Optional[str] = None,
    ) -> list[Ejercicio]:
        """Lista los ejercicios visibles para el usuario (sistema + propios) con filtro opcional."""
        query = db.session.query(Ejercicio).filter(
            or_(
                Ejercicio.es_predeterminado.is_(True),
                Ejercicio.creado_por == usuario_id,
            )
        )
        if query_texto and query_texto.strip():
            patron = f"%{query_texto.strip()}%"
            query = query.filter(Ejercicio.nombre.ilike(patron))

        return query.order_by(Ejercicio.nombre.asc()).all()

    def obtener_visible_por_id(
        self,
        ejercicio_id: int,
        usuario_id: int,
    ) -> Optional[Ejercicio]:
        """Obtiene un ejercicio por ID únicamente si es visible para el usuario indicado."""
        return (
            db.session.query(Ejercicio)
            .filter(
                Ejercicio.id == ejercicio_id,
                or_(
                    Ejercicio.es_predeterminado.is_(True),
                    Ejercicio.creado_por == usuario_id,
                ),
            )
            .first()
        )

