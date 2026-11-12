"""Pruebas de los controles que prometían algo que no hacían (auditoría de interfaz).

Cubre: editar una rutina desde la pantalla (incluidos los días), el arrastre del asa de las
hojas inferiores, el botón secundario del modal «Ejercicio terminado», la repetición al
mantener pulsado ± y las insignias/filas que parecían pulsables.
"""

from pathlib import Path

from app.seeds import seed_database

ESTATICOS = Path(__file__).resolve().parents[2] / "app" / "static"


def _usuario(client, email="controles@fittracker.local"):
    resp = client.post(
        "/api/auth/register",
        json={"nombre": "Atleta Controles", "email": email, "password": "Password123!"},
    )
    assert resp.status_code == 201
    client.post(
        "/api/auth/verify-code", json={"codigo": resp.get_json()["codigo_verificacion"]}
    )


def _ejercicios(client, cuantos=2):
    return [e["id"] for e in client.get("/api/ejercicios?q=press").get_json()["ejercicios"][:cuantos]]


def _rutina(client, ejercicio_ids, dias="LUN,MIE,VIE"):
    resp = client.post(
        "/api/rutinas",
        json={
            "nombre": "Empuje",
            "es_favorita": True,
            "dias_semana": dias,
            "ejercicios": [
                {"ejercicio_id": ej, "orden": i + 1, "series_objetivo": 3, "descanso_segundos": 90}
                for i, ej in enumerate(ejercicio_ids)
            ],
        },
    )
    assert resp.status_code == 201
    return resp.get_json()


# ---------------------------------------------------------------- editar rutina
def test_put_rutina_actualiza_dias_nombre_y_ejercicios(app, client):
    with app.app_context():
        seed_database()
    _usuario(client)
    ej_a, ej_b = _ejercicios(client)
    rutina = _rutina(client, [ej_a])

    resp = client.put(
        f"/api/rutinas/{rutina['id']}",
        json={
            "nombre": "Empuje pesado",
            "dias_semana": "mar, JUE",
            "ejercicios": [
                {"ejercicio_id": ej_b, "orden": 1, "series_objetivo": 5, "descanso_segundos": 120},
                {"ejercicio_id": ej_a, "orden": 2, "series_objetivo": 2, "descanso_segundos": 60},
            ],
        },
    )
    assert resp.status_code == 200
    datos = client.get(f"/api/rutinas/{rutina['id']}").get_json()
    assert datos["nombre"] == "Empuje pesado"
    assert datos["dias_semana"] == "MAR,JUE"
    assert [(e["ejercicio_id"], e["series_objetivo"]) for e in datos["ejercicios"]] == [(ej_b, 5), (ej_a, 2)]
    assert datos["es_favorita"] is True  # editar no cambia si es principal


def test_put_rutina_sin_dias_conserva_los_que_tenia(app, client):
    with app.app_context():
        seed_database()
    _usuario(client)
    rutina = _rutina(client, _ejercicios(client, 1), dias="SAB,DOM")

    resp = client.put(f"/api/rutinas/{rutina['id']}", json={"nombre": "Finde"})
    assert resp.status_code == 200
    assert resp.get_json()["dias_semana"] == "SAB,DOM"


def test_put_rutina_rechaza_dias_invalidos_o_vacios(app, client):
    with app.app_context():
        seed_database()
    _usuario(client)
    rutina = _rutina(client, _ejercicios(client, 1))

    for dias in ("", "LUN,FUNDAY", 7):
        resp = client.put(f"/api/rutinas/{rutina['id']}", json={"dias_semana": dias})
        assert resp.status_code == 400, dias
    assert client.get(f"/api/rutinas/{rutina['id']}").get_json()["dias_semana"] == "LUN,MIE,VIE"


def test_pantalla_rutinas_ofrece_editar_cada_rutina(app, client):
    with app.app_context():
        seed_database()
    _usuario(client)
    rutina = _rutina(client, _ejercicios(client, 1))

    html = client.get("/rutinas").get_data(as_text=True)
    assert f'data-editar-rutina="{rutina["id"]}"' in html
    # El script de la página guarda los cambios con PUT sobre la rutina editada.
    assert "method: editandoId ? 'PUT' : 'POST'" in html


# ---------------------------------------------------------------- asa de las hojas
def test_el_asa_de_las_hojas_tiene_gesto_de_arrastre(app, client):
    with app.app_context():
        seed_database()
    _usuario(client)

    for ruta in ("/", "/rutinas", "/mapa"):
        html = client.get(ruta, follow_redirects=True).get_data(as_text=True)
        assert "sheet-handle" in html, ruta
        assert "js/hojas.js" in html, ruta

    js = (ESTATICOS / "js" / "hojas.js").read_text(encoding="utf-8")
    assert "pointerdown" in js and ".sheet-handle" in js


# ---------------------------------------------------------------- modo foco
def test_modal_ejercicio_terminado_no_promete_un_descanso_que_no_inicia(app, client):
    with app.app_context():
        seed_database()
    _usuario(client)

    html = client.get("/", follow_redirects=True).get_data(as_text=True)
    assert "Descansar un momento" not in html
    assert "Hacer otra serie" in html


def test_peso_y_repeticiones_son_lectura_y_los_botones_se_repiten_al_mantener(app, client):
    with app.app_context():
        seed_database()
    _usuario(client)

    html = client.get("/", follow_redirects=True).get_data(as_text=True)
    assert 'data-weight-step="10"' in html  # salto grande para no dar decenas de toques

    js = (ESTATICOS / "js" / "registro.js").read_text(encoding="utf-8")
    assert "vincularRepeticion" in js

    css = (ESTATICOS / "css" / "styles.css").read_text(encoding="utf-8")
    bloque = css.split(".stepper-display {", 1)[1].split("}", 1)[0]
    assert "border" not in bloque and "background" not in bloque  # ya no imita un campo de texto


# ---------------------------------------------------------------- parecen pulsables
def test_insignias_y_filas_informativas_no_imitan_botones(app, client):
    css = (ESTATICOS / "css" / "styles.css").read_text(encoding="utf-8")
    insignia = css.split("\n.status-badge {", 1)[1].split("}", 1)[0]
    assert "border: 2px" not in insignia
    assert "border-radius: 999px" in insignia
    assert ".duo-list-row--static" in css

    mapa_js = (ESTATICOS / "js" / "mapa.js").read_text(encoding="utf-8")
    assert "duo-list-row duo-list-row--static" in mapa_js
    # La lista de músculos bajo el mapa sí es pulsable: fila con chevron.
    assert "plain-list__row plain-list__row--action" in mapa_js
    assert "plain-list__chevron" in mapa_js

    with app.app_context():
        seed_database()
    _usuario(client)
    onboarding = client.get("/onboarding").get_data(as_text=True)
    cuerpo = onboarding.split("</title>", 1)[1]
    assert "Perfil Biométrico\n      </span>" not in cuerpo
