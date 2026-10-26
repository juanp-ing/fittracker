"""Repositorio para operaciones de persistencia de Rutina y RutinaEjercicio."""

from typing import Optional

from app import db
from app.models.rutina import Rutina, RutinaEjercicio


class RutinaRepository:
    """Gestiona las rutinas de entrenamiento garantizando el aislamiento por usuario."""

    def crear(
        self,
        usuario_id: Optional[int],
        nombre: str,
        es_favorita: bool,
        ejercicios_items: list[dict],
        es_plantilla_famosa: bool = False,
        descripcion: Optional[str] = None,
        meta_objetivo: Optional[str] = None,
        somatotipo_ideal: Optional[str] = None,
        nivel: Optional[str] = "INTERMEDIO",
        dias_semana: Optional[str] = "LUN,MIE,VIE",
    ) -> Rutina:
        """Crea una rutina junto con su lista ordenada de ejercicios configurados."""
        rutina = Rutina(
            usuario_id=usuario_id,
            nombre=nombre.strip(),
            es_favorita=es_favorita,
            es_plantilla_famosa=es_plantilla_famosa,
            descripcion=descripcion,
            meta_objetivo=meta_objetivo,
            somatotipo_ideal=somatotipo_ideal,
            nivel=nivel or "INTERMEDIO",
            dias_semana=dias_semana or "LUN,MIE,VIE",
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
        """Lista las rutinas personales pertenecientes a un usuario, priorizando las favoritas."""
        query = db.session.query(Rutina).filter(
            Rutina.usuario_id == usuario_id,
            Rutina.es_plantilla_famosa.is_(False),
        )
        if solo_favoritas:
            query = query.filter(Rutina.es_favorita.is_(True))
        return query.order_by(Rutina.es_favorita.desc(), Rutina.id.desc()).all()

    def listar_plantillas_famosas(self) -> list[Rutina]:
        """Devuelve todas las plantillas del catálogo de Rutinas Famosas."""
        return (
            db.session.query(Rutina)
            .filter(Rutina.es_plantilla_famosa.is_(True))
            .order_by(Rutina.id.asc())
            .all()
        )

    def obtener_plantilla_famosa_por_id(self, plantilla_id: int) -> Optional[Rutina]:
        """Obtiene una plantilla de rutina famosa por su ID."""
        return (
            db.session.query(Rutina)
            .filter(
                Rutina.id == plantilla_id,
                Rutina.es_plantilla_famosa.is_(True),
            )
            .first()
        )

    def clonar_plantilla_para_usuario(
        self,
        plantilla: Rutina,
        usuario_id: int,
        es_favorita: bool = True,
    ) -> Rutina:
        """Clona una plantilla de rutina famosa en la cuenta personal del usuario."""
        ejercicios_items = [
            {
                "ejercicio_id": item.ejercicio_id,
                "orden": item.orden,
                "descanso_segundos": item.descanso_segundos,
                "series_objetivo": item.series_objetivo,
            }
            for item in sorted(plantilla.ejercicios, key=lambda x: x.orden)
        ]
        return self.crear(
            usuario_id=usuario_id,
            nombre=plantilla.nombre,
            es_favorita=es_favorita,
            ejercicios_items=ejercicios_items,
            es_plantilla_famosa=False,
            descripcion=plantilla.descripcion,
            meta_objetivo=plantilla.meta_objetivo,
            somatotipo_ideal=plantilla.somatotipo_ideal,
            nivel=plantilla.nivel,
            dias_semana=plantilla.dias_semana,
        )

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
                Rutina.es_plantilla_famosa.is_(False),
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
