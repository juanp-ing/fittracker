"""Pruebas funcionales E2E para las vistas HTML Mobile-First, micro-interacciones y recursos estáticos."""

from app.seeds import seed_database


def test_vistas_html_mobile_first_y_archivos_estaticos(app, client):
    """Verifica el renderizado de vistas de acceso, shell móvil, bottom nav y módulos JS/CSS."""
    with app.app_context():
        seed_database()

    # 1. Sin sesión, visitar '/' redirige a '/login'
    resp_root_anon = client.get("/")
    assert resp_root_anon.status_code == 302
    assert "/login" in resp_root_anon.headers["Location"]

    # 2. Vistas públicas de login y registro (200 OK)
    resp_login = client.get("/login")
    assert resp_login.status_code == 200
    html_login = resp_login.get_data(as_text=True)
    assert "mobile-shell" in html_login
    assert "user-scalable=no" in html_login
    assert 'class="duo-alert"' in html_login

    resp_reg = client.get("/register")
    assert resp_reg.status_code == 200

    # 3. Registrar usuario y verificar acceso a las 4 pantallas del Bottom Nav
    client.post(
        "/api/auth/register",
        json={
            "nombre": "Atleta Mobile",
            "email": "mobile@fittracker.local",
            "password": "Password123",
        },
    )

    resp_hoy = client.get("/")
    assert resp_hoy.status_code == 200
    html_hoy = resp_hoy.get_data(as_text=True)
    assert "¡SERIE TERMINADA!" in html_hoy
    assert "bottom-nav" in html_hoy
    assert 'id="pr-celebration-banner"' in html_hoy
    assert 'aria-live="polite"' in html_hoy
    assert "buscador.js" in html_hoy
    assert "registro.js" in html_hoy
    assert "cronometro.js" in html_hoy

    resp_rutinas = client.get("/rutinas")
    assert resp_rutinas.status_code == 200

    resp_mapa = client.get("/mapa")
    assert resp_mapa.status_code == 200
    html_mapa = resp_mapa.get_data(as_text=True)
    assert "mapa-muscular-svg" in html_mapa
    assert 'data-grupo="Pecho"' in html_mapa

    resp_resumen = client.get("/resumen")
    assert resp_resumen.status_code == 200
    assert "resumen-mensual-contenedor" in resp_resumen.get_data(as_text=True)

    # 4. Verificar tokens de DESIGN.md, micro-interacciones y accesibilidad en styles.css y registro.js
    resp_css = client.get("/static/css/styles.css")
    assert resp_css.status_code == 200
    texto_css = resp_css.get_data(as_text=True)
    assert "--color-eager-green: #58cc02" in texto_css
    assert "--color-spark-blue: #1cb0f6" in texto_css
    assert "--touch-target-min: 48px" in texto_css
    assert "transform: translateY(2px)" in texto_css
    assert "duo-pr-spring-in" in texto_css
    assert "@media (prefers-reduced-motion: reduce)" in texto_css

    resp_js = client.get("/static/js/registro.js")
    assert resp_js.status_code == 200
    texto_js = resp_js.get_data(as_text=True)
    assert "celebrarNuevoPR" in texto_js
    assert "prefers-reduced-motion: reduce" in texto_js

    assert client.get("/static/manifest.json").status_code == 200
    assert client.get("/static/img/silueta.svg").status_code == 200
