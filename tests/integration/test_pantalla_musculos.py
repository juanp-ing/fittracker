"""Pantalla «Músculos y récords»: cabecera, ventana de días y gráfica de una sola escala."""

import re
from pathlib import Path

from app.seeds import seed_database

ESTATICOS = Path(__file__).resolve().parents[2] / "app" / "static"


def _usuario_verificado(client, email="musculos@fittracker.local"):
    client.post(
        "/api/auth/register",
        json={"nombre": "Músculos", "email": email, "password": "Secreta123"},
    )
    codigo = client.post("/api/auth/resend-code").get_json()["codigo_verificacion"]
    client.post("/api/auth/verify-code", json={"codigo": codigo})


def _registrar_serie(client, ejercicio_id, peso):
    sesion = client.post("/api/sesiones", json={}).get_json()
    resp = client.post(
        f"/api/sesiones/{sesion['id']}/series",
        json={"ejercicio_id": ejercicio_id, "peso": peso, "repeticiones": 8},
    )
    assert resp.status_code == 201


def test_cabecera_en_lenguaje_llano(app, client):
    seed_database()
    _usuario_verificado(client)

    html = client.get("/mapa").get_data(as_text=True)

    assert "Mapa Muscular Anatómico</h1>" not in html
    assert re.search(r'<h1 class="page-title">Músculos trabajados</h1>', html)


def test_ventana_de_dias_es_un_control_segmentado_de_una_linea(app, client):
    seed_database()
    _usuario_verificado(client)

    html = client.get("/mapa").get_data(as_text=True)

    grupo = re.search(r'<div class="segmented"[^>]*>(.*?)</div>', html, re.S)
    assert grupo, "la ventana de días debe usar el control segmentado"
    botones = re.findall(r'<button[^>]*data-mapa-dias="(\d+)"[^>]*>([^<]+)</button>', grupo.group(1))
    assert [dias for dias, _ in botones] == ["7", "14", "30"]
    assert all("aria-pressed" in b for b in re.findall(r"<button[^>]*>", grupo.group(1)))


def test_selector_separa_ejercicios_entrenados_de_los_que_no(app, client):
    seed_database()
    _usuario_verificado(client)
    catalogo = client.get("/api/ejercicios").get_json()["ejercicios"]
    _registrar_serie(client, catalogo[2]["id"], 40)

    html = client.get("/mapa").get_data(as_text=True)

    selector = re.search(
        r'<select id="selector-ejercicio-progreso"[^>]*>(.*?)</select>', html, re.S
    ).group(1)
    entrenados = re.search(r'<optgroup label="Entrenados">(.*?)</optgroup>', selector, re.S)
    sin_datos = re.search(r'<optgroup label="Sin series todavía">(.*?)</optgroup>', selector, re.S)
    assert entrenados and sin_datos
    assert re.findall(r'value="(\d+)"', entrenados.group(1)) == [str(catalogo[2]["id"])]


def test_grafica_muestra_una_metrica_a_la_vez_con_fechas_legibles():
    js = (ESTATICOS / "js" / "graficas.js").read_text(encoding="utf-8")

    # Peso (~60 kg) y volumen (~600 kg) ya no comparten eje: se elige una métrica.
    assert "data-metrica-progreso" in js or "metricaProgreso" in js
    assert "Volumen Máx Serie (kg)" not in js
    # Fechas «12 oct» sin girar en lugar de ISO rotado.
    assert "formatearFechaCorta" in js
    assert "maxRotation: 0" in js


def test_font_body_no_se_usa_sin_definir():
    css = (ESTATICOS / "css" / "styles.css").read_text(encoding="utf-8")

    assert "var(--font-body)" not in css or "--font-body:" in css


def test_gris_de_texto_cumple_contraste_aa():
    css = (ESTATICOS / "css" / "styles.css").read_text(encoding="utf-8")
    color = re.search(r"--color-pencil-gray:\s*(#[0-9a-fA-F]{6})", css).group(1)

    def luminancia(hex_color):
        canales = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        lineales = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canales]
        return 0.2126 * lineales[0] + 0.7152 * lineales[1] + 0.0722 * lineales[2]

    contraste = (1.0 + 0.05) / (luminancia(color) + 0.05)
    assert contraste >= 4.5, f"{color} sobre blanco da {contraste:.2f}:1"


# --------------------------------------------------------------------------- onboarding
PLANTILLAS = ESTATICOS.parent / "templates"


def test_onboarding_habla_en_lenguaje_llano(app, client):
    seed_database()
    _usuario_verificado(client, email="onboarding.llano@fittracker.local")

    html = client.get("/onboarding").get_data(as_text=True)
    # Solo el texto visible: el JS y los data-* usan «somatotipo» como nombre del campo de la API.
    html = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    html = re.sub(r"<[^>]+>", " ", html)

    for jerga in ("somatotipo", "Somatotipo", "Biométric", "Ectomorfo", "Mesomorfo", "Endomorfo", "Sobrepeso"):
        assert jerga not in html, jerga
    assert "Complexión" in html
    for opcion in ("Delgada", "Atlética", "Robusta"):
        assert opcion in html


def test_onboarding_sin_estilos_en_linea():
    plantilla = (PLANTILLAS / "auth" / "onboarding.html").read_text(encoding="utf-8")

    assert 'style="' not in plantilla


def test_perfil_muestra_la_complexion_sin_jerga(app, client):
    seed_database()
    _usuario_verificado(client, email="perfil.llano@fittracker.local")
    client.put(
        "/api/perfil",
        json={"sexo": "MUJER", "peso_kg": 60, "meta": "DEFINIR", "somatotipo": "MESOMORFO"},
    )

    html = client.get("/perfil").get_data(as_text=True)

    assert "Mesomorfo" not in html
    assert "Atlética" in html
