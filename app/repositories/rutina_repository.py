"""Repositorio para operaciones de persistencia de Rutina y RutinaEjercicio."""

from typing import Optional

from app import db
from app.models.rutina import Rutina, RutinaEjercicio


class RutinaRepository:
    """Gestiona las rutinas de entrenamiento garantizando el aislamiento por usuario."""

    def crear(
        self,
        usuario_id: int,
        nombre: str,
        es_favorita: bool,
        ejercicios_items: list[dict],
    ) -> Rutina:
        """Crea una rutina junto con su lista ordenada de ejercicios configurados."""
        rutina = Rutina(
            usuario_id=usuario_id,
            nombre=nombre.strip(),
            es_favorita=es_favorita,
        )
        db.session.add(rutina)
        db.session.flush()

        for idx, item in enumerate(ejercicios_items, start=1):
            rutina_ejercicio = RutinaEjercicio(
                rutina_id=rutina.id,
                ejercicio_id=item["ejercicio_id"],
                orden=item.get("orden", idx),
                descanso_segundos=item.get("descanso_segundos", 90),
                series_objetivo=item.get("series_objetivo", 3),
            )
            db.session.add(rutina_ejercicio)

        db.session.commit()
        return rutina

    def listar_por_usuario(
        self,
        usuario_id: int,
        solo_favoritas: bool = False,
    ) -> list[Rutina]:
        """Lista las rutinas pertenecientes a un usuario, priorizando las favoritas."""
        query = db.session.query(Rutina).filter(Rutina.usuario_id == usuario_id)
        if solo_favoritas:
            query = query.filter(Rutina.es_favorita.is_(True))
        return query.order_by(Rutina.es_favorita.desc(), Rutina.id.desc()).all()

    def obtener_por_id_y_usuario(
        self,
        rutina_id: int,
        usuario_id: int,
    ) -> Optional[Rutina]:
        """Obtiene una rutina verificando que pertenezca al usuario indicado."""
        return (
            db.session.query(Rutina)
            .filter(
                Rutina.id == rutina_id,
                Rutina.usuario_id == usuario_id,
            )
            .first()
        )

    def actualizar(
        self,
        rutina: Rutina,
        nombre: Optional[str] = None,
        ejercicios_items: Optional[list[dict]] = None,
    ) -> Rutina:
        """Actualiza el nombre y/o la configuración de ejercicios de una rutina."""
        if nombre is not None:
            rutina.nombre = nombre.strip()

        if ejercicios_items is not None:
            rutina.ejercicios.clear()
            db.session.flush()
            for idx, item in enumerate(ejercicios_items, start=1):
                rutina_ejercicio = RutinaEjercicio(
                    rutina_id=rutina.id,
                    ejercicio_id=item["ejercicio_id"],
                    orden=item.get("orden", idx),
                    descanso_segundos=item.get("descanso_segundos", 90),
                    series_objetivo=item.get("series_objetivo", 3),
                )
                db.session.add(rutina_ejercicio)

        db.session.commit()
        return rutina

    def alternar_favorita(self, rutina: Rutina) -> Rutina:
        """Invierte el estado booleano de favorita de una rutina."""
        rutina.es_favorita = not rutina.es_favorita
        db.session.commit()
        return rutina

    def eliminar(self, rutina: Rutina) -> None:
        """Elimina una rutina de la base de datos."""
        db.session.delete(rutina)
        db.session.commit()
