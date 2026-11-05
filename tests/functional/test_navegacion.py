"""Pruebas de la navegación principal: Hoy · Rutinas · Progreso · Perfil (paso 3 de la auditoría UX)."""

import json
import re

from app.seeds import seed_database


def _usuario(client, email="nav@fittracker.local", nombre="Atleta Nav"):
    resp = client.post(
        "/api/auth/register",
        json={"nombre": nombre, "email": email, "password": "Password123!"},
    )
    assert resp.status_code == 201
    client.post(
        "/api/auth/verify-code", json={"codigo": resp.get_json()["codigo_verificacion"]}
    )
    return resp.get_json()["id"]


def _rutina(client, nombre, favorita=False):
    ej = client.get("/api/ejercicios").get_json()["ejercicios"][0]["id"]
    resp = client.post(
        "/api/rutinas",
        json={
            "nombre": nombre,
            "es_favorita": favorita,
            "dias_semana": "LUN,MAR,MIE,JUE,VIE,SAB,DOM",
            "ejercicios": [
                {"ejercicio_id": ej, "orden": 1, "series_objetivo": 3, "descanso_segundos": 90}
            ],
        },
    )
    assert resp.status_code == 201
    return resp.get_json()["id"]


def _nav(html):
    m = re.search(r'<nav class="bottom-nav".*?</nav>', html, re.S)
    assert m, "Debe existir la barra de navegación inferior"
    return m.group(0)


def _item_activo(html):
    m = re.search(r'class="bottom-nav__item is-active"[^>]*>.*?<span>([^<]+)</span>', _nav(html), re.S)
    return m.group(1).strip() if m else None


# --------------------------------------------------------------------------------------
# Barra inferior y encabezado
# --------------------------------------------------------------------------------------


def test_barra_inferior_tiene_hoy_rutinas_progreso_y_perfil(app, client):
    seed_database()
    _usuario(client)

    nav = _nav(client.get("/").get_data(as_text=True))

    destinos = re.findall(r'href="([^"]+)"', nav)
    etiquetas = [e.strip() for e in re.findall(r"<span>([^<]+)</span>", nav)]
    assert destinos == ["/", "/rutinas", "/progreso", "/perfil"]
    assert etiquetas == ["Hoy", "Rutinas", "Progreso", "Perfil"]


def test_el_encabezado_ya_no_tiene_boton_de_salir(app, client):
    seed_database()
    _usuario(client)

    html = client.get("/").get_data(as_text=True)

    assert "btn-header-logout" not in html
    assert ">Salir<" not in html.split('<main class="main-content">')[0]


def test_cada_pantalla_marca_su_pestana_activa(app, client):
    seed_database()
    _usuario(client)

    assert _item_activo(client.get("/").get_data(as_text=True)) == "Hoy"
    assert _item_activo(client.get("/rutinas").get_data(as_text=True)) == "Rutinas"
    assert _item_activo(client.get("/progreso").get_data(as_text=True)) == "Progreso"
    assert _item_activo(client.get("/mapa").get_data(as_text=True)) == "Progreso"
    assert _item_activo(client.get("/resumen").get_data(as_text=True)) == "Progreso"
    assert _item_activo(client.get("/perfil").get_data(as_text=True)) == "Perfil"


def test_onboarding_no_muestra_la_barra_inferior(app, client):
    seed_database()
    _usuario(client)

    html = client.get("/onboarding").get_data(as_text=True)

    assert 'class="bottom-nav"' not in html


# --------------------------------------------------------------------------------------
# Progreso: resumen del mes + mapa muscular bajo una sola pestaña
# --------------------------------------------------------------------------------------


def test_progreso_muestra_el_resumen_y_subpestanas_hacia_el_mapa(app, client):
    seed_database()
    _usuario(client)

    resp = client.get("/progreso")

    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "resumen-mensual-contenedor" in html
    subnav = re.search(r'<nav class="sub-tabs".*?</nav>', html, re.S).group(0)
    assert 'href="/progreso"' in subnav and 'href="/mapa"' in subnav
    assert 'aria-current="page"' in re.search(r'<a[^>]*href="/progreso"[^>]*>', subnav).group(0)


def test_mapa_marca_su_subpestana(app, client):
    seed_database()
    _usuario(client)

    html = client.get("/mapa").get_data(as_text=True)

    subnav = re.search(r'<nav class="sub-tabs".*?</nav>', html, re.S).group(0)
    assert 'aria-current="page"' in re.search(r'<a[^>]*href="/mapa"[^>]*>', subnav).group(0)


# --------------------------------------------------------------------------------------
# Perfil
# --------------------------------------------------------------------------------------


def test_perfil_requiere_sesion(app, client):
    resp = client.get("/perfil")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_perfil_muestra_datos_editar_y_cerrar_sesion(app, client):
    seed_database()
    _usuario(client, email="perfil@fittracker.local", nombre="Lucía")
    client.put(
        "/api/perfil",
        json={
            "sexo": "MUJER",
            "peso_kg": 61.5,
            "porcentaje_grasa": 23,
            "meta": "DEFINIR",
            "somatotipo": "MESOMORFO",
        },
    )

    html = client.get("/perfil").get_data(as_text=True)

    assert "Lucía" in html
    assert "perfil@fittracker.local" in html
    assert "61.5 kg" in html
    assert "Definir" in html
    assert "Mesomorfo" in html
    assert 'href="/onboarding?siguiente=/perfil"' in html
    assert 'id="btn-cerrar-sesion"' in html


def test_onboarding_vuelve_al_perfil_solo_si_el_destino_es_interno(app, client):
    seed_database()
    _usuario(client)

    html_ok = client.get("/onboarding?siguiente=/perfil").get_data(as_text=True)
    html_malo = client.get("/onboarding?siguiente=https://evil.example").get_data(as_text=True)

    assert 'data-destino="/perfil"' in html_ok
    assert 'data-destino="/"' in html_malo
    # Al editar desde Perfil se puede cancelar y volver sin completar el asistente
    assert 'id="btn-cancelar-onboarding" href="/perfil"' in html_ok
    assert 'id="btn-cancelar-onboarding"' not in client.get("/onboarding").get_data(as_text=True)


# --------------------------------------------------------------------------------------
# Rutinas
# --------------------------------------------------------------------------------------


def test_entrenar_esta_rutina_abre_hoy_con_esa_rutina(app, client):
    seed_database()
    _usuario(client)
    _rutina(client, "Favorita", favorita=True)
    otra = _rutina(client, "Pierna", favorita=False)

    html_rutinas = client.get("/rutinas").get_data(as_text=True)
    assert f'href="/?rutina_id={otra}"' in html_rutinas

    html_hoy = client.get(f"/?rutina_id={otra}").get_data(as_text=True)
    agenda = json.loads(
        re.search(r'id="datos-agenda">(.*?)</script>', html_hoy, re.S).group(1)
    )
    assert agenda["rutina"]["id"] == otra


def test_rutina_id_ajena_o_invalida_no_rompe_hoy(app, client):
    seed_database()
    _usuario(client, email="a@fittracker.local")
    ajena = _rutina(client, "De A")
    client.post("/api/auth/logout")
    _usuario(client, email="b@fittracker.local")

    assert client.get(f"/?rutina_id={ajena}").status_code == 200
    assert client.get("/?rutina_id=abc").status_code == 200


def test_rutinas_sin_rutinas_propias_abre_el_catalogo(app, client):
    seed_database()
    _usuario(client)

    html = client.get("/rutinas").get_data(as_text=True)

    assert re.search(r'id="panel-mis-rutinas"[^>]*hidden', html)
    assert not re.search(r'id="panel-rutinas-famosas"[^>]*hidden', html)


def test_rutinas_con_rutinas_propias_abre_mis_rutinas_y_crear_va_en_una_hoja(app, client):
    seed_database()
    _usuario(client)
    _rutina(client, "Mía", favorita=True)

    html = client.get("/rutinas").get_data(as_text=True)

    assert not re.search(r'id="panel-mis-rutinas"[^>]*hidden', html)
    assert re.search(r'id="sheet-crear-rutina"[^>]*hidden', html)
    for dia in ("LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"):
        assert f'data-dia-rutina="{dia}"' in html


def test_rutina_recien_creada_se_resalta_y_nueva_invalida_no_rompe(app, client):
    seed_database()
    _usuario(client)
    rutina_id = _rutina(client, "Recién hecha", favorita=True)

    resp = client.get(f"/rutinas?nueva={rutina_id}")

    assert resp.status_code == 200
    tarjeta = re.search(rf'<article class="routine-card[^"]*"\s+id="rutina-{rutina_id}"', resp.get_data(as_text=True))
    assert tarjeta and "is-new" in tarjeta.group(0)
    assert client.get("/rutinas?nueva=abc").status_code == 200
