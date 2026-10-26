"""Patrón Factory para la creación validada de ejercicios del sistema y de usuario."""

from typing import Optional


class EjercicioFactory:
    """Fábrica de dominio para construir y validar ejercicios predeterminados y personalizados."""

    @staticmethod
    def _normalizar_nombre(nombre: str) -> str:
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("El nombre del ejercicio es obligatorio.")
        nombre_limpio = " ".join(nombre.strip().split())
        if len(nombre_limpio) > 120:
            raise ValueError("El nombre del ejercicio no puede superar los 120 caracteres.")
        return nombre_limpio

    @staticmethod
    def _validar_grupos(
        grupos_primarios_ids: list[int],
        grupos_secundarios_ids: Optional[list[int]] = None,
    ) -> tuple[list[int], list[int]]:
        if not isinstance(grupos_primarios_ids, list) or len(grupos_primarios_ids) == 0:
            raise ValueError("El ejercicio debe tener al menos un grupo muscular primario.")

        primarios_limpios: list[int] = []
        for gid in grupos_primarios_ids:
            if not isinstance(gid, int) or isinstance(gid, bool) or gid <= 0:
                raise ValueError("Los IDs de grupos musculares primarios deben ser enteros positivos.")
            if gid not in primarios_limpios:
                primarios_limpios.append(gid)

        secundarios_limpios: list[int] = []
        if grupos_secundarios_ids is not None:
            if not isinstance(grupos_secundarios_ids, list):
                raise ValueError("grupos_secundarios_ids debe ser una lista de enteros.")
            for gid in grupos_secundarios_ids:
                if not isinstance(gid, int) or isinstance(gid, bool) or gid <= 0:
                    raise ValueError(
                        "Los IDs de grupos musculares secundarios deben ser enteros positivos."
                    )
                if gid not in primarios_limpios and gid not in secundarios_limpios:
                    secundarios_limpios.append(gid)

        return primarios_limpios, secundarios_limpios

    @classmethod
    def crear_predeterminado(
        cls,
        nombre: str,
        grupos_primarios_ids: list[int],
        grupos_secundarios_ids: Optional[list[int]] = None,
    ) -> dict:
        """Construye los atributos validados para un ejercicio predeterminado del sistema."""
        nombre_limpio = cls._normalizar_nombre(nombre)
        primarios, secundarios = cls._validar_grupos(
            grupos_primarios_ids, grupos_secundarios_ids
        )
        return {
            "nombre": nombre_limpio,
            "es_predeterminado": True,
            "creado_por": None,
            "grupos_primarios_ids": primarios,
            "grupos_secundarios_ids": secundarios,
        }

    @classmethod
    def crear_personalizado(
        cls,
        nombre: str,
        usuario_id: int,
        grupos_primarios_ids: list[int],
        grupos_secundarios_ids: Optional[list[int]] = None,
    ) -> dict:
        """Construye los atributos validados para un ejercicio personalizado de un usuario."""
        if not isinstance(usuario_id, int) or isinstance(usuario_id, bool) or usuario_id <= 0:
            raise ValueError("Se requiere un usuario_id válido para crear un ejercicio personalizado.")

        nombre_limpio = cls._normalizar_nombre(nombre)
        primarios, secundarios = cls._validar_grupos(
            grupos_primarios_ids, grupos_secundarios_ids
        )
        return {
            "nombre": nombre_limpio,
            "es_predeterminado": False,
            "creado_por": usuario_id,
            "grupos_primarios_ids": primarios,
            "grupos_secundarios_ids": secundarios,
        }
