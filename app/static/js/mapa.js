/**
 * mapa.js — Mapa Muscular Anatómico Dual (Hombre/Mujer) estilo react-body-highlighter,
 * coloreado bicolor (#58cc02 / #a5ed6e) y Bottom Sheet con Recomendador de Ejercicios.
 */
(function () {
  const COLOR_PRIMARIO = '#58cc02';
  const COLOR_SECUNDARIO = '#a5ed6e';
  const COLOR_INACTIVO = '#d8dfe6';
  const GRAD_PRIMARIO = 'url(#grad-muscle-primary)';
  const GRAD_SECUNDARIO = 'url(#grad-muscle-secondary)';
  const GRAD_INACTIVO = 'url(#grad-muscle-rest)';
  const STORAGE_GENERO_KEY = 'fittracker_body_gender';
  const STORAGE_PRESELECT_EJ_KEY = 'fittracker_preselect_ejercicio_id';

  let diasVentanaActual = 7;
  let mostrarNombresAnatomicos = false;
  const hostSvgEl = document.getElementById('mapa-svg-host');
  const sexoPerfilAttr = hostSvgEl
    ? (hostSvgEl.getAttribute('data-sexo-perfil') || '').toUpperCase()
    : '';
  let generoActual =
    sexoPerfilAttr === 'MUJER'
      ? 'mujer'
      : sexoPerfilAttr === 'HOMBRE'
      ? 'hombre'
      : localStorage.getItem(STORAGE_GENERO_KEY) === 'mujer'
      ? 'mujer'
      : 'hombre';
  let ultimosPrimarios = [];
  let ultimosSecundarios = [];
  let grupoSeleccionadoActual = null;
  const cacheSvgTexto = {};

  const resumenListaEl = document.getElementById('mapa-muscular-lista');
  const modalMusculo = document.getElementById('modal-detalle-musculo');
  const btnCerrarSheet = document.getElementById('btn-cerrar-sheet-musculo');
  const sheetNombreEl = document.getElementById('sheet-musculo-nombre');
  const sheetEstadoEl = document.getElementById('sheet-musculo-estado');
  const sheetAnatomiaEl = document.getElementById('sheet-musculo-anatomia');
  const sheetSeriesEl = document.getElementById('sheet-musculo-series');
  const sheetSeriesSubEl = document.getElementById('sheet-musculo-series-sub');
  const sheetPrEl = document.getElementById('sheet-musculo-pr');
  const sheetPrEjEl = document.getElementById('sheet-musculo-pr-ej');
  const sheetRecientesEl = document.getElementById('sheet-ejercicios-recientes');
  const sheetRecomendadosTituloEl = document.getElementById('sheet-recomendados-titulo');
  const sheetRecomendadosEl = document.getElementById('sheet-ejercicios-recomendados');

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  async function cambiarGeneroSilueta(nuevoGenero) {
    generoActual = nuevoGenero === 'mujer' ? 'mujer' : 'hombre';
    localStorage.setItem(STORAGE_GENERO_KEY, generoActual);

    document.querySelectorAll('[data-silueta-genero]').forEach((btn) => {
      const activo = btn.getAttribute('data-silueta-genero') === generoActual;
      btn.classList.toggle('is-active', activo);
    });

    if (!hostSvgEl) return;
    const urlSvg =
      generoActual === 'mujer'
        ? hostSvgEl.getAttribute('data-url-mujer') || '/static/img/silueta_mujer.svg'
        : hostSvgEl.getAttribute('data-url-hombre') || '/static/img/silueta_hombre.svg';

    try {
      if (!cacheSvgTexto[urlSvg]) {
        const resp = await fetch(urlSvg);
        if (resp.ok) {
          cacheSvgTexto[urlSvg] = await resp.text();
        }
      }
      if (cacheSvgTexto[urlSvg]) {
        hostSvgEl.innerHTML = cacheSvgTexto[urlSvg];
        const svgInyectado = hostSvgEl.querySelector('svg');
        if (svgInyectado) {
          svgInyectado.id = 'mapa-muscular-svg';
        }
      }
    } catch (err) {
      console.warn('Usando SVG inline de respaldo:', err);
    }

    const svgRoot = document.getElementById('mapa-muscular-svg');
    if (svgRoot) {
      vincularInteraccionRegionesSVG(svgRoot);
      sincronizarEtiquetasAnatomicas(svgRoot);
      aplicarColoresSVG(svgRoot, ultimosPrimarios, ultimosSecundarios);
    }
  }

  function sincronizarEtiquetasAnatomicas(svgRoot) {
    if (!svgRoot) return;
    const capaEtiquetas = svgRoot.querySelector('#svg-etiquetas-anatomicas');
    if (capaEtiquetas) {
      capaEtiquetas.hidden = !mostrarNombresAnatomicos;
    }
  }

  async function cargarMapaMuscular(dias = 7) {
    diasVentanaActual = Number(dias) || 7;
    const svgRoot = document.getElementById('mapa-muscular-svg');
    if (!svgRoot) return;

    try {
      const resp = await fetch(`/api/mapa-muscular?dias=${encodeURIComponent(diasVentanaActual)}`, {
        headers: { Accept: 'application/json' },
      });
      if (!resp.ok) return;
      const data = await resp.json();
      ultimosPrimarios = data.primarios || [];
      ultimosSecundarios = data.secundarios || [];

      const svgActual = document.getElementById('mapa-muscular-svg');
      if (svgActual) {
        aplicarColoresSVG(svgActual, ultimosPrimarios, ultimosSecundarios);
      }
      renderizarDetalleGrupos(resumenListaEl, data.grupos || []);
    } catch (err) {
      console.warn('No se pudo cargar el mapa muscular:', err);
    }
  }

  function aplicarColoresSVG(svgRoot, primarios, secundarios) {
    const setPrimarios = new Set((primarios || []).map((n) => n.toLowerCase()));
    const setSecundarios = new Set((secundarios || []).map((n) => n.toLowerCase()));
    const tieneGradientes3D = Boolean(svgRoot.querySelector('#grad-muscle-primary'));

    const zonas = svgRoot.querySelectorAll('.muscle-region, [data-grupo]');
    zonas.forEach((zona) => {
      const nombre = (zona.getAttribute('data-grupo') || '').toLowerCase();
      zona.classList.remove('is-primario', 'is-secundario', 'is-selected');
      if (
        grupoSeleccionadoActual &&
        nombre === grupoSeleccionadoActual.toLowerCase()
      ) {
        zona.classList.add('is-selected');
        zona.style.filter = tieneGradientes3D ? 'url(#muscle-glow)' : '';
      } else {
        zona.style.filter = '';
      }

      if (setPrimarios.has(nombre)) {
        zona.classList.add('is-primario');
        zona.style.fill = tieneGradientes3D ? GRAD_PRIMARIO : COLOR_PRIMARIO;
      } else if (setSecundarios.has(nombre)) {
        zona.classList.add('is-secundario');
        zona.style.fill = tieneGradientes3D ? GRAD_SECUNDARIO : COLOR_SECUNDARIO;
      } else {
        zona.style.fill = tieneGradientes3D ? GRAD_INACTIVO : COLOR_INACTIVO;
      }
    });
  }

  function vincularInteraccionRegionesSVG(svgRoot) {
    if (!svgRoot) return;
    const regiones = svgRoot.querySelectorAll('.muscle-region, [data-grupo]');
    regiones.forEach((region) => {
      const nombreGrupo = region.getAttribute('data-grupo');
      const anatomia = region.getAttribute('data-anatomia') || '';
      if (!nombreGrupo) return;

      region.addEventListener('click', () => {
        abrirDetalleMusculo(nombreGrupo, anatomia);
      });
      region.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          abrirDetalleMusculo(nombreGrupo, anatomia);
        }
      });
    });
  }

  async function abrirDetalleMusculo(nombreGrupo, anatomiaTexto = '') {
    if (!nombreGrupo) return;
    grupoSeleccionadoActual = nombreGrupo;

    const svgRoot = document.getElementById('mapa-muscular-svg');
    if (svgRoot) {
      aplicarColoresSVG(svgRoot, ultimosPrimarios, ultimosSecundarios);
    }

    if (sheetNombreEl) sheetNombreEl.textContent = nombreGrupo;
    if (sheetAnatomiaEl) {
      sheetAnatomiaEl.textContent = anatomiaTexto || `Grupo muscular: ${nombreGrupo}`;
    }
    if (sheetRecomendadosTituloEl) {
      sheetRecomendadosTituloEl.textContent = `💡 Recomendados para entrenar ${nombreGrupo}`;
    }
    if (modalMusculo) {
      modalMusculo.hidden = false;
    }

    try {
      const resp = await fetch(
        `/api/mapa-muscular/${encodeURIComponent(nombreGrupo)}?dias=${encodeURIComponent(diasVentanaActual)}`,
        { headers: { Accept: 'application/json' } }
      );
      if (!resp.ok) return;
      const detalle = await resp.json();
      renderizarBottomSheetMusculo(detalle);
    } catch (err) {
      console.warn('Error al consultar detalle del músculo:', err);
    }
  }

  function renderizarBottomSheetMusculo(detalle) {
    if (!detalle) return;

    if (sheetEstadoEl) {
      sheetEstadoEl.className = 'status-badge';
      if (detalle.estado_activacion === 'PRIMARIO') {
        sheetEstadoEl.classList.add('status-badge--mejoro');
        sheetEstadoEl.textContent = 'Entrenado Primario';
      } else if (detalle.estado_activacion === 'SECUNDARIO') {
        sheetEstadoEl.style.backgroundColor = 'var(--color-fresh-leaf)';
        sheetEstadoEl.style.borderColor = 'var(--color-eager-green)';
        sheetEstadoEl.textContent = 'Secundario';
      } else {
        sheetEstadoEl.style.backgroundColor = '';
        sheetEstadoEl.style.borderColor = '';
        sheetEstadoEl.textContent = 'Descansado';
      }
    }

    const totalSeries =
      detalle.series_semana && typeof detalle.series_semana === 'object'
        ? detalle.series_semana.total
        : Number(detalle.total_series_semana || 0);
    const primarias = Number(detalle.series_primarias || 0);
    const secundarias = Number(detalle.series_secundarias || 0);

    if (sheetSeriesEl) {
      sheetSeriesEl.textContent = `${totalSeries} series`;
    }
    if (sheetSeriesSubEl) {
      sheetSeriesSubEl.textContent = `${primarias} primarias · ${secundarias} secundarias`;
    }

    if (sheetPrEl && sheetPrEjEl) {
      if (detalle.pr_actual && detalle.pr_actual.peso > 0) {
        sheetPrEl.textContent = `${detalle.pr_actual.peso} kg`;
        sheetPrEjEl.textContent = detalle.pr_actual.ejercicio_nombre || detalle.pr_actual.ejercicio;
      } else {
        sheetPrEl.textContent = 'Sin PR';
        sheetPrEjEl.textContent = 'Entrena este músculo hoy';
      }
    }

    if (sheetRecientesEl) {
      const recientes = detalle.ejercicios_recientes || [];
      if (recientes.length === 0) {
        sheetRecientesEl.innerHTML = `
          <div class="duo-list-row">
            <span style="font-size: 0.85rem; font-weight: 700; color: var(--color-charcoal);">
              Músculo descansado en los últimos ${detalle.dias_ventana || 7} días.
            </span>
          </div>
        `;
      } else {
        sheetRecientesEl.innerHTML = recientes
          .map(
            (ej) => `
            <div class="duo-list-row">
              <div>
                <strong style="font-family: var(--font-display); color: var(--color-night-ink);">
                  ${escapeHtml(ej.nombre)}
                </strong>
                <div style="font-size: 0.78rem; font-weight: 700; color: var(--color-charcoal);">
                  ${ej.series} series · Máx: ${ej.peso_maximo} kg
                </div>
              </div>
              <span class="status-badge ${ej.es_primario ? 'status-badge--mejoro' : ''}">
                ${ej.es_primario ? 'Primario' : 'Secundario'}
              </span>
            </div>
          `
          )
          .join('');
      }
    }

    if (sheetRecomendadosEl) {
      const recomendados = detalle.ejercicios_recomendados || [];
      if (recomendados.length === 0) {
        sheetRecomendadosEl.innerHTML = `
          <div class="duo-list-row">
            <span style="font-size: 0.85rem; font-weight: 700; color: var(--color-charcoal);">
              Sin sugerencias adicionales disponibles.
            </span>
          </div>
        `;
      } else {
        sheetRecomendadosEl.innerHTML = '';
        recomendados.forEach((ej) => {
          const fila = document.createElement('div');
          fila.className = 'duo-list-row';
          const metaTexto =
            ej.ultimo_peso !== null && ej.ultimo_peso !== undefined
              ? `Última vez: ${ej.ultimo_peso} kg × ${ej.ultimas_repeticiones}`
              : ej.entrenado_esta_semana
              ? 'Ya entrenado esta semana'
              : 'Fresco para entrenar hoy';

          fila.innerHTML = `
            <div>
              <strong style="font-family: var(--font-display); color: var(--color-night-ink);">
                ${escapeHtml(ej.nombre)}
              </strong>
              <div style="font-size: 0.78rem; font-weight: 700; color: var(--color-charcoal);">
                ${escapeHtml(metaTexto)}
              </div>
            </div>
          `;

          const btnEntrenar = document.createElement('a');
          btnEntrenar.href = `/?ejercicio_id=${encodeURIComponent(ej.id)}`;
          btnEntrenar.className = 'btn-duo btn-duo--green btn-duo--sm';
          btnEntrenar.textContent = '＋ Entrenar';
          btnEntrenar.addEventListener('click', () => {
            localStorage.setItem(STORAGE_PRESELECT_EJ_KEY, String(ej.id));
          });

          fila.appendChild(btnEntrenar);
          sheetRecomendadosEl.appendChild(fila);
        });
      }
    }
  }

  function cerrarDetalleMusculo() {
    if (modalMusculo) {
      modalMusculo.hidden = true;
    }
    grupoSeleccionadoActual = null;
    const svgRoot = document.getElementById('mapa-muscular-svg');
    if (svgRoot) {
      aplicarColoresSVG(svgRoot, ultimosPrimarios, ultimosSecundarios);
    }
  }

  function renderizarDetalleGrupos(contenedor, grupos) {
    if (!contenedor) return;
    if (!grupos || grupos.length === 0) {
      contenedor.innerHTML =
        '<p style="color: var(--color-charcoal); font-weight: 700; margin: 0;">Registra tus primeras series o toca cualquier músculo de la silueta para ver recomendaciones.</p>';
      return;
    }
    contenedor.innerHTML = '';
    grupos.forEach((g) => {
      const fila = document.createElement('button');
      fila.type = 'button';
      fila.className = 'duo-list-row';
      fila.style.width = '100%';
      fila.style.textAlign = 'left';
      fila.style.cursor = 'pointer';
      fila.innerHTML = `
        <div>
          <strong style="font-family:var(--font-display); color:var(--color-night-ink);">${escapeHtml(g.nombre)}</strong>
          <div style="font-size:0.8rem; font-weight:700; color:var(--color-charcoal);">
            ${g.series_primarias} series primarias · ${g.series_secundarias} secundarias
          </div>
        </div>
        <span class="status-badge ${g.es_primario ? 'status-badge--mejoro' : ''}"
              style="background-color:${g.es_primario ? 'var(--color-storybook-green)' : 'var(--color-fresh-leaf)'}; border-color:var(--color-eager-green);">
          ${g.es_primario ? 'Primario' : 'Secundario'}
        </span>
      `;
      fila.addEventListener('click', () => abrirDetalleMusculo(g.nombre));
      contenedor.appendChild(fila);
    });
  }

  document.querySelectorAll('[data-mapa-dias]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const dias = Number(btn.getAttribute('data-mapa-dias')) || 7;
      document.querySelectorAll('[data-mapa-dias]').forEach((b) => b.classList.remove('is-active'));
      btn.classList.add('is-active');
      cargarMapaMuscular(dias);
    });
  });

  document.querySelectorAll('[data-silueta-genero]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const gen = btn.getAttribute('data-silueta-genero');
      cambiarGeneroSilueta(gen);
    });
  });

  const btnToggleNombres = document.getElementById('btn-toggle-nombres-anatomicos');
  if (btnToggleNombres) {
    btnToggleNombres.addEventListener('click', () => {
      mostrarNombresAnatomicos = !mostrarNombresAnatomicos;
      btnToggleNombres.classList.toggle('is-active', mostrarNombresAnatomicos);
      btnToggleNombres.setAttribute('aria-pressed', mostrarNombresAnatomicos ? 'true' : 'false');
      const svgRoot = document.getElementById('mapa-muscular-svg');
      sincronizarEtiquetasAnatomicas(svgRoot);
    });
  }

  if (btnCerrarSheet) {
    btnCerrarSheet.addEventListener('click', cerrarDetalleMusculo);
  }
  if (modalMusculo) {
    modalMusculo.addEventListener('click', (e) => {
      if (e.target === modalMusculo) {
        cerrarDetalleMusculo();
      }
    });
  }

  window.FitTrackerMapa = {
    cargarMapaMuscular,
    aplicarColoresSVG,
    cambiarGeneroSilueta,
    abrirDetalleMusculo,
  };

  document.addEventListener('DOMContentLoaded', () => {
    const svgRoot = document.getElementById('mapa-muscular-svg');
    if (svgRoot) {
      vincularInteraccionRegionesSVG(svgRoot);
      if (generoActual === 'mujer') {
        cambiarGeneroSilueta('mujer');
      }
      cargarMapaMuscular(7);
    }
  });
})();
