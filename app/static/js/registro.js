/**
 * registro.js — Registro de series en < 10 segundos sin teclado, micro-interacciones táctiles,
 * celebración gamificada de PR (spring) y cola offline (RF-05, RF-06, RF-10, RNF-09).
 */
(function () {
  const OFFLINE_QUEUE_KEY = 'fittracker_offline_series_queue';
  const ACTIVE_SESION_KEY = 'fittracker_active_sesion_id';

  let sesionActivaId = Number(localStorage.getItem(ACTIVE_SESION_KEY)) || null;
  let ejercicioActual = null;
  let pesoActual = 20.0;
  let repeticionesActuales = 10;
  let pasoPeso = 2.5;
  let pulsePesoTimer = null;
  let pulseRepsTimer = null;

  const nombreEjercicioEl = document.getElementById('ejercicio-activo-nombre');
  const valorPesoEl = document.getElementById('stepper-peso-valor');
  const valorRepsEl = document.getElementById('stepper-reps-valor');
  const btnPesoMenos = document.getElementById('btn-peso-menos');
  const btnPesoMas = document.getElementById('btn-peso-mas');
  const btnRepsMenos = document.getElementById('btn-reps-menos');
  const btnRepsMas = document.getElementById('btn-reps-mas');
  const btnGuardarSerie = document.getElementById('btn-guardar-serie');
  const btnFinalizarSesion = document.getElementById('btn-finalizar-sesion');
  const listaSeriesHoy = document.getElementById('lista-series-sesion');
  const prBanner = document.getElementById('pr-celebration-banner');
  const prBannerTexto = document.getElementById('pr-celebration-texto');
  const syncBadge = document.getElementById('offline-sync-badge');
  const chipsPasoPeso = document.querySelectorAll('[data-weight-step]');
  const selectorRutina = document.getElementById('selector-rutina-inicio');

  function prefiereMovimientoReducido() {
    return (
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    );
  }

  function vincularFeedbackTactil(boton) {
    if (!boton) return;
    const presionar = () => boton.classList.add('is-pressed');
    const soltar = () => boton.classList.remove('is-pressed');
    boton.addEventListener('pointerdown', presionar, { passive: true });
    boton.addEventListener('pointerup', soltar, { passive: true });
    boton.addEventListener('pointercancel', soltar, { passive: true });
    boton.addEventListener('pointerleave', soltar, { passive: true });
  }

  function pulsarValor(el, tipo) {
    if (!el || prefiereMovimientoReducido()) return;
    el.classList.add('is-pulsing');
    if (tipo === 'peso') {
      if (pulsePesoTimer) clearTimeout(pulsePesoTimer);
      pulsePesoTimer = setTimeout(() => el.classList.remove('is-pulsing'), 110);
    } else {
      if (pulseRepsTimer) clearTimeout(pulseRepsTimer);
      pulseRepsTimer = setTimeout(() => el.classList.remove('is-pulsing'), 110);
    }
  }

  function celebrarNuevoPR(nombreEjercicio, peso) {
    if (!prBanner || !prBannerTexto) return;
    prBannerTexto.textContent = `¡NUEVO PR en ${nombreEjercicio}: ${peso} kg!`;
    prBanner.hidden = false;

    prBanner.classList.remove('is-celebrating');
    if (!prefiereMovimientoReducido()) {
      // Reiniciar animación spring sin bloquear el hilo principal ni el cronómetro
      void prBanner.offsetWidth;
      prBanner.classList.add('is-celebrating');
      if (typeof prBanner.animate === 'function') {
        prBanner.animate(
          [
            { opacity: 0, transform: 'translateY(8px) scale(0.92)' },
            { opacity: 1, transform: 'translateY(-2px) scale(1.03)', offset: 0.65 },
            { opacity: 1, transform: 'translateY(0) scale(1)' },
          ],
          {
            duration: 380,
            easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
            fill: 'forwards',
          }
        );
      }
    }
  }

  function actualizarDisplays() {
    if (valorPesoEl) {
      valorPesoEl.textContent = Number.isInteger(pesoActual)
        ? String(pesoActual)
        : pesoActual.toFixed(1);
    }
    if (valorRepsEl) {
      valorRepsEl.textContent = String(repeticionesActuales);
    }
    actualizarBadgeOffline();
  }

  function seleccionarEjercicio(ejercicio) {
    if (!ejercicio) return;
    ejercicioActual = ejercicio;
    if (nombreEjercicioEl) {
      nombreEjercicioEl.textContent = ejercicio.nombre;
    }
    if (ejercicio.ultimo_peso !== null && ejercicio.ultimo_peso !== undefined) {
      pesoActual = Number(ejercicio.ultimo_peso);
    }
    if (
      ejercicio.ultimas_repeticiones !== null &&
      ejercicio.ultimas_repeticiones !== undefined
    ) {
      repeticionesActuales = Number(ejercicio.ultimas_repeticiones);
    }
    actualizarDisplays();
  }

  async function asegurarSesionActiva() {
    if (sesionActivaId) {
      return sesionActivaId;
    }
    const rutinaId =
      selectorRutina && selectorRutina.value ? Number(selectorRutina.value) : null;
    const resp = await fetch('/api/sesiones', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rutina_id: rutinaId }),
    });
    if (!resp.ok) {
      throw new Error('No se pudo iniciar la sesión');
    }
    const data = await resp.json();
    sesionActivaId = data.id;
    localStorage.setItem(ACTIVE_SESION_KEY, String(sesionActivaId));
    if (btnFinalizarSesion) {
      btnFinalizarSesion.hidden = false;
    }
    return sesionActivaId;
  }

  function obtenerColaOffline() {
    try {
      return JSON.parse(localStorage.getItem(OFFLINE_QUEUE_KEY) || '[]');
    } catch (_) {
      return [];
    }
  }

  function guardarColaOffline(cola) {
    localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(cola));
    actualizarBadgeOffline();
  }

  function actualizarBadgeOffline() {
    if (!syncBadge) return;
    const cola = obtenerColaOffline();
    if (cola.length > 0) {
      syncBadge.textContent = `${cola.length} en cola offline`;
      syncBadge.hidden = false;
    } else {
      syncBadge.hidden = true;
    }
  }

  function agregarSerieEnUI(item, esOffline) {
    if (!listaSeriesHoy) return;
    const vacio = listaSeriesHoy.querySelector('[data-empty-series]');
    if (vacio) vacio.remove();

    const fila = document.createElement('div');
    fila.className = 'duo-card' + (item.es_pr ? ' duo-card--highlight' : '');
    fila.style.padding = '0.65rem 0.9rem';
    fila.style.display = 'flex';
    fila.style.justifyContent = 'space-between';
    fila.style.alignItems = 'center';

    const etiquetaEstado = esOffline
      ? '<span class="status-badge status-badge--estancado">Pendiente Sync</span>'
      : item.es_pr
      ? '<span class="status-badge status-badge--mejoro">¡NUEVO PR!</span>'
      : '<span class="status-badge">Completada</span>';

    fila.innerHTML = `
      <div>
        <strong style="font-family: var(--font-display); color: var(--color-night-ink);">
          ${item.ejercicio_nombre || (ejercicioActual ? ejercicioActual.nombre : 'Ejercicio')}
        </strong>
        <div style="font-size: 0.88rem; font-weight: 700; color: var(--color-charcoal);">
          ${item.peso} kg × ${item.repeticiones} reps (${(item.peso * item.repeticiones).toFixed(0)} kg vol)
        </div>
      </div>
      ${etiquetaEstado}
    `;
    listaSeriesHoy.prepend(fila);
  }

  async function registrarSerieActual() {
    if (!ejercicioActual) return;
    if (prBanner) {
      prBanner.hidden = true;
      prBanner.classList.remove('is-celebrating');
    }

    const payloadSerie = {
      ejercicio_id: ejercicioActual.id,
      ejercicio_nombre: ejercicioActual.nombre,
      peso: pesoActual,
      repeticiones: repeticionesActuales,
      timestamp: Date.now(),
    };

    try {
      const idSesion = await asegurarSesionActiva();
      const resp = await fetch(`/api/sesiones/${idSesion}/series`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ejercicio_id: payloadSerie.ejercicio_id,
          peso: payloadSerie.peso,
          repeticiones: payloadSerie.repeticiones,
        }),
      });

      if (resp.status === 400 || resp.status === 404) {
        // Si la sesión previa ya estaba cerrada, limpiar e iniciar una nueva
        localStorage.removeItem(ACTIVE_SESION_KEY);
        sesionActivaId = null;
        const nuevoId = await asegurarSesionActiva();
        const retry = await fetch(`/api/sesiones/${nuevoId}/series`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ejercicio_id: payloadSerie.ejercicio_id,
            peso: payloadSerie.peso,
            repeticiones: payloadSerie.repeticiones,
          }),
        });
        if (!retry.ok) throw new Error('Error al registrar serie');
        return procesarRespuestaSerie(await retry.json());
      }

      if (!resp.ok) {
        throw new Error('Fallo de red o servidor');
      }

      const data = await resp.json();
      procesarRespuestaSerie(data);
    } catch (err) {
      // Encolar en localStorage si falla la red del gimnasio (RNF-09)
      const cola = obtenerColaOffline();
      cola.push(payloadSerie);
      guardarColaOffline(cola);
      agregarSerieEnUI(payloadSerie, true);
      if (window.FitTrackerCronometro) {
        window.FitTrackerCronometro.iniciar(90);
      }
    }
  }

  function procesarRespuestaSerie(data) {
    ejercicioActual.ultimo_peso = data.peso;
    ejercicioActual.ultimas_repeticiones = data.repeticiones;
    agregarSerieEnUI(
      {
        ...data,
        ejercicio_nombre: ejercicioActual ? ejercicioActual.nombre : '',
      },
      false
    );

    // Iniciar inmediatamente el cronómetro de descanso sin bloqueo
    if (window.FitTrackerCronometro) {
      window.FitTrackerCronometro.iniciar(data.descanso_segundos || 90);
    }

    // Disparar celebración gamificada estilo Duolingo en paralelo si es PR
    if (data.es_pr) {
      celebrarNuevoPR(ejercicioActual ? ejercicioActual.nombre : 'Ejercicio', data.peso);
    }
  }

  async function sincronizarColaOffline() {
    const cola = obtenerColaOffline();
    if (cola.length === 0 || !navigator.onLine) return;

    const pendientes = [];
    for (const item of cola) {
      try {
        const idSesion = await asegurarSesionActiva();
        const resp = await fetch(`/api/sesiones/${idSesion}/series`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ejercicio_id: item.ejercicio_id,
            peso: item.peso,
            repeticiones: item.repeticiones,
          }),
        });
        if (!resp.ok) {
          pendientes.push(item);
        }
      } catch (_) {
        pendientes.push(item);
      }
    }
    guardarColaOffline(pendientes);
  }

  async function finalizarSesionActiva() {
    if (!sesionActivaId) return;
    try {
      const resp = await fetch(`/api/sesiones/${sesionActivaId}/finalizar`, {
        method: 'PATCH',
      });
      if (resp.ok) {
        localStorage.removeItem(ACTIVE_SESION_KEY);
        sesionActivaId = null;
        if (btnFinalizarSesion) btnFinalizarSesion.hidden = true;
        if (window.FitTrackerCronometro) window.FitTrackerCronometro.detener();
      }
    } catch (_) {}
  }

  // Vincular feedback táctil instantáneo (pointerdown) en controles de pulgar
  [btnPesoMenos, btnPesoMas, btnRepsMenos, btnRepsMas, btnGuardarSerie].forEach(
    vincularFeedbackTactil
  );

  // Eventos de botones gigantes +/- (sin bloqueo para toques repetidos rápidos)
  if (btnPesoMenos) {
    btnPesoMenos.addEventListener('click', () => {
      pesoActual = Math.max(0, Math.round((pesoActual - pasoPeso) * 10) / 10);
      actualizarDisplays();
      pulsarValor(valorPesoEl, 'peso');
    });
  }
  if (btnPesoMas) {
    btnPesoMas.addEventListener('click', () => {
      pesoActual = Math.round((pesoActual + pasoPeso) * 10) / 10;
      actualizarDisplays();
      pulsarValor(valorPesoEl, 'peso');
    });
  }
  if (btnRepsMenos) {
    btnRepsMenos.addEventListener('click', () => {
      repeticionesActuales = Math.max(1, repeticionesActuales - 1);
      actualizarDisplays();
      pulsarValor(valorRepsEl, 'reps');
    });
  }
  if (btnRepsMas) {
    btnRepsMas.addEventListener('click', () => {
      repeticionesActuales += 1;
      actualizarDisplays();
      pulsarValor(valorRepsEl, 'reps');
    });
  }

  chipsPasoPeso.forEach((chip) => {
    vincularFeedbackTactil(chip);
    chip.addEventListener('click', () => {
      pasoPeso = Number(chip.getAttribute('data-weight-step')) || 2.5;
      chipsPasoPeso.forEach((c) => c.classList.remove('is-active'));
      chip.classList.add('is-active');
    });
  });

  if (btnGuardarSerie) {
    btnGuardarSerie.addEventListener('click', registrarSerieActual);
  }
  if (btnFinalizarSesion) {
    btnFinalizarSesion.addEventListener('click', finalizarSesionActiva);
    btnFinalizarSesion.hidden = !sesionActivaId;
  }

  window.addEventListener('online', sincronizarColaOffline);

  window.FitTrackerRegistro = {
    seleccionarEjercicio,
    registrarSerieActual,
    celebrarNuevoPR,
    sincronizarColaOffline,
  };

  document.addEventListener('DOMContentLoaded', () => {
    actualizarDisplays();
    sincronizarColaOffline();
  });
})();
