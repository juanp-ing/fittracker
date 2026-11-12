"""Modelos de Rutina, RutinaDia y RutinaEjercicio."""

from app import db


class Rutina(db.Model):
    """Plantilla de entrenamiento perteneciente a un usuario o al catálogo de Rutinas Famosas."""

    __tablename__ = "rutinas"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    nombre = db.Column(db.String(100), nullable=False)
    es_favorita = db.Column(db.Boolean, default=False, nullable=False)
    es_plantilla_famosa = db.Column(db.Boolean, default=False, nullable=False)
    descripcion = db.Column(db.String(300), nullable=True)
    meta_objetivo = db.Column(db.String(30), nullable=True)
    somatotipo_ideal = db.Column(db.String(20), nullable=True)
    nivel = db.Column(db.String(20), default="INTERMEDIO", nullable=True)
    dias_semana = db.Column(db.String(50), default="LUN,MIE,VIE", nullable=True)

    usuario = db.relationship("Usuario", back_populates="rutinas")
    ejercicios = db.relationship(
        "RutinaEjercicio",
        back_populates="rutina",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RutinaEjercicio.orden",
    )
    dias = db.relationship(
        "RutinaDia",
        back_populates="rutina",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    sesiones = db.relationship(
        "Sesion",
        back_populates="rutina",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Rutina id={self.id} nombre={self.nombre!r}>"


class RutinaDia(db.Model):
    """Nombre que recibe un día de entrenamiento dentro de una rutina (p. ej. LUN → «Empuje»)."""

    __tablename__ = "rutina_dias"
    __table_args__ = (
        db.UniqueConstraint("rutina_id", "dia_semana", name="uq_rutina_dias_rutina_dia"),
    )

    id = db.Column(db.Integer, primary_key=True)
    rutina_id = db.Column(
        db.Integer,
        db.ForeignKey("rutinas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dia_semana = db.Column(db.String(3), nullable=False)
    nombre = db.Column(db.String(60), nullable=False)

    rutina = db.relationship("Rutina", back_populates="dias")

    def __repr__(self) -> str:
        return f"<RutinaDia rutina_id={self.rutina_id} dia={self.dia_semana} nombre={self.nombre!r}>"


class RutinaEjercicio(db.Model):
    """Detalle de un ejercicio configurado dentro de una rutina."""

    __tablename__ = "rutina_ejercicios"

    id = db.Column(db.Integer, primary_key=True)
    rutina_id = db.Column(
        db.Integer,
        db.ForeignKey("rutinas.id", ondelete="CASCADE"),
        nullable=False,
    )
    ejercicio_id = db.Column(
        db.Integer,
        db.ForeignKey("ejercicios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    orden = db.Column(db.Integer, nullable=False)
    # Día en que toca este ejercicio (LUN…DOM). NULL = todos los días de la rutina.
    dia_semana = db.Column(db.String(3), nullable=True)
    descanso_segundos = db.Column(db.Integer, default=90, nullable=False)
    series_objetivo = db.Column(db.Integer, default=3, nullable=False)

    rutina = db.relationship("Rutina", back_populates="ejercicios")
    ejercicio = db.relationship("Ejercicio", back_populates="rutina_ejercicios")

    def __repr__(self) -> str:
        return (
            f"<RutinaEjercicio id={self.id} rutina_id={self.rutina_id} "
            f"ejercicio_id={self.ejercicio_id} orden={self.orden}>"
        )
