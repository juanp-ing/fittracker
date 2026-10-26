/**
 * registro.js — Registro de series en < 10 segundos sin teclado, Mini-Calendario Semanal,
 * Checklist con Explosión POP + Vibración Especial, Auto-Ocultado, Modal de Hidratación
 * y cola offline (RF-05, RF-06, RF-10, RNF-09, Fase V2.4).
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

  // Estado del Mini-Calendario Semanal y Checklist Diario (Fase V2.4)
  const agendaCardEl = document.getElementById('agenda-diaria-card');
  let fechaAgendaActual =
    (agendaCardEl && agendaCardEl.getAttribute('data-fecha-actual')) ||
    new Date().toISOString().slice(0, 10);
  let mostrarCompletados = false;
  let siguienteEjercicioPendiente = null;

  const nombreEjercicioEl = document.getElementById('ejercicio-activo-nombre');
  const progresoActivoPill = document.getElementById('ejercicio-activo-progreso-pill');
  const panelRegistroTactil = document.getElementById('panel-registro-tactil');
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

  // Elementos del Mini-Calendario Semanal y Modal de Ejercicio Terminado
  const mesNombreEl = document.getElementById('calendario-mes-nombre');
  const subtituloRutinaEl = document.getElementById('calendario-rutina-subtitulo');
  const switchCompletadosBtn = document.getElementById('switch-mostrar-completados');
  const switchCompletadosIcon = document.getElementById('switch-completados-icon');
  const btnSemanaAnterior = document.getElementById('btn-semana-anterior');
  const btnSemanaSiguiente = document.getElementById('btn-semana-siguiente');
  const tiraDiasEl = document.getElementById('calendario-tira-dias');
  const listaChecklistEl = document.getElementById('lista-checklist-diario');
  const bannerTodoCompletadoEl = document.getElementById('checklist-todo-completado');

  const modalTerminadoEl = document.getElementById('modal-ejercicio-terminado');
  const modalTerminadoTitulo = document.getElementById('modal-terminado-titulo');
  const modalTerminadoSubtitulo = document.getElementById('modal-terminado-subtitulo');
  const btnModalSeguirSiguiente = document.getElementById('btn-modal-seguir-siguiente');
  const btnModalDescansoAgua = document.getElementById('btn-modal-descanso-agua');

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

  function resaltarTareaActivaEnChecklist(ejercicioId) {
    if (!listaChecklistEl) return;
    listaChecklistEl.querySelectorAll('.daily-task-item').forEach((fila) => {
      const idFila = Number(fila.getAttribute('data-task-ejercicio-id'));
      fila.classList.toggle('is-active-exercise', idFila === Number(ejercicioId));
    });
  }

  function actualizarPillProgresoActivo(completadas, objetivo) {
    if (!progresoActivoPill) return;
    if (objetivo && objetivo > 0) {
      progresoActivoPill.textContent = `${completadas || 0}/${objetivo} series`;
      progresoActivoPill.hidden = false;
    } else {
      progresoActivoPill.hidden = true;
    }
  }

  function seleccionarEjercicio(ejercicio, hacerScroll) {
    if (!ejercicio) return;
    const idNormalizado = Number(ejercicio.id || ejercicio.ejercicio_id);
    ejercicioActual = {
      ...ejercicio,
      id: idNormalizado,
      nombre: ejercicio.nombre || ejercicio.ejercicio_nombre || 'Ejercicio',
    };
    if (nombreEjercicioEl) {
      nombreEjercicioEl.textContent = ejercicioActual.nombre;
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

    // Sincronizar con fila del checklist si existe
    if (listaChecklistEl) {
      const fila = listaChecklistEl.querySelector(
        `.daily-task-item[data-task-ejercicio-id="${idNormalizado}"]`
      );
      if (fila) {
        const comp = Number(fila.getAttribute('data-task-series-completadas') || 0);
        const obj = Number(fila.getAttribute('data-task-series-objetivo') || 3);
        actualizarPillProgresoActivo(comp, obj);
      } else if (ejercicio.series_objetivo) {
        actualizarPillProgresoActivo(
          ejercicio.series_completadas_hoy || 0,
          ejercicio.series_objetivo
        );
      } else {
        actualizarPillProgresoActivo(0, 0);
      }
    }

    resaltarTareaActivaEnChecklist(idNormalizado);
    actualizarDisplays();

    if (hacerScroll && panelRegistroTactil && typeof panelRegistroTactil.scrollIntoView === 'function') {
      panelRegistroTactil.scrollIntoView({
        behavior: prefiereMovimientoReducido() ? 'auto' : 'smooth',
        block: 'nearest',
      });
    }
  }

  function aplicarVisibilidadChecklist() {
    if (!listaChecklistEl) return;
    const filas = Array.from(listaChecklistEl.querySelectorAll('.daily-task-item'));
    if (filas.length === 0) {
      if (bannerTodoCompletadoEl) bannerTodoCompletadoEl.hidden = true;
      return;
    }

    let pendientesVisibles = 0;
    let totalCompletadas = 0;

    filas.forEach((fila) => {
      const estaCompletado = fila.getAttribute('data-task-completado') === 'true';
      if (estaCompletado) {
        totalCompletadas += 1;
      }
      if (fila.classList.contains('is-exploding-pop')) {
        // Mantener visible durante los 420ms de la explosión POP
        fila.hidden = false;
        return;
      }
      if (estaCompletado && !mostrarCompletados) {
        fila.hidden = true;
      } else {
        fila.hidden = false;
        if (!estaCompletado) pendientesVisibles += 1;
      }
    });

    if (bannerTodoCompletadoEl) {
      bannerTodoCompletadoEl.hidden = !(
        totalCompletadas === filas.length &&
        filas.length > 0 &&
        !mostrarCompletados
      );
    }
  }

  function vincularEventosFilasChecklist() {
    if (!listaChecklistEl) return;
    listaChecklistEl.querySelectorAll('.daily-task-item').forEach((fila) => {
      fila.addEventListener('click', () => {
        const ejData = {
          id: Number(fila.getAttribute('data-task-ejercicio-id')),
          nombre: fila.getAttribute('data-task-nombre'),
          series_objetivo: Number(fila.getAttribute('data-task-series-objetivo') || 3),
          series_completadas_hoy: Number(
            fila.getAttribute('data-task-series-completadas') || 0
          ),
          descanso_segundos: Number(fila.getAttribute('data-task-descanso') || 90),
          ultimo_peso: Number(fila.getAttribute('data-task-peso') || 20),
          ultimas_repeticiones: Number(fila.getAttribute('data-task-reps') || 10),
        };
        seleccionarEjercicio(ejData, true);
      });
    });
  }

  function renderizarAgendaDiaria(agenda) {
    if (!agenda) return;
    fechaAgendaActual = agenda.fecha || fechaAgendaActual;
    if (agendaCardEl) {
      agendaCardEl.setAttribute('data-fecha-actual', fechaAgendaActual);
    }
    if (mesNombreEl && agenda.mes_nombre) {
      mesNombreEl.textContent = agenda.mes_nombre;
    }
    if (subtituloRutinaEl) {
      subtituloRutinaEl.textContent = agenda.rutina
        ? `Tareas diarias · ${agenda.rutina.nombre}`
        : 'Tareas diarias · Tu Rutina de Hoy';
    }

    if (tiraDiasEl && Array.isArray(agenda.dias_semana)) {
      tiraDiasEl.innerHTML = agenda.dias_semana
        .map((d) => {
          const clases = [
            'weekly-day-btn',
            d.seleccionado ? 'is-selected' : '',
            d.es_hoy ? 'is-today' : '',
          ]
            .filter(Boolean)
            .join(' ');
          const puntosHtml = Array.from({ length: Number(d.puntos || 0) })
            .map(() => '<span class="calendar-dot"></span>')
            .join('');
          return `
            <button type="button" class="${clases}" data-agenda-fecha="${d.fecha}">
              <span class="calendar-day-abbr">${d.abreviatura}</span>
              <span class="calendar-day-num">${d.dia_numero}</span>
              <span class="calendar-dots-row">${puntosHtml}</span>
            </button>
          `;
        })
        .join('');

      tiraDiasEl.querySelectorAll('[data-agenda-fecha]').forEach((btnDia) => {
        btnDia.addEventListener('click', () => {
          const f = btnDia.getAttribute('data-agenda-fecha');
          if (f) cargarAgendaDiaria(f);
        });
      });
    }

    if (listaChecklistEl && Array.isArray(agenda.ejercicios)) {
      if (agenda.ejercicios.length === 0) {
        listaChecklistEl.innerHTML = `
          <div id="checklist-sin-rutina" style="font-size: 0.86rem; font-weight: 700; color: var(--color-charcoal); text-align: center; padding: 0.35rem 0;">
            Activa o clona una rutina en la pestaña <strong>Rutinas</strong> para ver tu checklist diario aquí.
          </div>
        `;
      } else {
        listaChecklistEl.innerHTML = agenda.ejercicios
          .map((ej) => {
            const completado = Boolean(ej.completado);
            return `
              <button
                type="button"
                class="daily-task-item ${completado ? 'is-completed' : ''}"
                data-task-ejercicio-id="${ej.ejercicio_id}"
                data-task-nombre="${ej.ejercicio_nombre}"
                data-task-orden="${ej.orden}"
                data-task-series-objetivo="${ej.series_objetivo}"
                data-task-series-completadas="${ej.series_completadas_hoy}"
                data-task-descanso="${ej.descanso_segundos}"
                data-task-peso="${ej.ultimo_peso}"
                data-task-reps="${ej.ultimas_repeticiones}"
                data-task-completado="${completado ? 'true' : 'false'}"
                ${completado && !mostrarCompletados ? 'hidden' : ''}
              >
                <div class="daily-task-item__info">
                  <span class="daily-task-item__title">${ej.orden}. ${ej.ejercicio_nombre}</span>
                  <span class="daily-task-item__meta" data-task-meta-text>
                    ${ej.series_completadas_hoy}/${ej.series_objetivo} series · ${ej.descanso_segundos}s descanso
                  </span>
                </div>
                <span class="task-checkbox ${completado ? 'is-checked' : ''}" aria-hidden="true">✓</span>
              </button>
            `;
          })
          .join('');
        vincularEventosFilasChecklist();
      }
      aplicarVisibilidadChecklist();

      if (ejercicioActual) {
        resaltarTareaActivaEnChecklist(ejercicioActual.id);
      } else {
        const primerPendiente =
          agenda.ejercicios.find((e) => !e.completado) || agenda.ejercicios[0];
        if (primerPendiente) {
          seleccionarEjercicio(primerPendiente, false);
        }
      }
    }
  }

  async function cargarAgendaDiaria(fechaStr, rutinaIdOpcional) {
    try {
      const params = new URLSearchParams();
      if (fechaStr) params.set('fecha', fechaStr);
      const rId =
        rutinaIdOpcional !== undefined
          ? rutinaIdOpcional
          : selectorRutina && selectorRutina.value
          ? selectorRutina.value
          : '';
      if (rId) params.set('rutina_id', String(rId));

      const resp = await fetch(`/api/sesiones/agenda-diaria?${params.toString()}`);
      if (!resp.ok) return;
      const data = await resp.json();
      renderizarAgendaDiaria(data);
    } catch (_) {}
  }

  function desplazarFechaDias(fechaIso, deltaDias) {
    const partes = (fechaIso || '').split('-').map(Number);
    const base =
      partes.length === 3
        ? new Date(Date.UTC(partes[0], partes[1] - 1, partes[2]))
        : new Date();
    base.setUTCDate(base.getUTCDate() + deltaDias);
    return base.toISOString().slice(0, 10);
  }

  function dispararVibracionVictoriaEjercicio() {
    if (typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function') {
      try {
        navigator.vibrate([60, 40, 60, 40, 180]);
      } catch (_) {}
    }
  }

  function abrirModalEjercicioTerminado(nombreEjercicio, dataRespuesta) {
    if (!modalTerminadoEl) return;
    siguienteEjercicioPendiente = dataRespuesta.siguiente_ejercicio || null;

    if (modalTerminadoTitulo) {
      modalTerminadoTitulo.textContent = `¡Completaste todas las series de ${nombreEjercicio}!`;
    }
    if (modalTerminadoSubtitulo) {
      const hechas = dataRespuesta.series_completadas_ejercicio || 3;
      const meta = dataRespuesta.series_objetivo_ejercicio || hechas;
      modalTerminadoSubtitulo.textContent = `${hechas}/${meta} series completadas con éxito.`;
    }
    if (btnModalSeguirSiguiente) {
      if (siguienteEjercicioPendiente && siguienteEjercicioPendiente.nombre) {
        btnModalSeguirSiguiente.textContent = `▶ SEGUIR CON: ${siguienteEjercicioPendiente.nombre}`;
      } else {
        btnModalSeguirSiguiente.textContent =
          '🏆 ¡RUTINA DEL DÍA COMPLETADA! FINALIZAR SESIÓN';
      }
    }
    modalTerminadoEl.hidden = false;
  }

  function cerrarModalEjercicioTerminado() {
    if (!modalTerminadoEl) return;
    modalTerminadoEl.hidden = true;
  }

  function animarExplosionPopEnChecklist(ejercicioId, hechas, objetivo, onFinish) {
    if (!listaChecklistEl) {
      if (typeof onFinish === 'function') onFinish();
      return;
    }
    const fila = listaChecklistEl.querySelector(
      `.daily-task-item[data-task-ejercicio-id="${Number(ejercicioId)}"]`
    );
    if (!fila) {
      if (typeof onFinish === 'function') onFinish();
      return;
    }

    const descanso = Number(fila.getAttribute('data-task-descanso') || 90);
    fila.setAttribute('data-task-series-completadas', String(hechas));
    fila.setAttribute('data-task-completado', 'true');
    fila.classList.add('is-completed');

    const metaEl = fila.querySelector('[data-task-meta-text]');
    if (metaEl) {
      metaEl.textContent = `${hechas}/${objetivo} series · ${descanso}s descanso`;
    }
    const checkEl = fila.querySelector('.task-checkbox');
    if (checkEl) {
      checkEl.classList.add('is-checked');
    }

    if (prefiereMovimientoReducido()) {
      aplicarVisibilidadChecklist();
      if (typeof onFinish === 'function') onFinish();
      return;
    }

    fila.classList.add('is-exploding-pop');
    if (typeof fila.animate === 'function') {
      fila.animate(
        [
          { transform: 'scale(1)', opacity: 1 },
          { transform: 'scale(1.06)', opacity: 1, offset: 0.45 },
          { transform: 'scale(0.95)', opacity: mostrarCompletados ? 1 : 0 },
        ],
        {
          duration: 420,
          easing: 'cubic-bezier(0.22, 1, 0.36, 1)',
        }
      );
    }

    setTimeout(() => {
      fila.classList.remove('is-exploding-pop');
      aplicarVisibilidadChecklist();
      if (typeof onFinish === 'function') onFinish();
    }, 420);
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
    const nombreEj = ejercicioActual ? ejercicioActual.nombre : 'Ejercicio';
    ejercicioActual.ultimo_peso = data.peso;
    ejercicioActual.ultimas_repeticiones = data.repeticiones;

    agregarSerieEnUI(
      {
        ...data,
        ejercicio_nombre: nombreEj,
      },
      false
    );

    const hechas = Number(data.series_completadas_ejercicio || 1);
    const objetivo = Number(data.series_objetivo_ejercicio || 3);
    actualizarPillProgresoActivo(hechas, objetivo);

    // Actualizar progreso en la fila del checklist diario
    if (listaChecklistEl && ejercicioActual) {
      const fila = listaChecklistEl.querySelector(
        `.daily-task-item[data-task-ejercicio-id="${Number(ejercicioActual.id)}"]`
      );
      if (fila && !data.ejercicio_completado_ahora) {
        const descanso = Number(fila.getAttribute('data-task-descanso') || 90);
        fila.setAttribute('data-task-series-completadas', String(hechas));
        fila.setAttribute('data-task-peso', String(data.peso));
        fila.setAttribute('data-task-reps', String(data.repeticiones));
        const metaEl = fila.querySelector('[data-task-meta-text]');
        if (metaEl) {
          metaEl.textContent = `${hechas}/${objetivo} series · ${descanso}s descanso`;
        }
      }
    }

    // Iniciar inmediatamente el cronómetro de descanso sin bloqueo
    if (window.FitTrackerCronometro) {
      window.FitTrackerCronometro.iniciar(data.descanso_segundos || 90);
    }

    // Disparar celebración gamificada estilo Duolingo en paralelo si es PR
    if (data.es_pr) {
      celebrarNuevoPR(nombreEj, data.peso);
    }

    // Fase V2.4: Si completó todas las series del ejercicio (ej. 3 de 3):
    // 1. Vibración Háptica Especial de Victoria [60, 40, 60, 40, 180]
    // 2. Explosión POP en el checklist y auto-ocultado
    // 3. Modal de ¡EJERCICIO TERMINADO! con recordatorio de hidratación
    if (data.ejercicio_completado_ahora) {
      dispararVibracionVictoriaEjercicio();
      animarExplosionPopEnChecklist(
        ejercicioActual ? ejercicioActual.id : data.ejercicio_id,
        hechas,
        objetivo,
        () => {
          abrirModalEjercicioTerminado(nombreEj, data);
        }
      );
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
  [
    btnPesoMenos,
    btnPesoMas,
    btnRepsMenos,
    btnRepsMas,
    btnGuardarSerie,
    btnModalSeguirSiguiente,
    btnModalDescansoAgua,
  ].forEach(vincularFeedbackTactil);

  // Switch táctil "Mostrar completados" (✕ apagado / ✓ encendido en #58cc02)
  if (switchCompletadosBtn) {
    switchCompletadosBtn.addEventListener('click', () => {
      mostrarCompletados = !mostrarCompletados;
      switchCompletadosBtn.classList.toggle('is-on', mostrarCompletados);
      switchCompletadosBtn.setAttribute(
        'aria-checked',
        mostrarCompletados ? 'true' : 'false'
      );
      if (switchCompletadosIcon) {
        switchCompletadosIcon.textContent = mostrarCompletados ? '✓' : '✕';
      }
      aplicarVisibilidadChecklist();
    });
  }

  // Navegación semanal (< y >) y días de la semana
  if (btnSemanaAnterior) {
    btnSemanaAnterior.addEventListener('click', () => {
      const nuevaFecha = desplazarFechaDias(fechaAgendaActual, -7);
      cargarAgendaDiaria(nuevaFecha);
    });
  }
  if (btnSemanaSiguiente) {
    btnSemanaSiguiente.addEventListener('click', () => {
      const nuevaFecha = desplazarFechaDias(fechaAgendaActual, 7);
      cargarAgendaDiaria(nuevaFecha);
    });
  }
  if (tiraDiasEl) {
    tiraDiasEl.querySelectorAll('[data-agenda-fecha]').forEach((btnDia) => {
      btnDia.addEventListener('click', () => {
        const f = btnDia.getAttribute('data-agenda-fecha');
        if (f) cargarAgendaDiaria(f);
      });
    });
  }
  if (selectorRutina) {
    selectorRutina.addEventListener('change', () => {
      cargarAgendaDiaria(fechaAgendaActual, selectorRutina.value || '');
    });
  }

  // Botones del Modal ¡EJERCICIO TERMINADO!
  if (btnModalSeguirSiguiente) {
    btnModalSeguirSiguiente.addEventListener('click', () => {
      cerrarModalEjercicioTerminado();
      if (siguienteEjercicioPendiente) {
        seleccionarEjercicio(siguienteEjercicioPendiente, true);
      } else {
        finalizarSesionActiva();
      }
    });
  }
  if (btnModalDescansoAgua) {
    btnModalDescansoAgua.addEventListener('click', () => {
      cerrarModalEjercicioTerminado();
      if (siguienteEjercicioPendiente) {
        seleccionarEjercicio(siguienteEjercicioPendiente, false);
      }
    });
  }

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
    cargarAgendaDiaria,
    abrirModalEjercicioTerminado,
    cerrarModalEjercicioTerminado,
  };

  document.addEventListener('DOMContentLoaded', () => {
    vincularEventosFilasChecklist();
    aplicarVisibilidadChecklist();

    // Autoseleccionar el primer ejercicio pendiente del checklist diario si existe
    if (!ejercicioActual && listaChecklistEl) {
      const primeraFila =
        listaChecklistEl.querySelector(
          '.daily-task-item[data-task-completado="false"]'
        ) || listaChecklistEl.querySelector('.daily-task-item');
      if (primeraFila) {
        seleccionarEjercicio(
          {
            id: Number(primeraFila.getAttribute('data-task-ejercicio-id')),
            nombre: primeraFila.getAttribute('data-task-nombre'),
            series_objetivo: Number(
              primeraFila.getAttribute('data-task-series-objetivo') || 3
            ),
            series_completadas_hoy: Number(
              primeraFila.getAttribute('data-task-series-completadas') || 0
            ),
            descanso_segundos: Number(
              primeraFila.getAttribute('data-task-descanso') || 90
            ),
            ultimo_peso: Number(primeraFila.getAttribute('data-task-peso') || 20),
            ultimas_repeticiones: Number(
              primeraFila.getAttribute('data-task-reps') || 10
            ),
          },
          false
        );
      }
    }

    actualizarDisplays();
    sincronizarColaOffline();
  });
})();
