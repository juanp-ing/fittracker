/**
 * buscador.js — Buscador instantáneo en memoria (0ms) y creación rápida de ejercicios (RF-04, RF-07).
 */
(function () {
  let catalogoEjercicios = [];
  let catalogoGrupos = [];
  let ejercicioSeleccionadoId = null;
  let gruposPrimariosSeleccionados = new Set();
  let gruposSecundariosSeleccionados = new Set();

  const inputBusqueda = document.getElementById('buscador-ejercicio-input');
  const listaResultados = document.getElementById('buscador-resultados');
  const modalBackdrop = document.getElementById('modal-crear-ejercicio');
  const inputNuevoNombre = document.getElementById('nuevo-ejercicio-nombre');
  const contenedorChipsPrimarios = document.getElementById('chips-grupos-primarios');
  const contenedorChipsSecundarios = document.getElementById('chips-grupos-secundarios');
  const btnGuardarNuevo = document.getElementById('btn-confirmar-nuevo-ejercicio');
  const btnCerrarModal = document.getElementById('btn-cerrar-modal-ejercicio');
  const errorModal = document.getElementById('modal-ejercicio-error');

  async function cargarCatalogos() {
    try {
      const [respEj, respGr] = await Promise.all([
        fetch('/api/ejercicios', { headers: { Accept: 'application/json' } }),
        fetch('/api/grupos-musculares', { headers: { Accept: 'application/json' } }),
      ]);
      if (respEj.ok) {
        const dataEj = await respEj.json();
        catalogoEjercicios = dataEj.ejercicios || [];
      }
      if (respGr.ok) {
        const dataGr = await respGr.json();
        catalogoGrupos = dataGr.grupos_musculares || [];
      }
      renderizarResultados(inputBusqueda ? inputBusqueda.value : '');
      if (catalogoEjercicios.length > 0 && !ejercicioSeleccionadoId) {
        seleccionarEjercicio(catalogoEjercicios[0]);
      }
    } catch (err) {
      console.warn('Modo sin conexión al cargar catálogo:', err);
    }
  }

  function seleccionarEjercicio(ejercicio) {
    if (!ejercicio) return;
    ejercicioSeleccionadoId = ejercicio.id;
    renderizarResultados(inputBusqueda ? inputBusqueda.value : '');

    window.dispatchEvent(
      new CustomEvent('fittracker:ejercicio-seleccionado', { detail: ejercicio })
    );
    if (window.FitTrackerRegistro && typeof window.FitTrackerRegistro.seleccionarEjercicio === 'function') {
      window.FitTrackerRegistro.seleccionarEjercicio(ejercicio);
    }
  }

  function renderizarResultados(texto) {
    if (!listaResultados) return;
    const termino = (texto || '').trim().toLowerCase();
    const filtrados = termino
      ? catalogoEjercicios.filter((e) => e.nombre.toLowerCase().includes(termino))
      : catalogoEjercicios.slice(0, 8);

    listaResultados.innerHTML = '';

    filtrados.forEach((ej) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'exercise-option' + (ej.id === ejercicioSeleccionadoId ? ' is-selected' : '');

      const primarios = (ej.grupos_primarios || []).map((g) => g.nombre).join(', ');
      const ultimoTexto =
        ej.ultimo_peso !== null && ej.ultimo_peso !== undefined
          ? `${ej.ultimo_peso} kg × ${ej.ultimas_repeticiones}`
          : 'Nuevo';

      btn.innerHTML = `
        <div>
          <div class="exercise-option__title">${escapeHtml(ej.nombre)}</div>
          <div class="exercise-option__meta">${escapeHtml(primarios || 'General')}</div>
        </div>
        <span class="status-badge status-badge--mejoro">${escapeHtml(ultimoTexto)}</span>
      `;
      btn.addEventListener('click', () => seleccionarEjercicio(ej));
      listaResultados.appendChild(btn);
    });

    if (termino.length > 0) {
      const coincidenciaExacta = catalogoEjercicios.some(
        (e) => e.nombre.trim().toLowerCase() === termino
      );
      if (!coincidenciaExacta) {
        const btnCrear = document.createElement('button');
        btnCrear.type = 'button';
        btnCrear.className = 'btn-duo btn-duo--blue btn-duo--block';
        btnCrear.textContent = `＋ Crear '${texto.trim()}' ahora`;
        btnCrear.addEventListener('click', () => abrirModalCreacion(texto.trim()));
        listaResultados.appendChild(btnCrear);
      }
    }
  }

  function renderizarChipsGrupos() {
    if (!contenedorChipsPrimarios || !contenedorChipsSecundarios) return;
    contenedorChipsPrimarios.innerHTML = '';
    contenedorChipsSecundarios.innerHTML = '';

    catalogoGrupos.forEach((g) => {
      // Chip primario
      const chipP = document.createElement('button');
      chipP.type = 'button';
      chipP.className = 'muscle-chip' + (gruposPrimariosSeleccionados.has(g.id) ? ' is-primary' : '');
      chipP.textContent = g.nombre;
      chipP.addEventListener('click', () => {
        if (gruposPrimariosSeleccionados.has(g.id)) {
          gruposPrimariosSeleccionados.delete(g.id);
        } else {
          gruposPrimariosSeleccionados.add(g.id);
          gruposSecundariosSeleccionados.delete(g.id);
        }
        renderizarChipsGrupos();
      });
      contenedorChipsPrimarios.appendChild(chipP);

      // Chip secundario
      const chipS = document.createElement('button');
      chipS.type = 'button';
      chipS.className =
        'muscle-chip' + (gruposSecundariosSeleccionados.has(g.id) ? ' is-secondary' : '');
      chipS.textContent = g.nombre;
      chipS.addEventListener('click', () => {
        if (gruposSecundariosSeleccionados.has(g.id)) {
          gruposSecundariosSeleccionados.delete(g.id);
        } else if (!gruposPrimariosSeleccionados.has(g.id)) {
          gruposSecundariosSeleccionados.add(g.id);
        }
        renderizarChipsGrupos();
      });
      contenedorChipsSecundarios.appendChild(chipS);
    });
  }

  function abrirModalCreacion(nombreInicial) {
    if (!modalBackdrop) return;
    gruposPrimariosSeleccionados.clear();
    gruposSecundariosSeleccionados.clear();
    if (catalogoGrupos.length > 0) {
      gruposPrimariosSeleccionados.add(catalogoGrupos[0].id);
    }
    if (inputNuevoNombre) {
      inputNuevoNombre.value = nombreInicial || '';
    }
    if (errorModal) {
      errorModal.hidden = true;
    }
    renderizarChipsGrupos();
    modalBackdrop.hidden = false;
  }

  function cerrarModalCreacion() {
    if (modalBackdrop) {
      modalBackdrop.hidden = true;
    }
  }

  async function guardarNuevoEjercicio() {
    const nombre = inputNuevoNombre ? inputNuevoNombre.value.trim() : '';
    const primariosIds = Array.from(gruposPrimariosSeleccionados);
    const secundariosIds = Array.from(gruposSecundariosSeleccionados);

    if (!nombre || primariosIds.length === 0) {
      if (errorModal) {
        errorModal.textContent = 'Ingresa un nombre y toca al menos 1 músculo primario.';
        errorModal.hidden = false;
      }
      return;
    }

    try {
      const resp = await fetch('/api/ejercicios', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nombre,
          grupos_primarios_ids: primariosIds,
          grupos_secundarios_ids: secundariosIds,
        }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        if (errorModal) {
          errorModal.textContent = data.error || 'No se pudo crear el ejercicio.';
          errorModal.hidden = false;
        }
        return;
      }
      catalogoEjercicios.unshift(data);
      cerrarModalCreacion();
      if (inputBusqueda) {
        inputBusqueda.value = '';
      }
      seleccionarEjercicio(data);
    } catch (err) {
      if (errorModal) {
        errorModal.textContent = 'Error de conexión al guardar el ejercicio.';
        errorModal.hidden = false;
      }
    }
  }

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  if (inputBusqueda) {
    inputBusqueda.addEventListener('input', (e) => renderizarResultados(e.target.value));
  }
  if (btnGuardarNuevo) {
    btnGuardarNuevo.addEventListener('click', guardarNuevoEjercicio);
  }
  if (btnCerrarModal) {
    btnCerrarModal.addEventListener('click', cerrarModalCreacion);
  }

  window.FitTrackerBuscador = {
    recargar: cargarCatalogos,
    abrirModalCreacion,
    obtenerCatalogo: () => catalogoEjercicios,
  };

  document.addEventListener('DOMContentLoaded', () => {
    if (inputBusqueda || listaResultados) {
      cargarCatalogos();
    }
  });
})();
