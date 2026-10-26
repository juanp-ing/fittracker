"""Pruebas de integración para API de Autenticación, Semillas y Catálogo de Ejercicios."""

from app.seeds import seed_database


def test_auth_registro_duplicado_login_logout_y_proteccion_401(client):
    """Verifica registro (201), duplicado (400/409), login (200/401) y bloqueo 401 sin sesión."""
    # 1. Acceso sin sesión a ruta protegida /api/ejercicios debe devolver 401 JSON
    unauth_resp = client.get("/api/ejercicios")
    assert unauth_resp.status_code == 401
    assert unauth_resp.is_json
    assert "error" in unauth_resp.get_json()

    # 2. Registro exitoso (201)
    reg_resp = client.post(
        "/api/auth/register",
        json={
            "nombre": "Laura Gómez",
            "email": "laura@fittracker.local",
            "password": "Password123",
        },
    )
    assert reg_resp.status_code == 201
    reg_data = reg_resp.get_json()
    assert reg_data["email"] == "laura@fittracker.local"
    assert reg_data["nombre"] == "Laura Gómez"

    # 3. Correo duplicado debe devolver 400 o 409
    dup_resp = client.post(
        "/api/auth/register",
        json={
            "nombre": "Laura Clon",
            "email": "LAURA@fittracker.local",
            "password": "Password123",
        },
    )
    assert dup_resp.status_code in (400, 409)

    # 4. Cerrar sesión (200) y comprobar que vuelve a exigir autenticación (401)
    logout_resp = client.post("/api/auth/logout")
    assert logout_resp.status_code == 200
    assert client.get("/api/ejercicios").status_code == 401

    # 5. Login inválido (401)
    bad_login = client.post(
        "/api/auth/login",
        json={
            "email": "laura@fittracker.local",
            "password": "ClaveIncorrecta",
        },
    )
    assert bad_login.status_code == 401

    # 6. Login válido (200)
    ok_login = client.post(
        "/api/auth/login",
        json={
            "email": "laura@fittracker.local",
            "password": "Password123",
        },
    )
    assert ok_login.status_code == 200
    assert client.get("/api/ejercicios").status_code == 200


def test_seed_database_idempotente_carga_grupos_y_ejercicios(app, client):
    """Verifica que seed_database cargue 10 grupos y >= 20 ejercicios sin duplicar."""
    with app.app_context():
        primera_ejecucion = seed_database()
        assert primera_ejecucion["total_grupos"] == 10
        assert primera_ejecucion["total_ejercicios"] >= 20
        assert primera_ejecucion["grupos_creados"] == 10
        assert primera_ejecucion["ejercicios_creados"] >= 20

        # Segunda ejecución idempotente: no debe crear registros duplicados
        segunda_ejecucion = seed_database()
        assert segunda_ejecucion["grupos_creados"] == 0
        assert segunda_ejecucion["ejercicios_creados"] == 0
        assert segunda_ejecucion["total_grupos"] == 10
        assert segunda_ejecucion["total_ejercicios"] == primera_ejecucion["total_ejercicios"]

    # Verificar vía API con un usuario autenticado que los ejercicios tienen músculos primarios y secundarios
    client.post(
        "/api/auth/register",
        json={
            "nombre": "Tester Seeds",
            "email": "seeds@fittracker.local",
            "password": "Password123",
        },
    )
    grupos_resp = client.get("/api/grupos-musculares")
    assert grupos_resp.status_code == 200
    assert len(grupos_resp.get_json()["grupos_musculares"]) == 10

    ej_resp = client.get("/api/ejercicios?q=Press de banca")
    assert ej_resp.status_code == 200
    ejercicios = ej_resp.get_json()["ejercicios"]
    assert len(ejercicios) >= 1
    banca = ejercicios[0]
    assert banca["es_predeterminado"] is True
    assert len(banca["grupos_primarios"]) >= 1
    assert len(banca["grupos_secundarios"]) >= 1


def test_flujo_busqueda_creacion_al_vuelo_y_aislamiento_entre_usuarios(app, client):
    """Verifica que Usuario A busque, cree un ejercicio al vuelo (201) y Usuario B no lo vea."""
    with app.app_context():
        seed_database()

    # 1. Registrar y autenticar Usuario A
    client.post(
        "/api/auth/register",
        json={
            "nombre": "Usuario A",
            "email": "usuario_a@fittracker.local",
            "password": "Password123",
        },
    )

    # 2. Usuario A busca un ejercicio personalizado que aún no existe
    busqueda_inicial = client.get("/api/ejercicios?q=Sentadilla Zercher")
    assert busqueda_inicial.status_code == 200
    assert busqueda_inicial.get_json()["ejercicios"] == []

    # 3. Obtener IDs de grupos musculares para crear el ejercicio
    grupos = {
        g["nombre"]: g["id"]
        for g in client.get("/api/grupos-musculares").get_json()["grupos_musculares"]
    }

    # 4. Usuario A crea el ejercicio personalizado al vuelo (POST /api/ejercicios -> 201)
    crear_resp = client.post(
        "/api/ejercicios",
        json={
            "nombre": "Sentadilla Zercher con Barra",
            "grupos_primarios_ids": [grupos["Cuádriceps"], grupos["Glúteos"]],
            "grupos_secundarios_ids": [grupos["Core"], grupos["Espalda"]],
        },
    )
    assert crear_resp.status_code == 201
    creado = crear_resp.get_json()
    assert creado["nombre"] == "Sentadilla Zercher con Barra"
    assert creado["es_predeterminado"] is False

    # 5. Usuario A vuelve a buscar y ahora sí encuentra su ejercicio
    busqueda_posterior = client.get("/api/ejercicios?q=Zercher")
    assert busqueda_posterior.status_code == 200
    encontrados_a = busqueda_posterior.get_json()["ejercicios"]
    assert len(encontrados_a) == 1
    assert encontrados_a[0]["id"] == creado["id"]

    # 6. Cerrar sesión de Usuario A y registrar/autenticar Usuario B
    client.post("/api/auth/logout")
    client.post(
        "/api/auth/register",
        json={
            "nombre": "Usuario B",
            "email": "usuario_b@fittracker.local",
            "password": "Password123",
        },
    )

    # 7. Usuario B busca "Zercher" y NO debe ver el ejercicio privado de Usuario A
    busqueda_b = client.get("/api/ejercicios?q=Zercher")
    assert busqueda_b.status_code == 200
    assert busqueda_b.get_json()["ejercicios"] == []

    # Pero Usuario B sí ve los ejercicios predeterminados del sistema
    todos_b = client.get("/api/ejercicios").get_json()["ejercicios"]
    assert len(todos_b) >= 20
    assert all(e["es_predeterminado"] is True for e in todos_b)
