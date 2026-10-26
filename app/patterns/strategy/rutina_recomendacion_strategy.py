"""Patrón Strategy para recomendar y puntuar las 12 Rutinas Famosas según el PerfilUsuario."""

from typing import Optional


class RutinaRecomendacionStrategy:
    """Puntúa, filtra y ordena rutinas famosas según meta, somatotipo y sexo del atleta."""

    def puntuar_rutina(self, rutina_dict: dict, perfil: Optional[dict] = None) -> dict:
        """Calcula match_score (0-100) y recomendada_para_ti para una plantilla de rutina famosa."""
        perfil_data = perfil or {}
        meta_usuario = (perfil_data.get("meta") or "GANAR_MASA").upper()
        somatotipo_usuario = (perfil_data.get("somatotipo") or "MESOMORFO").upper()
        sexo_usuario = (perfil_data.get("sexo") or "HOMBRE").upper()

        meta_rutina = (rutina_dict.get("meta_objetivo") or "").upper()
        soma_rutina = (rutina_dict.get("somatotipo_ideal") or "TODOS").upper()
        nombre_rutina = (rutina_dict.get("nombre") or "").lower()

        score = 20

        if meta_rutina == meta_usuario:
            score += 45

        if soma_rutina == somatotipo_usuario:
            score += 35
        elif soma_rutina == "TODOS":
            score += 20

        if sexo_usuario == "MUJER" and ("glúteo" in nombre_rutina or "strong curves" in nombre_rutina):
            score = min(100, score + 10)

        score = max(0, min(100, score))
        recomendada = bool(
            meta_rutina == meta_usuario
            and (soma_rutina == somatotipo_usuario or soma_rutina == "TODOS")
        )

        resultado = dict(rutina_dict)
        resultado["match_score"] = score
        resultado["recomendada_para_ti"] = recomendada
        return resultado

    def ordenar_y_filtrar(
        self,
        rutinas: list[dict],
        perfil: Optional[dict] = None,
        filtro_meta: Optional[str] = None,
        filtro_somatotipo: Optional[str] = None,
    ) -> list[dict]:
        """Filtra opcionalmente por meta/somatotipo y ordena por mayor afinidad (match_score)."""
        meta_norm = filtro_meta.strip().upper() if filtro_meta else None
        soma_norm = filtro_somatotipo.strip().upper() if filtro_somatotipo else None

        puntuadas: list[dict] = []
        for r in rutinas:
            if meta_norm and (r.get("meta_objetivo") or "").upper() != meta_norm:
                continue
            if soma_norm:
                r_soma = (r.get("somatotipo_ideal") or "").upper()
                if r_soma != soma_norm:
                    continue
            puntuadas.append(self.puntuar_rutina(r, perfil))

        puntuadas.sort(
            key=lambda item: (
                1 if item["recomendada_para_ti"] else 0,
                item["match_score"],
                -int(item.get("id") or 0),
            ),
            reverse=True,
        )
        return puntuadas
