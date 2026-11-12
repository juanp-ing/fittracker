"""Rutinas con ejercicios distintos cada día: catálogo ampliado, rutinas famosas reales, Hoy y editor."""

import re

from app import db
from app.models.rutina import Rutina
from app.seeds import seed_database
from app.seeds.initial_data import EJERCICIOS_PREDETERMINADOS_BASE, RUTINAS_FAMOSAS_BASE

PPL = "Push / Pull / Legs (Empuje, Tirón y Pierna)"
# Semana de referencia: el lunes 9 al domingo 15 de noviembre de 2026.
LUNES, MARTES, DOMINGO = "2026-11-09", "2026-11-10", "2026-11-15"


def _usuario(client, email="por.dia@fittracker.local"):
    client.post(
        "/api/auth/register",
        json={"nombre": "Por Día", "email": email, "password": "Secreta123"},
    )
    codigo = client.post("/api/auth/resend-code").get_json()["codigo_verificacion"]
    client.post("/api/auth/verify-code", json={"codigo": codigo})


def _famosas(client):
    return client.get("/api/rutinas/famosas").get_json()["rutinas_famosas"]


def _clonar(client, nombre=PPL):
    plantilla = next(r for r in _famosas(client) if r["nombre"] == nombre)
    resp = client.post(f"/api/rutinas/famosas/{plantilla['id']}/clonar")
    assert resp.status_code == 201
    return resp.get_json()


def _ids(ejercicios):
    return [e["ejercicio_id"] for e in ejercicios]


# ------------------------------------------------------------------ catálogo de ejercicios
def test_catalogo_ampliado_sin_nombres_repetidos(app):
    resumen = seed_database()

    assert resumen["total_ejercicios"] >= 100
    nombres = [e["nombre"].strip().lower() for e in EJERCICIOS_PREDETERMINADOS_BASE]
    assert len(nombres) == len(set(nombres))
    assert all(e["primarios"] for e in EJERCICIOS_PREDETERMINADOS_BASE)


def test_las_rutinas_famosas_solo_usan_ejercicios_del_catalogo():
    catalogo = {e["nombre"].strip().lower() for e in EJERCICIOS_PREDETERMINADOS_BASE}

    for rutina in RUTINAS_FAMOSAS_BASE:
        for dia in rutina["dias"]:
            for nombre, _series in dia["ejercicios"]:
                assert nombre.strip().lower() in catalogo, f"{rutina['nombre']}: falta «{nombre}»"


# ------------------------------------------------------------------ rutinas famosas reales
def test_cada_rutina_famosa_tiene_un_plan_distinto_por_dia(app, client):
    seed_database()
    _usuario(client)

    famosas = _famosas(client)

    assert len(famosas) == 12
    for rutina in famosas:
        codigos = rutina["dias_semana"].split(",")
        assert rutina["por_dias"] is True, rutina["nombre"]
        assert [d["codigo"] for d in rutina["dias"]] == codigos
        for dia in rutina["dias"]:
            assert dia["nombre"], f"{rutina['nombre']} {dia['codigo']} sin nombre"
            assert len(dia["ejercicios"]) >= 3
        planes = {tuple(_ids(d["ejercicios"])) for d in rutina["dias"]}
        assert len(planes) >= 2, f"{rutina['nombre']} repite los mismos ejercicios todos los días"


def test_push_pull_legs_no_repite_ningun_dia(app, client):
    seed_database()
    _usuario(client)

    ppl = next(r for r in _famosas(client) if r["nombre"] == PPL)

    assert [d["codigo"] for d in ppl["dias"]] == ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB"]
    assert [d["nombre"] for d in ppl["dias"]] == [
        "Empuje A", "Tirón A", "Pierna A", "Empuje B", "Tirón B", "Pierna B",
    ]
    planes = [tuple(_ids(d["ejercicios"])) for d in ppl["dias"]]
    assert len(set(planes)) == 6


def test_clonar_conserva_el_plan_de_cada_dia(app, client):
    seed_database()
    _usuario(client)
    plantilla = next(r for r in _famosas(client) if r["nombre"] == PPL)

    clon = _clonar(client)

    assert clon["por_dias"] is True
    assert [(d["codigo"], d["nombre"], _ids(d["ejercicios"])) for d in clon["dias"]] == [
        (d["codigo"], d["nombre"], _ids(d["ejercicios"])) for d in plantilla["dias"]
    ]
    assert {e["dia_semana"] for e in clon["ejercicios"]} == {"LUN", "MAR", "MIE", "JUE", "VIE", "SAB"}


def test_el_seed_repara_plantillas_antiguas_de_lista_unica(app):
    seed_database()
    plantilla = db.session.query(Rutina).filter_by(nombre=PPL, es_plantilla_famosa=True).one()
    for item in plantilla.ejercicios:  # como estaban antes: la misma lista todos los días
        item.dia_semana = None
    db.session.commit()

    reparado = seed_database()
    db.session.refresh(plantilla)

    assert reparado["rutinas_famosas_actualizadas"] == 1
    assert {i.dia_semana for i in plantilla.ejercicios} == {"LUN", "MAR", "MIE", "JUE", "VIE", "SAB"}
    assert seed_database()["rutinas_famosas_actualizadas"] == 0


# ------------------------------------------------------------------ Hoy
def test_hoy_muestra_solo_los_ejercicios_de_ese_dia(app, client):
    seed_database()
    _usuario(client)
    clon = _clonar(client)
    por_codigo = {d["codigo"]: d for d in clon["dias"]}

    lunes = client.get(f"/api/sesiones/agenda-diaria?fecha={LUNES}").get_json()
    martes = client.get(f"/api/sesiones/agenda-diaria?fecha={MARTES}").get_json()

    assert _ids(lunes["ejercicios"]) == _ids(por_codigo["LUN"]["ejercicios"])
    assert _ids(martes["ejercicios"]) == _ids(por_codigo["MAR"]["ejercicios"])
    assert _ids(lunes["ejercicios"]) != _ids(martes["ejercicios"])
    assert lunes["rutina"]["dia_codigo"] == "LUN"
    assert lunes["rutina"]["dia_nombre"] == "Empuje A"
    assert martes["rutina"]["dia_nombre"] == "Tirón A"
    assert lunes["total_ejercicios"] == len(por_codigo["LUN"]["ejercicios"])


def test_en_dia_de_descanso_se_propone_el_siguiente_entrenamiento(app, client):
    seed_database()
    _usuario(client)
    clon = _clonar(client)
    lunes = next(d for d in clon["dias"] if d["codigo"] == "LUN")

    domingo = client.get(f"/api/sesiones/agenda-diaria?fecha={DOMINGO}").get_json()

    dia_sel = next(d for d in domingo["dias_semana"] if d["seleccionado"])
    assert dia_sel["toca_entrenar"] is False
    assert domingo["rutina"]["dia_codigo"] == "LUN"
    assert _ids(domingo["ejercicios"]) == _ids(lunes["ejercicios"])


def test_el_siguiente_ejercicio_sale_del_plan_del_dia(app, client):
    seed_database()
    _usuario(client)
    clon = _clonar(client)
    hoy = client.get("/api/sesiones/agenda-diaria").get_json()
    plan_hoy = hoy["ejercicios"]
    primero = plan_hoy[0]

    sesion = client.post("/api/sesiones", json={"rutina_id": clon["id"]}).get_json()
    respuestas = [
        client.post(
            f"/api/sesiones/{sesion['id']}/series",
            json={"ejercicio_id": primero["ejercicio_id"], "peso": 40, "repeticiones": 8},
        ).get_json()
        for _ in range(primero["series_objetivo"])
    ]

    ultima = respuestas[-1]
    assert ultima["series_objetivo_ejercicio"] == primero["series_objetivo"]
    assert ultima["ejercicio_completado_ahora"] is True
    assert ultima["siguiente_ejercicio"]["ejercicio_id"] == plan_hoy[1]["ejercicio_id"]


# ------------------------------------------------------------------ rutinas propias
def test_crear_rutina_con_ejercicios_distintos_por_dia(app, client):
    seed_database()
    _usuario(client)
    cat = client.get("/api/ejercicios").get_json()["ejercicios"]
    a, b, c = cat[0]["id"], cat[1]["id"], cat[2]["id"]

    resp = client.post(
        "/api/rutinas",
        json={
            "nombre": "Mi torso y pierna",
            "dias_semana": "LUN",
            "nombres_dias": {"LUN": "Torso", "JUE": "Pierna"},
            "ejercicios": [
                {"ejercicio_id": a, "dia_semana": "LUN", "series_objetivo": 4},
                {"ejercicio_id": b, "dia_semana": "LUN"},
                {"ejercicio_id": c, "dia_semana": "JUE"},
            ],
        },
    )

    assert resp.status_code == 201
    rutina = resp.get_json()
    assert rutina["dias_semana"] == "LUN,JUE"  # el jueves se añade porque tiene ejercicios
    assert rutina["por_dias"] is True
    assert [(d["codigo"], d["nombre"], _ids(d["ejercicios"])) for d in rutina["dias"]] == [
        ("LUN", "Torso", [a, b]),
        ("JUE", "Pierna", [c]),
    ]


def test_dia_no_valido_se_rechaza(app, client):
    seed_database()
    _usuario(client)
    ej = client.get("/api/ejercicios").get_json()["ejercicios"][0]["id"]

    resp = client.post(
        "/api/rutinas",
        json={"nombre": "Mala", "ejercicios": [{"ejercicio_id": ej, "dia_semana": "LUNES"}]},
    )

    assert resp.status_code == 400


def test_rutina_de_lista_unica_sigue_igual_todos_los_dias(app, client):
    seed_database()
    _usuario(client)
    cat = client.get("/api/ejercicios").get_json()["ejercicios"]
    a, b = cat[0]["id"], cat[1]["id"]

    rutina = client.post(
        "/api/rutinas",
        json={
            "nombre": "Siempre igual",
            "dias_semana": "LUN,MAR",
            "es_favorita": True,
            "ejercicios": [{"ejercicio_id": a}, {"ejercicio_id": b}],
        },
    ).get_json()

    assert rutina["por_dias"] is False
    assert [_ids(d["ejercicios"]) for d in rutina["dias"]] == [[a, b], [a, b]]
    lunes = client.get(f"/api/sesiones/agenda-diaria?fecha={LUNES}").get_json()
    martes = client.get(f"/api/sesiones/agenda-diaria?fecha={MARTES}").get_json()
    assert _ids(lunes["ejercicios"]) == _ids(martes["ejercicios"]) == [a, b]
    assert lunes["rutina"]["dia_nombre"] is None


def test_editar_conserva_y_cambia_el_plan_por_dia(app, client):
    seed_database()
    _usuario(client)
    clon = _clonar(client)
    lunes = next(d for d in clon["dias"] if d["codigo"] == "LUN")
    martes = next(d for d in clon["dias"] if d["codigo"] == "MAR")

    resp = client.put(
        f"/api/rutinas/{clon['id']}",
        json={
            "dias_semana": "LUN,MAR",
            "nombres_dias": {"LUN": "Empuje", "MAR": "Tirón"},
            "ejercicios": [
                {"ejercicio_id": lunes["ejercicios"][0]["ejercicio_id"], "dia_semana": "LUN"},
                {"ejercicio_id": martes["ejercicios"][0]["ejercicio_id"], "dia_semana": "MAR"},
            ],
        },
    )

    assert resp.status_code == 200
    editada = resp.get_json()
    assert editada["dias_semana"] == "LUN,MAR"
    assert [(d["codigo"], d["nombre"], len(d["ejercicios"])) for d in editada["dias"]] == [
        ("LUN", "Empuje", 1),
        ("MAR", "Tirón", 1),
    ]


# ------------------------------------------------------------------ pantallas
def test_rutinas_muestra_el_plan_de_cada_dia_y_el_editor_por_dias(app, client):
    seed_database()
    _usuario(client)
    _clonar(client)

    html = client.get("/rutinas").get_data(as_text=True)

    for nombre_dia in ("Empuje A", "Tirón B", "Pierna A"):
        assert nombre_dia in html
    assert 'id="toggle-dias-distintos"' in html
    assert 'id="rutina-dia-nombre"' in html


def test_hoy_presenta_el_nombre_del_dia(app, client):
    seed_database()
    _usuario(client)
    _clonar(client)
    client.put(
        "/api/perfil",
        json={"sexo": "HOMBRE", "peso_kg": 70, "meta": "GANAR_MASA", "somatotipo": "MESOMORFO"},
    )
    agenda = client.get("/api/sesiones/agenda-diaria").get_json()

    html = client.get("/", follow_redirects=True).get_data(as_text=True)

    titulo = re.search(r'<h1 id="hero-titulo"[^>]*>(.*?)</h1>', html, re.S).group(1)
    dia_sel = next(d for d in agenda["dias_semana"] if d["seleccionado"])
    if dia_sel["toca_entrenar"]:
        assert agenda["rutina"]["dia_nombre"] in titulo
    else:
        assert "Día de descanso" in titulo
        assert agenda["rutina"]["dia_nombre"] in html
