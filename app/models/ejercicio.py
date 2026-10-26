"""Modelos de GrupoMuscular, Ejercicio y asociación EjercicioGrupo."""

from app import db


class GrupoMuscular(db.Model):
    """Grupo muscular anatómico para clasificar ejercicios y colorear el mapa SVG."""

    __tablename__ = "grupos_musculares"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)

    ejercicio_grupos = db.relationship(
        "EjercicioGrupo",
        back_populates="grupo",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<GrupoMuscular id={self.id} nombre={self.nombre!r}>"


class Ejercicio(db.Model):
    """Ejercicio de gimnasio (predeterminado del sistema o personalizado por usuario)."""

    __tablename__ = "ejercicios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, index=True)
    es_predeterminado = db.Column(db.Boolean, default=False, nullable=False)
    creado_por = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=True,
    )

    creador = db.relationship("Usuario", back_populates="ejercicios_creados")
    ejercicio_grupos = db.relationship(
        "EjercicioGrupo",
        back_populates="ejercicio",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    rutina_ejercicios = db.relationship(
        "RutinaEjercicio",
        back_populates="ejercicio",
        passive_deletes=True,
    )
    series = db.relationship(
        "Serie",
        back_populates="ejercicio",
        passive_deletes=True,
    )
    prs = db.relationship(
        "PR",
        back_populates="ejercicio",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Ejercicio id={self.id} nombre={self.nombre!r}>"


class EjercicioGrupo(db.Model):
    """Asociación explícita muchos-a-muchos entre Ejercicio y GrupoMuscular."""

    __tablename__ = "ejercicio_grupos"

    ejercicio_id = db.Column(
        db.Integer,
        db.ForeignKey("ejercicios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    grupo_id = db.Column(
        db.Integer,
        db.ForeignKey("grupos_musculares.id", ondelete="CASCADE"),
        primary_key=True,
    )
    es_primario = db.Column(db.Boolean, default=True, nullable=False)

    ejercicio = db.relationship("Ejercicio", back_populates="ejercicio_grupos")
    grupo = db.relationship("GrupoMuscular", back_populates="ejercicio_grupos")

    def __repr__(self) -> str:
        return (
            f"<EjercicioGrupo ejercicio_id={self.ejercicio_id} "
            f"grupo_id={self.grupo_id} es_primario={self.es_primario}>"
        )

