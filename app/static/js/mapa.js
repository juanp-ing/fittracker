/**
 * mapa.js — Coloreado dinámico del Mapa Muscular Anatómico SVG Bicolor (RF-13).
 * Primarios: #58cc02 (--color-eager-green)
 * Secundarios: #a5ed6e (--color-fresh-leaf)
 */
(function () {
  const COLOR_PRIMARIO = '#58cc02';
  const COLOR_SECUNDARIO = '#a5ed6e';
  const COLOR_INACTIVO = '#e5e5e5';

  async function cargarMapaMuscular(dias = 7) {
    const svgRoot = document.getElementById('mapa-muscular-svg');
    const resumenListaEl = document.getElementById('mapa-muscular-lista');
    if (!svgRoot) return;

    try {
      const resp = await fetch(`/api/mapa-muscular?dias=${encodeURIComponent(dias)}`, {
        headers: { Accept: 'application/json' },
      });
      if (!resp.ok) return;
      const data = await resp.json();
      aplicarColoresSVG(svgRoot, data.primarios || [], data.secundarios || []);
      renderizarDetalleGrupos(resumenListaEl, data.grupos || []);
    } catch (err) {
      console.warn('No se pudo cargar el mapa muscular:', err);
    }
  }

  function aplicarColoresSVG(svgRoot, primarios, secundarios) {
    const setPrimarios = new Set(primarios.map((n) => n.toLowerCase()));
    const setSecundarios = new Set(secundarios.map((n) => n.toLowerCase()));

    const zonas = svgRoot.querySelectorAll('[data-grupo]');
    zonas.forEach((zona) => {
      const nombre = (zona.getAttribute('data-grupo') || '').toLowerCase();
      zona.classList.remove('is-primario', 'is-secundario');
      if (setPrimarios.has(nombre)) {
        zona.classList.add('is-primario');
        zona.style.fill = COLOR_PRIMARIO;
      } else if (setSecundarios.has(nombre)) {
        zona.classList.add('is-secundario');
        zona.style.fill = COLOR_SECUNDARIO;
      } else {
        zona.style.fill = COLOR_INACTIVO;
      }
    });
  }

  function renderizarDetalleGrupos(contenedor, grupos) {
    if (!contenedor) return;
    if (!grupos || grupos.length === 0) {
      contenedor.innerHTML =
        '<p style="color: var(--color-charcoal); font-weight: 700; margin: 0;">Registra tus primeras series para iluminar el mapa muscular.</p>';
      return;
    }
    contenedor.innerHTML = grupos
      .map(
        (g) => `
        <div class="duo-list-row">
          <div>
            <strong style="font-family:var(--font-display); color:var(--color-night-ink);">${g.nombre}</strong>
            <div style="font-size:0.8rem; font-weight:700; color:var(--color-charcoal);">
              ${g.series_primarias} series primarias · ${g.series_secundarias} secundarias
            </div>
          </div>
          <span class="status-badge ${g.es_primario ? 'status-badge--mejoro' : ''}"
                style="background-color:${g.es_primario ? 'var(--color-storybook-green)' : 'var(--color-fresh-leaf)'}; border-color:var(--color-eager-green);">
            ${g.es_primario ? 'Primario' : 'Secundario'}
          </span>
        </div>
      `
      )
      .join('');
  }

  document.querySelectorAll('[data-mapa-dias]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const dias = Number(btn.getAttribute('data-mapa-dias')) || 7;
      document.querySelectorAll('[data-mapa-dias]').forEach((b) => b.classList.remove('is-active'));
      btn.classList.add('is-active');
      cargarMapaMuscular(dias);
    });
  });

  window.FitTrackerMapa = {
    cargarMapaMuscular,
    aplicarColoresSVG,
  };

  document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('mapa-muscular-svg')) {
      cargarMapaMuscular(7);
    }
  });
})();
