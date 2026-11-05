/**
 * registro.js — Pantalla "Hoy" en dos estados:
 *
 *  1. Antes de entrenar: tarjeta "Hoy toca", semana y plan del día.
 *  2. Modo foco (sesión activa): ejercicio actual, series como puntos, +/- de peso y reps,
 *     panel fijo al pulgar con descanso, "Deshacer" y «¡Serie terminada!».
 *
 * La fuente de verdad de la sesión activa es el servidor (#datos-sesion-activa), no
 * localStorage. Las series sin conexión se encolan y se sincronizan al volver la red.
 * (RF-05, RF-06, RF-10, RNF-09)
 */
(function () {
  'use strict';

  const OFFLINE_QUEUE_KEY = 'fittracker_offline_series_queue';
  const LEGACY_SESION_KEY = 'fittracker_active_sesion_id';
  const SERIES_POR_DEFECTO = 3;
  const DURACION_TOAST_MS = 6000;
  const DURACION_PR_MS = 3200;
  const DIAS_LARGOS = {
    dom: 'domingo', lun: 'lunes', mar: 'martes', 'mié': 'miércoles',
    jue: 'jueves', vie: 'viernes', 'sáb': 'sábado',
  };

  const $ = (id) => document.getElementById(id);

  function leerJSON(id) {
    const el = $(id);
    if (!el) return null;
    try {
      return JSON.parse(el.textContent || 'null');
    } catch (_) {
      return null;
    }
  }

  // La sesión activa ya no vive en localStorage: limpiar el valor heredado.
  localStorage.removeItem(LEGACY_SESION_KEY);

  const estado = {
    sesion: leerJSON('datos-sesion-activa'),
    agenda: leerJSON('datos-agenda'),
    libre: false,
    ejercicioActual: null,
    peso: 20,
    reps: 10,
    pasoPeso: 2.5,
    mostrarCompletados: false,
    guardando: false,
    timerToast: null,
    timerPR: null,
    timerReloj: null,
    serieDeshacible: null,
  };
  if (estado.sesion && !Array.isArray(estado.sesion.series)) estado.sesion.series = [];

  // ------------------------------------------------------------------ elementos
  const vistaEl = $('vista-hoy');
  const previoEl = $('hoy-previo');
  const focoEl = $('hoy-foco');
  const dockEl = $('focus-dock');

  const heroEyebrow = $('hero-eyebrow');
  const heroTitulo = $('hero-titulo');
  const heroMeta = $('hero-meta');
  const heroProgreso = $('hero-progreso');
  const heroProgresoBarra = $('hero-progreso-barra');
  const heroProgresoTexto = $('hero-progreso-texto');
  const btnEmpezar = $('btn-empezar-entrenamiento');
  const heroRacha = $('hero-racha');
  const heroRachaTexto = $('hero-racha-texto');
  const heroSemana = $('hero-semana');
  const heroSemanaSegmentos = $('hero-semana-segmentos');
  const heroSemanaTexto = $('hero-semana-texto');
  const selectorRutina = $('selector-rutina-inicio');

  const agendaSeccion = $('agenda-diaria-card');
  const mesNombreEl = $('calendario-mes-nombre');
  const tiraDiasEl = $('calendario-tira-dias');
  const btnSemanaAnterior = $('btn-semana-anterior');
  const btnSemanaSiguiente = $('btn-semana-siguiente');
  const switchCompletadosBtn = $('switch-mostrar-completados');
  const switchCompletadosIcon = $('switch-completados-icon');
  const listaChecklistEl = $('lista-checklist-diario');
  const bannerTodoCompletadoEl = $('checklist-todo-completado');

  const rutinaFocoEl = $('foco-rutina-nombre');
  const relojSesionEl = $('foco-reloj-sesion');
  const btnFinalizarSesion = $('btn-finalizar-sesion');
  const posicionEl = $('foco-posicion');
  const nombreEjercicioEl = $('ejercicio-activo-nombre');
  const puntosSeriesEl = $('foco-puntos-series');
  const seriesTextoEl = $('foco-series-texto');
  const ultimaVezEl = $('foco-ultima-vez');
  const btnCambiarEjercicio = $('btn-cambiar-ejercicio');
  const btnSiguiente = $('foco-siguiente');
  const siguienteNombreEl = $('foco-siguiente-nombre');
  const listaSeriesEl = $('lista-series-sesion');
  const seriesVacioEl = $('series-sesion-vacio');

  const valorPesoEl = $('stepper-peso-valor');
  const valorRepsEl = $('stepper-reps-valor');
  const btnPesoMenos = $('btn-peso-menos');
  const btnPesoMas = $('btn-peso-mas');
  const btnRepsMenos = $('btn-reps-menos');
  const btnRepsMas = $('btn-reps-mas');
  const chipsPasoPeso = document.querySelectorAll('[data-weight-step]');
  const btnGuardarSerie = $('btn-guardar-serie');

  const prBanner = $('pr-celebration-banner');
  const prBannerTexto = $('pr-celebration-texto');
  const prAntesEl = $('pr-celebration-antes');
  const prAhoraEl = $('pr-celebration-ahora');
  const btnCerrarCelebracion = $('btn-cerrar-celebracion');
  const toastEl = $('toast-deshacer');
  const toastTextoEl = $('toast-deshacer-texto');
  const toastAccionBtn = $('btn-toast-deshacer');
  const syncBadge = $('offline-sync-badge');

  const sheetCambiar = $('sheet-cambiar-ejercicio');
  const sheetBloqueRutina = $('sheet-bloque-rutina');
  const sheetListaRutina = $('sheet-lista-rutina');
  const btnCerrarSheetCambiar = $('btn-cerrar-sheet-cambiar');
  const btnNuevoEjercicio = $('btn-nuevo-ejercicio');
  const inputBusqueda = $('buscador-ejercicio-input');

  const modalTerminadoEl = $('modal-ejercicio-terminado');
  const modalTerminadoTitulo = $('modal-terminado-titulo');
  const modalTerminadoSubtitulo = $('modal-terminado-subtitulo');
  const btnModalSeguirSiguiente = $('btn-modal-seguir-siguiente');
  const btnModalDescansoAgua = $('btn-modal-descanso-agua');

  const modalResumenEl = $('modal-sesion-terminada');
  const btnCerrarResumen = $('btn-cerrar-resumen-sesion');

  // ------------------------------------------------------------------ utilidades
  function escapeHtml(str) {
    return String(str == null ? '' : str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function formatearPeso(valor) {
    const n = Number(valor) || 0;
    return Number.isInteger(n) ? String(n) : String(Math.round(n * 100) / 100);
  }

  function formatearKg(valor) {
    return `${Math.round(Number(valor) || 0).toLocaleString('es')} kg`;
  }

  function parsearFechaUTC(iso) {
    if (!iso) return null;
    const conZona = /([zZ]|[+-]\d\d:?\d\d)$/.test(iso) ? iso : `${iso}Z`;
    const fecha = new Date(conZona);
    return Number.isNaN(fecha.getTime()) ? null : fecha;
  }

  function formatearDuracion(ms) {
    const total = Math.max(0, Math.floor(ms / 1000));
    const h = Math.floor(total / 3600);
    const m = Math.floor((total % 3600) / 60);
    const s = total % 60;
    const mm = String(m).padStart(2, '0');
    const ss = String(s).padStart(2, '0');
    return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
  }

  function prefiereMovimientoReducido() {
    return (
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    );
  }

  function vibrar(patron) {
    if (typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function') {
      try {
        navigator.vibrate(patron);
      } catch (_) {}
    }
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

  function pulsarValor(el) {
    if (!el || prefiereMovimientoReducido()) return;
    el.classList.remove('is-pulsing');
    void el.offsetWidth;
    el.classList.add('is-pulsing');
    setTimeout(() => el.classList.remove('is-pulsing'), 110);
  }

  function esErrorDeRed(err) {
    return err instanceof TypeError || (typeof navigator !== 'undefined' && navigator.onLine === false);
  }

  // ------------------------------------------------------------------ modelo del plan
  function itemsRutina() {
    if (estado.libre || !estado.agenda) return [];
    return estado.agenda.ejercicios || [];
  }

  function itemDe(ejercicioId) {
    return itemsRutina().find((it) => Number(it.ejercicio_id) === Number(ejercicioId)) || null;
  }

  function seriesEnSesion(ejercicioId) {
    if (!estado.sesion) return 0;
    return estado.sesion.series.filter((s) => Number(s.ejercicio_id) === Number(ejercicioId)).length;
  }

  function progresoDe(ejercicioId) {
    const item = itemDe(ejercicioId);
    const objetivo = item ? Number(item.series_objetivo) || SERIES_POR_DEFECTO : SERIES_POR_DEFECTO;
    const hechas = item ? Number(item.series_completadas_hoy) || 0 : seriesEnSesion(ejercicioId);
    return { hechas, objetivo, enRutina: Boolean(item) };
  }

  function recalcularTotalesAgenda() {
    const a = estado.agenda;
    if (!a || !Array.isArray(a.ejercicios)) return;
    a.series_hechas = a.ejercicios.reduce(
      (acc, it) => acc + Math.min(Number(it.series_completadas_hoy) || 0, Number(it.series_objetivo) || 0),
      0
    );
  }

  function ajustarProgreso(ejercicioId, delta) {
    const item = itemDe(ejercicioId);
    if (!item) return;
    item.series_completadas_hoy = Math.max(0, (Number(item.series_completadas_hoy) || 0) + delta);
    item.completado = item.series_completadas_hoy >= (Number(item.series_objetivo) || 0);
    recalcularTotalesAgenda();
  }

  function siguientePendiente() {
    const items = itemsRutina();
    if (!items.length) return null;
    const actualId = estado.ejercicioActual ? Number(estado.ejercicioActual.id) : null;
    const idx = items.findIndex((it) => Number(it.ejercicio_id) === actualId);
    const orden = idx >= 0 ? items.slice(idx + 1).concat(items.slice(0, idx)) : items;
    return (
      orden.find(
        (it) =>
          Number(it.ejercicio_id) !== actualId &&
          (Number(it.series_completadas_hoy) || 0) < (Number(it.series_objetivo) || 0)
      ) || null
    );
  }

  function diaSeleccionado() {
    const dias = (estado.agenda && estado.agenda.dias_semana) || [];
    return dias.find((d) => d.seleccionado) || null;
  }

  // ------------------------------------------------------------------ modos
  function establecerModo(modo) {
    const foco = modo === 'foco';
    if (vistaEl) vistaEl.dataset.modo = modo;
    if (previoEl) previoEl.hidden = foco;
    if (focoEl) focoEl.hidden = !foco;
    if (dockEl) dockEl.hidden = !foco;
    document.body.classList.toggle('has-focus-dock', foco);
    if (foco) {
      iniciarRelojSesion();
    } else {
      detenerRelojSesion();
      ocultarToast();
    }
    actualizarAlturaDock();
    window.scrollTo({ top: 0, behavior: 'auto' });
  }

  function actualizarAlturaDock() {
    const alto = dockEl && !dockEl.hidden ? dockEl.offsetHeight : 0;
    document.documentElement.style.setProperty('--dock-h', `${alto}px`);
  }

  // ------------------------------------------------------------------ estado 1: antes de entrenar
  function filaPlanHtml(it) {
    const hechas = Number(it.series_completadas_hoy) || 0;
    const objetivo = Number(it.series_objetivo) || SERIES_POR_DEFECTO;
    const completado = hechas >= objetivo;
    const esActual = estado.ejercicioActual && Number(estado.ejercicioActual.id) === Number(it.ejercicio_id);
    const progreso = completado
      ? '<svg class="icon icon--sm" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'
      : `${hechas}/${objetivo}`;
    return `
      <button type="button"
        class="daily-task-item${completado ? ' is-completed' : ''}${esActual ? ' is-active-exercise' : ''}"
        data-task-ejercicio-id="${Number(it.ejercicio_id)}">
        <span class="daily-task-item__info">
          <span class="daily-task-item__title">${escapeHtml(it.ejercicio_nombre)}</span>
          <span class="daily-task-item__meta">${objetivo} series · ${Number(it.descanso_segundos) || 90}s descanso</span>
        </span>
        <span class="task-progress${completado ? ' is-done' : ''}" aria-label="${hechas} de ${objetivo} series">${progreso}</span>
      </button>`;
  }

  function renderizarPrevio() {
    const a = estado.agenda;
    if (!a) return;
    const dia = diaSeleccionado();
    const esHoy = !dia || dia.es_hoy;
    const nombreDia = dia ? DIAS_LARGOS[dia.abreviatura] || dia.abreviatura : '';
    const rutina = estado.libre ? null : a.rutina;
    const items = itemsRutina();

    if (heroEyebrow) {
      if (rutina && dia && !dia.toca_entrenar) {
        heroEyebrow.textContent = esHoy ? 'Hoy es día de descanso' : `El ${nombreDia} ${dia.dia_numero} es de descanso`;
      } else {
        heroEyebrow.textContent = esHoy ? 'Hoy toca' : `Plan del ${nombreDia} ${dia.dia_numero}`;
      }
    }
    if (heroTitulo) heroTitulo.textContent = rutina ? rutina.nombre : 'Entrenamiento libre';
    if (heroMeta) {
      heroMeta.textContent = items.length
        ? `${items.length} ejercicios · ${a.series_totales} series · ~${a.minutos_estimados} min`
        : 'Elige ejercicios sobre la marcha o activa una rutina en la pestaña Rutinas.';
    }
    const hechas = items.length ? Number(a.series_hechas) || 0 : 0;
    const totales = Number(a.series_totales) || 0;
    if (heroProgreso) heroProgreso.hidden = !(hechas > 0 && totales > 0);
    if (heroProgresoBarra) heroProgresoBarra.style.width = `${totales ? Math.round((hechas / totales) * 100) : 0}%`;
    if (heroProgresoTexto) heroProgresoTexto.textContent = `${hechas} de ${totales} series hechas`;
    if (btnEmpezar) {
      if (estado.ejercicioActual && !itemDe(estado.ejercicioActual.id)) {
        btnEmpezar.textContent = `Empezar con ${estado.ejercicioActual.nombre}`;
      } else {
        btnEmpezar.textContent = hechas > 0 && esHoy ? 'Continuar entrenamiento' : 'Empezar entrenamiento';
      }
    }

    renderizarRacha(a.racha);

    if (agendaSeccion) agendaSeccion.setAttribute('data-fecha-actual', a.fecha || '');
    if (mesNombreEl && a.mes_nombre) {
      mesNombreEl.textContent = a.mes_nombre.charAt(0).toUpperCase() + a.mes_nombre.slice(1);
    }

    if (tiraDiasEl && Array.isArray(a.dias_semana)) {
      tiraDiasEl.innerHTML = a.dias_semana
        .map((d) => {
          const clases = ['weekly-day-btn', d.seleccionado ? 'is-selected' : '', d.es_hoy ? 'is-today' : '']
            .filter(Boolean)
            .join(' ');
          const puntos = '<span class="calendar-dot"></span>'.repeat(Number(d.puntos) || 0);
          return `
            <button type="button" class="${clases}" data-agenda-fecha="${escapeHtml(d.fecha)}"
              aria-pressed="${d.seleccionado ? 'true' : 'false'}">
              <span class="calendar-day-abbr">${escapeHtml(d.abreviatura)}</span>
              <span class="calendar-day-num">${Number(d.dia_numero)}</span>
              <span class="calendar-dots-row">${puntos}</span>
            </button>`;
        })
        .join('');
    }

    if (listaChecklistEl) {
      listaChecklistEl.innerHTML = items.length
        ? items.map(filaPlanHtml).join('')
        : `<p id="checklist-sin-rutina" class="empty-note">${
            estado.libre
              ? 'Modo libre: elegirás cada ejercicio al empezar.'
              : 'No hay ejercicios planificados para este día. Activa o clona una rutina en la pestaña <strong>Rutinas</strong>.'
          }</p>`;
    }
    aplicarVisibilidadChecklist();
  }

  function renderizarRacha(racha) {
    if (!racha) return;
    const semanas = Number(racha.semanas_seguidas) || 0;
    if (heroRacha) heroRacha.hidden = semanas === 0;
    if (heroRachaTexto) heroRachaTexto.textContent = `${semanas} ${semanas === 1 ? 'semana' : 'semanas'} seguidas`;
    const meta = Number(racha.meta_dias_semana) || 0;
    const hechos = Number(racha.dias_semana_actual) || 0;
    if (heroSemana) heroSemana.classList.toggle('is-done', Boolean(racha.semana_cumplida));
    if (heroSemanaSegmentos) {
      heroSemanaSegmentos.innerHTML = Array.from(
        { length: meta },
        (_, i) => `<span class="week-goal__seg${i < hechos ? ' is-done' : ''}"></span>`
      ).join('');
    }
    if (heroSemanaTexto) {
      heroSemanaTexto.textContent = racha.semana_cumplida
        ? `Meta semanal cumplida · ${hechos} días`
        : `Esta semana: ${hechos} de ${meta} días`;
    }
  }

  function aplicarVisibilidadChecklist() {
    if (!listaChecklistEl) return;
    const filas = Array.from(listaChecklistEl.querySelectorAll('.daily-task-item'));
    let completadas = 0;
    filas.forEach((fila) => {
      const completa = fila.classList.contains('is-completed');
      if (completa) completadas += 1;
      fila.hidden = completa && !estado.mostrarCompletados;
    });
    if (bannerTodoCompletadoEl) {
      bannerTodoCompletadoEl.hidden = !(filas.length > 0 && completadas === filas.length && !estado.mostrarCompletados);
    }
  }

  async function cargarAgendaDiaria(fechaStr, rutinaIdOpcional) {
    try {
      const params = new URLSearchParams();
      if (fechaStr) params.set('fecha', fechaStr);
      const rutinaId =
        rutinaIdOpcional !== undefined ? rutinaIdOpcional : selectorRutina ? selectorRutina.value : '';
      if (rutinaId) params.set('rutina_id', String(rutinaId));
      const resp = await fetch(`/api/sesiones/agenda-diaria?${params.toString()}`);
      if (!resp.ok) return;
      estado.agenda = await resp.json();
      renderizarPrevio();
      if (estado.sesion) renderizarFoco();
    } catch (_) {}
  }

  function desplazarFechaDias(fechaIso, deltaDias) {
    const partes = (fechaIso || '').split('-').map(Number);
    const base = partes.length === 3 ? new Date(Date.UTC(partes[0], partes[1] - 1, partes[2])) : new Date();
    base.setUTCDate(base.getUTCDate() + deltaDias);
    return base.toISOString().slice(0, 10);
  }

  // ------------------------------------------------------------------ sesión
  async function crearSesion(rutinaId) {
    const resp = await fetch('/api/sesiones', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rutina_id: rutinaId || null }),
    });
    if (!resp.ok) throw new Error('No se pudo iniciar la sesión');
    const data = await resp.json();
    estado.sesion = {
      ...data,
      rutina_nombre: rutinaId && estado.agenda && estado.agenda.rutina ? estado.agenda.rutina.nombre : null,
      series: [],
    };
    return estado.sesion.id;
  }

  async function asegurarSesion() {
    if (estado.sesion) return estado.sesion.id;
    const rutinaId = !estado.libre && estado.agenda && estado.agenda.rutina ? estado.agenda.rutina.id : null;
    return crearSesion(rutinaId);
  }

  async function empezarEntrenamiento(ejercicioIdPreferido) {
    if (btnEmpezar) btnEmpezar.disabled = true;
    try {
      // El entrenamiento siempre ocurre hoy: si se estaba mirando otro día, volver a hoy.
      const dia = diaSeleccionado();
      if (dia && !dia.es_hoy) await cargarAgendaDiaria(null);
      await asegurarSesion();
    } catch (err) {
      mostrarToast(
        esErrorDeRed(err)
          ? 'Sin conexión: no se pudo empezar. Inténtalo de nuevo.'
          : 'No se pudo empezar el entrenamiento.'
      );
      return;
    } finally {
      if (btnEmpezar) btnEmpezar.disabled = false;
    }

    establecerModo('foco');

    const preferido = ejercicioIdPreferido ? itemDe(ejercicioIdPreferido) : null;
    if (preferido) {
      seleccionarEjercicio(preferido);
    } else if (!estado.ejercicioActual || itemsRutina().length) {
      const primero = itemsRutina().find(
        (it) => (Number(it.series_completadas_hoy) || 0) < (Number(it.series_objetivo) || 0)
      );
      if (estado.ejercicioActual && !itemDe(estado.ejercicioActual.id)) {
        seleccionarEjercicio(estado.ejercicioActual);
      } else if (primero) {
        seleccionarEjercicio(primero);
      } else {
        estado.ejercicioActual = null;
        renderizarFoco();
        abrirSheetCambiar();
      }
    } else {
      renderizarFoco();
    }
  }

  async function finalizarSesionActiva() {
    if (!estado.sesion) return;
    const series = estado.sesion.series;
    const pregunta = series.length
      ? '¿Terminar el entrenamiento de hoy?'
      : 'Aún no registraste series. ¿Salir del entrenamiento?';
    if (!window.confirm(pregunta)) return;

    try {
      const resp = await fetch(`/api/sesiones/${estado.sesion.id}/finalizar`, { method: 'PATCH' });
      // 400 = ya estaba finalizada (p. ej. desde otro dispositivo): se trata como éxito.
      if (!resp.ok && resp.status !== 400) {
        mostrarToast('No se pudo terminar el entrenamiento. Inténtalo de nuevo.');
        return;
      }
    } catch (_) {
      mostrarToast('Sin conexión: no se pudo terminar el entrenamiento.');
      return;
    }

    if (window.FitTrackerCronometro) window.FitTrackerCronometro.detener();
    const inicio = parsearFechaUTC(estado.sesion.fecha_inicio);
    const resumen = {
      duracionMin: inicio ? Math.max(1, Math.round((Date.now() - inicio.getTime()) / 60000)) : 0,
      series: series.length,
      volumen: series.reduce((acc, s) => acc + Number(s.peso) * Number(s.repeticiones), 0),
      prs: series.filter((s) => s.es_pr).length,
    };
    estado.sesion = null;
    estado.ejercicioActual = null;

    if (resumen.series > 0 && modalResumenEl) {
      $('resumen-sesion-duracion').textContent = `${resumen.duracionMin} min`;
      $('resumen-sesion-series').textContent = String(resumen.series);
      $('resumen-sesion-volumen').textContent = formatearKg(resumen.volumen);
      $('resumen-sesion-prs').textContent = String(resumen.prs);
      abrirHoja(modalResumenEl);
    } else {
      establecerModo('previo');
    }
    cargarAgendaDiaria(null);
  }

  function iniciarRelojSesion() {
    detenerRelojSesion();
    const tick = () => {
      const inicio = estado.sesion ? parsearFechaUTC(estado.sesion.fecha_inicio) : null;
      if (relojSesionEl) relojSesionEl.textContent = inicio ? formatearDuracion(Date.now() - inicio.getTime()) : '00:00';
    };
    tick();
    estado.timerReloj = setInterval(tick, 1000);
  }

  function detenerRelojSesion() {
    if (estado.timerReloj) clearInterval(estado.timerReloj);
    estado.timerReloj = null;
  }

  // ------------------------------------------------------------------ estado 2: modo foco
  function normalizarEjercicio(ej) {
    const id = Number(ej.id || ej.ejercicio_id);
    const item = itemDe(id);
    const fuente = item || ej;
    return {
      id,
      nombre: ej.nombre || ej.ejercicio_nombre || (item && item.ejercicio_nombre) || 'Ejercicio',
      ultimo_peso: fuente.ultimo_peso != null ? Number(fuente.ultimo_peso) : null,
      ultimas_repeticiones: fuente.ultimas_repeticiones != null ? Number(fuente.ultimas_repeticiones) : null,
      descanso_segundos: Number((item && item.descanso_segundos) || ej.descanso_segundos) || 90,
    };
  }

  function seleccionarEjercicio(ejercicio) {
    if (!ejercicio) return;
    estado.ejercicioActual = normalizarEjercicio(ejercicio);
    if (estado.ejercicioActual.ultimo_peso != null) estado.peso = estado.ejercicioActual.ultimo_peso;
    if (estado.ejercicioActual.ultimas_repeticiones != null) estado.reps = estado.ejercicioActual.ultimas_repeticiones;
    cerrarHoja(sheetCambiar);
    renderizarFoco();
    renderizarPrevio();
  }

  function renderizarFoco() {
    const ej = estado.ejercicioActual;
    if (rutinaFocoEl) {
      rutinaFocoEl.textContent = (estado.sesion && estado.sesion.rutina_nombre) || 'Entrenamiento libre';
    }

    if (!ej) {
      if (nombreEjercicioEl) nombreEjercicioEl.textContent = 'Elige un ejercicio';
      if (posicionEl) posicionEl.textContent = 'Toca «Cambiar» para elegir';
      if (puntosSeriesEl) puntosSeriesEl.innerHTML = '';
      if (seriesTextoEl) seriesTextoEl.textContent = '';
      if (ultimaVezEl) ultimaVezEl.hidden = true;
      if (btnGuardarSerie) btnGuardarSerie.disabled = true;
    } else {
      const items = itemsRutina();
      const idx = items.findIndex((it) => Number(it.ejercicio_id) === ej.id);
      const { hechas, objetivo } = progresoDe(ej.id);

      if (nombreEjercicioEl) nombreEjercicioEl.textContent = ej.nombre;
      if (posicionEl) posicionEl.textContent = idx >= 0 ? `Ejercicio ${idx + 1} de ${items.length}` : 'Ejercicio libre';
      if (puntosSeriesEl) {
        const total = Math.min(Math.max(objetivo, hechas), 12);
        puntosSeriesEl.innerHTML = Array.from({ length: total }, (_, i) => {
          const clase = i < hechas ? 'is-done' : i === hechas ? 'is-current' : '';
          return `<span class="set-dot ${clase}"></span>`;
        }).join('');
      }
      if (seriesTextoEl) {
        seriesTextoEl.textContent =
          hechas >= objetivo ? `${hechas} de ${objetivo} series · objetivo cumplido` : `Serie ${hechas + 1} de ${objetivo}`;
      }
      if (ultimaVezEl) {
        const tiene = ej.ultimo_peso != null && ej.ultimas_repeticiones != null;
        ultimaVezEl.hidden = !tiene;
        if (tiene) ultimaVezEl.textContent = `Última serie: ${formatearPeso(ej.ultimo_peso)} kg × ${ej.ultimas_repeticiones}`;
      }
      if (btnGuardarSerie) btnGuardarSerie.disabled = false;
    }

    const siguiente = ej ? siguientePendiente() : null;
    if (btnSiguiente) {
      btnSiguiente.hidden = !siguiente;
      if (siguiente && siguienteNombreEl) siguienteNombreEl.textContent = siguiente.ejercicio_nombre;
    }

    actualizarDisplays();
    renderizarListaSeries();
  }

  function actualizarDisplays() {
    if (valorPesoEl) valorPesoEl.textContent = formatearPeso(estado.peso);
    if (valorRepsEl) valorRepsEl.textContent = String(estado.reps);
    actualizarBadgeOffline();
  }

  function renderizarListaSeries() {
    if (!listaSeriesEl) return;
    const guardadas = estado.sesion ? estado.sesion.series.slice().reverse() : [];
    const pendientes = obtenerColaOffline().slice().reverse();

    const filasPendientes = pendientes.map(
      (s) => `
        <li class="log-row is-pending">
          <span class="log-row__info">
            <strong class="log-row__name">${escapeHtml(s.ejercicio_nombre)}</strong>
            <span class="log-row__detail">${formatearPeso(s.peso)} kg × ${Number(s.repeticiones)}</span>
          </span>
          <span class="status-badge status-badge--estancado">Sin enviar</span>
        </li>`
    );
    const filasGuardadas = guardadas.map(
      (s) => `
        <li class="log-row${s.es_pr ? ' is-pr' : ''}">
          <span class="log-row__info">
            <strong class="log-row__name">${escapeHtml(s.ejercicio_nombre)}</strong>
            <span class="log-row__detail">${formatearPeso(s.peso)} kg × ${Number(s.repeticiones)}</span>
          </span>
          ${s.es_pr ? '<span class="status-badge status-badge--mejoro">Récord</span>' : ''}
          <button type="button" class="log-row__delete" data-borrar-serie="${Number(s.id)}"
            aria-label="Borrar serie de ${escapeHtml(s.ejercicio_nombre)}, ${formatearPeso(s.peso)} kg por ${Number(s.repeticiones)}">
            <svg class="icon icon--sm" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 7h14M10 11v6M14 11v6M6 7l1 12h10l1-12M9 7V4h6v3"/></svg>
          </button>
        </li>`
    );
    listaSeriesEl.innerHTML = filasPendientes.concat(filasGuardadas).join('');
    if (seriesVacioEl) seriesVacioEl.hidden = filasPendientes.length + filasGuardadas.length > 0;
  }

  // ------------------------------------------------------------------ registrar / deshacer
  async function postSerie(sesionId, payload) {
    return fetch(`/api/sesiones/${sesionId}/series`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ejercicio_id: payload.ejercicio_id,
        peso: payload.peso,
        repeticiones: payload.repeticiones,
      }),
    });
  }

  async function registrarSerieActual() {
    const ej = estado.ejercicioActual;
    if (!ej || estado.guardando) return;
    estado.guardando = true;
    if (btnGuardarSerie) btnGuardarSerie.disabled = true;
    ocultarPR();

    const payload = {
      ejercicio_id: ej.id,
      ejercicio_nombre: ej.nombre,
      peso: estado.peso,
      repeticiones: estado.reps,
      timestamp: Date.now(),
    };

    try {
      let sesionId = await asegurarSesion();
      let resp = await postSerie(sesionId, payload);
      if (resp.status === 400 || resp.status === 404) {
        // La sesión se cerró o caducó (p. ej. desde otro dispositivo): abrir una nueva.
        estado.sesion = null;
        sesionId = await asegurarSesion();
        resp = await postSerie(sesionId, payload);
      }
      if (!resp.ok) {
        mostrarToast('No se pudo guardar la serie. Inténtalo de nuevo.');
        return;
      }
      procesarRespuestaSerie(await resp.json(), ej);
    } catch (err) {
      if (esErrorDeRed(err)) {
        const cola = obtenerColaOffline();
        cola.push(payload);
        guardarColaOffline(cola);
        ajustarProgreso(ej.id, +1);
        renderizarFoco();
        mostrarToast('Sin conexión: la serie se enviará al recuperar la red.');
        if (window.FitTrackerCronometro) window.FitTrackerCronometro.iniciar(ej.descanso_segundos);
      } else {
        mostrarToast('No se pudo guardar la serie. Inténtalo de nuevo.');
      }
    } finally {
      estado.guardando = false;
      if (btnGuardarSerie) btnGuardarSerie.disabled = !estado.ejercicioActual;
    }
  }

  function procesarRespuestaSerie(data, ej) {
    const antes = progresoDe(ej.id);
    const serie = {
      id: data.id,
      ejercicio_id: ej.id,
      ejercicio_nombre: ej.nombre,
      peso: data.peso,
      repeticiones: data.repeticiones,
      volumen: data.volumen,
      // La primera serie de un ejercicio genera un PR técnico, pero no hay marca que batir.
      es_pr: Boolean(data.es_pr) && Number(data.peso_anterior) > 0,
    };
    const esPrimeraMarca = Boolean(data.es_pr) && !serie.es_pr;
    estado.sesion.series.push(serie);
    ajustarProgreso(ej.id, +1);

    ej.ultimo_peso = Number(data.peso);
    ej.ultimas_repeticiones = Number(data.repeticiones);
    const item = itemDe(ej.id);
    if (item) {
      item.ultimo_peso = ej.ultimo_peso;
      item.ultimas_repeticiones = ej.ultimas_repeticiones;
    }

    const descanso = Number(data.descanso_segundos) || ej.descanso_segundos || 90;
    if (window.FitTrackerCronometro) window.FitTrackerCronometro.iniciar(descanso);

    estado.serieDeshacible = serie;
    const prefijo = esPrimeraMarca ? 'Primera marca' : 'Serie guardada';
    mostrarToast(`${prefijo} · ${formatearPeso(serie.peso)} kg × ${serie.repeticiones}`, {
      etiqueta: 'Deshacer',
      accion: () => deshacerSerie(serie.id),
    });
    vibrar(30);
    if (serie.es_pr) celebrarNuevoPR(ej.nombre, serie.peso, data.peso_anterior);

    renderizarFoco();
    renderizarPrevio();

    const despues = progresoDe(ej.id);
    if (antes.enRutina && antes.hechas < antes.objetivo && despues.hechas >= despues.objetivo) {
      vibrar([60, 40, 60, 40, 180]);
      setTimeout(() => abrirModalEjercicioTerminado(ej.nombre, despues), 450);
    }
  }

  async function deshacerSerie(serieId) {
    if (!estado.sesion) return;
    try {
      const resp = await fetch(`/api/sesiones/${estado.sesion.id}/series/${serieId}`, { method: 'DELETE' });
      if (!resp.ok) {
        mostrarToast('No se pudo borrar la serie.');
        return;
      }
      const data = await resp.json();
      estado.sesion.series = estado.sesion.series.filter((s) => Number(s.id) !== Number(serieId));
      ajustarProgreso(data.ejercicio_id, -1);
      if (estado.serieDeshacible && Number(estado.serieDeshacible.id) === Number(serieId)) {
        estado.serieDeshacible = null;
        ocultarPR();
        if (window.FitTrackerCronometro) window.FitTrackerCronometro.detener();
      }
      renderizarFoco();
      renderizarPrevio();
      mostrarToast('Serie borrada');
    } catch (_) {
      mostrarToast('Sin conexión: no se pudo borrar la serie.');
    }
  }

  // ------------------------------------------------------------------ cola offline
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
    const n = obtenerColaOffline().length;
    syncBadge.hidden = n === 0;
    syncBadge.textContent = n === 1 ? '1 serie sin enviar' : `${n} series sin enviar`;
  }

  async function sincronizarColaOffline() {
    const cola = obtenerColaOffline();
    if (cola.length === 0 || (typeof navigator !== 'undefined' && navigator.onLine === false)) return;
    const pendientes = [];
    for (const item of cola) {
      try {
        const sesionId = await asegurarSesion();
        const resp = await postSerie(sesionId, item);
        if (!resp.ok) {
          pendientes.push(item);
          continue;
        }
        const data = await resp.json();
        estado.sesion.series.push({
          id: data.id,
          ejercicio_id: item.ejercicio_id,
          ejercicio_nombre: item.ejercicio_nombre,
          peso: data.peso,
          repeticiones: data.repeticiones,
          es_pr: Boolean(data.es_pr),
        });
      } catch (_) {
        pendientes.push(item);
      }
    }
    guardarColaOffline(pendientes);
    renderizarListaSeries();
  }

  // ------------------------------------------------------------------ avisos (toast, PR)
  function mostrarToast(texto, opciones) {
    if (!toastEl || !toastTextoEl) return;
    toastTextoEl.textContent = texto;
    const conAccion = Boolean(opciones && opciones.accion);
    if (toastAccionBtn) {
      toastAccionBtn.hidden = !conAccion;
      toastAccionBtn.textContent = conAccion ? opciones.etiqueta || 'Deshacer' : '';
      toastAccionBtn.onclick = conAccion
        ? () => {
            ocultarToast();
            opciones.accion();
          }
        : null;
    }
    // Fuera del modo foco el dock no se ve: el aviso se muestra igualmente en su lugar.
    if (dockEl && dockEl.hidden) {
      dockEl.hidden = false;
      dockEl.classList.add('is-toast-only');
    }
    toastEl.hidden = false;
    actualizarAlturaDock();
    if (estado.timerToast) clearTimeout(estado.timerToast);
    estado.timerToast = setTimeout(ocultarToast, DURACION_TOAST_MS);
  }

  function ocultarToast() {
    if (estado.timerToast) clearTimeout(estado.timerToast);
    estado.timerToast = null;
    if (toastEl) toastEl.hidden = true;
    if (dockEl && dockEl.classList.contains('is-toast-only')) {
      dockEl.classList.remove('is-toast-only');
      dockEl.hidden = true;
    }
    actualizarAlturaDock();
  }

  function celebrarNuevoPR(nombreEjercicio, peso, pesoAnterior) {
    if (!prBanner) return;
    if (prBannerTexto) prBannerTexto.textContent = nombreEjercicio;
    if (prAntesEl) prAntesEl.textContent = `${formatearPeso(pesoAnterior)} kg`;
    if (prAhoraEl) prAhoraEl.textContent = `${formatearPeso(peso)} kg`;
    prBanner.hidden = false;
    prBanner.classList.remove('is-celebrating');
    if (!prefiereMovimientoReducido()) {
      void prBanner.offsetWidth;
      prBanner.classList.add('is-celebrating');
    }
    vibrar([40, 30, 40, 30, 120]);
    if (estado.timerPR) clearTimeout(estado.timerPR);
    estado.timerPR = setTimeout(ocultarPR, DURACION_PR_MS);
  }

  function ocultarPR() {
    if (estado.timerPR) clearTimeout(estado.timerPR);
    estado.timerPR = null;
    if (prBanner) {
      prBanner.hidden = true;
      prBanner.classList.remove('is-celebrating');
    }
  }

  // ------------------------------------------------------------------ hojas inferiores
  function abrirHoja(el) {
    if (!el) return;
    el.hidden = false;
    document.body.classList.add('has-open-sheet');
  }

  function cerrarHoja(el) {
    if (!el || el.hidden) return;
    el.hidden = true;
    if (!document.querySelector('.bottom-sheet-backdrop:not([hidden])')) {
      document.body.classList.remove('has-open-sheet');
    }
  }

  function abrirSheetCambiar() {
    const items = itemsRutina();
    if (sheetBloqueRutina) sheetBloqueRutina.hidden = items.length === 0;
    if (sheetListaRutina) sheetListaRutina.innerHTML = items.map(filaPlanHtml).join('');
    if (inputBusqueda) {
      inputBusqueda.value = '';
      inputBusqueda.dispatchEvent(new Event('input'));
    }
    abrirHoja(sheetCambiar);
  }

  function abrirModalEjercicioTerminado(nombreEjercicio, progreso) {
    if (!modalTerminadoEl) return;
    const siguiente = siguientePendiente();
    if (modalTerminadoTitulo) modalTerminadoTitulo.textContent = `¡Terminaste ${nombreEjercicio}!`;
    if (modalTerminadoSubtitulo) {
      modalTerminadoSubtitulo.textContent = `${progreso.hechas} de ${progreso.objetivo} series completadas.`;
    }
    if (btnModalSeguirSiguiente) {
      btnModalSeguirSiguiente.textContent = siguiente
        ? `Seguir con ${siguiente.ejercicio_nombre}`
        : 'Terminar entrenamiento';
      btnModalSeguirSiguiente.onclick = () => {
        cerrarHoja(modalTerminadoEl);
        if (siguiente) seleccionarEjercicio(siguiente);
        else finalizarSesionActiva();
      };
    }
    abrirHoja(modalTerminadoEl);
  }

  // ------------------------------------------------------------------ eventos
  function alTocarFilaPlan(contenedor, manejador) {
    if (!contenedor) return;
    contenedor.addEventListener('click', (e) => {
      const fila = e.target.closest('[data-task-ejercicio-id]');
      if (fila) manejador(Number(fila.getAttribute('data-task-ejercicio-id')));
    });
  }

  if (btnEmpezar) btnEmpezar.addEventListener('click', () => empezarEntrenamiento());

  alTocarFilaPlan(listaChecklistEl, (id) => {
    if (estado.sesion) {
      establecerModo('foco');
      seleccionarEjercicio(itemDe(id));
    } else {
      empezarEntrenamiento(id);
    }
  });
  alTocarFilaPlan(sheetListaRutina, (id) => seleccionarEjercicio(itemDe(id)));

  if (tiraDiasEl) {
    tiraDiasEl.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-agenda-fecha]');
      if (btn) cargarAgendaDiaria(btn.getAttribute('data-agenda-fecha'));
    });
  }
  if (btnSemanaAnterior) {
    btnSemanaAnterior.addEventListener('click', () =>
      cargarAgendaDiaria(desplazarFechaDias(estado.agenda && estado.agenda.fecha, -7))
    );
  }
  if (btnSemanaSiguiente) {
    btnSemanaSiguiente.addEventListener('click', () =>
      cargarAgendaDiaria(desplazarFechaDias(estado.agenda && estado.agenda.fecha, 7))
    );
  }
  if (selectorRutina) {
    selectorRutina.addEventListener('change', () => {
      estado.libre = selectorRutina.value === '';
      if (estado.libre) {
        renderizarPrevio();
      } else {
        cargarAgendaDiaria(estado.agenda && estado.agenda.fecha, selectorRutina.value);
      }
    });
  }
  if (switchCompletadosBtn) {
    switchCompletadosBtn.addEventListener('click', () => {
      estado.mostrarCompletados = !estado.mostrarCompletados;
      switchCompletadosBtn.classList.toggle('is-on', estado.mostrarCompletados);
      switchCompletadosBtn.setAttribute('aria-checked', estado.mostrarCompletados ? 'true' : 'false');
      if (switchCompletadosIcon) switchCompletadosIcon.textContent = estado.mostrarCompletados ? '✓' : '✕';
      aplicarVisibilidadChecklist();
    });
  }

  if (btnPesoMenos) {
    btnPesoMenos.addEventListener('click', () => {
      estado.peso = Math.max(0, Math.round((estado.peso - estado.pasoPeso) * 100) / 100);
      actualizarDisplays();
      pulsarValor(valorPesoEl);
    });
  }
  if (btnPesoMas) {
    btnPesoMas.addEventListener('click', () => {
      estado.peso = Math.round((estado.peso + estado.pasoPeso) * 100) / 100;
      actualizarDisplays();
      pulsarValor(valorPesoEl);
    });
  }
  if (btnRepsMenos) {
    btnRepsMenos.addEventListener('click', () => {
      estado.reps = Math.max(1, estado.reps - 1);
      actualizarDisplays();
      pulsarValor(valorRepsEl);
    });
  }
  if (btnRepsMas) {
    btnRepsMas.addEventListener('click', () => {
      estado.reps += 1;
      actualizarDisplays();
      pulsarValor(valorRepsEl);
    });
  }
  chipsPasoPeso.forEach((chip) => {
    vincularFeedbackTactil(chip);
    chip.addEventListener('click', () => {
      estado.pasoPeso = Number(chip.getAttribute('data-weight-step')) || 2.5;
      chipsPasoPeso.forEach((c) => c.classList.toggle('is-active', c === chip));
    });
  });
  [btnPesoMenos, btnPesoMas, btnRepsMenos, btnRepsMas, btnGuardarSerie].forEach(vincularFeedbackTactil);

  if (btnGuardarSerie) btnGuardarSerie.addEventListener('click', registrarSerieActual);
  if (btnFinalizarSesion) btnFinalizarSesion.addEventListener('click', finalizarSesionActiva);
  if (btnCambiarEjercicio) btnCambiarEjercicio.addEventListener('click', abrirSheetCambiar);
  if (btnSiguiente) {
    btnSiguiente.addEventListener('click', () => {
      const siguiente = siguientePendiente();
      if (siguiente) seleccionarEjercicio(siguiente);
    });
  }
  if (listaSeriesEl) {
    listaSeriesEl.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-borrar-serie]');
      if (!btn) return;
      if (window.confirm('¿Borrar esta serie?')) deshacerSerie(Number(btn.getAttribute('data-borrar-serie')));
    });
  }

  // La celebración se cierra sola, con su botón o tocando en cualquier parte.
  if (prBanner) prBanner.addEventListener('click', ocultarPR);
  if (btnCerrarCelebracion) btnCerrarCelebracion.addEventListener('click', ocultarPR);

  if (btnCerrarSheetCambiar) btnCerrarSheetCambiar.addEventListener('click', () => cerrarHoja(sheetCambiar));
  if (btnNuevoEjercicio) {
    btnNuevoEjercicio.addEventListener('click', () => {
      if (window.FitTrackerBuscador) {
        window.FitTrackerBuscador.abrirModalCreacion(inputBusqueda ? inputBusqueda.value.trim() : '');
      }
    });
  }
  if (btnModalDescansoAgua) btnModalDescansoAgua.addEventListener('click', () => cerrarHoja(modalTerminadoEl));
  if (btnCerrarResumen) {
    btnCerrarResumen.addEventListener('click', () => {
      cerrarHoja(modalResumenEl);
      establecerModo('previo');
    });
  }

  // Tocar el fondo oscuro o pulsar Escape cierra la hoja abierta (salvo el resumen final).
  document.querySelectorAll('.bottom-sheet-backdrop').forEach((fondo) => {
    fondo.addEventListener('click', (e) => {
      if (e.target !== fondo) return;
      if (fondo === modalResumenEl) btnCerrarResumen && btnCerrarResumen.click();
      else cerrarHoja(fondo);
    });
  });
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (prBanner && !prBanner.hidden) {
      ocultarPR();
      return;
    }
    const abierta = document.querySelector('.bottom-sheet-backdrop:not([hidden])');
    if (abierta === modalResumenEl) btnCerrarResumen && btnCerrarResumen.click();
    else if (abierta) cerrarHoja(abierta);
  });

  if (dockEl && typeof ResizeObserver === 'function') {
    new ResizeObserver(actualizarAlturaDock).observe(dockEl);
  }
  window.addEventListener('online', sincronizarColaOffline);

  window.FitTrackerRegistro = {
    seleccionarEjercicio,
    registrarSerieActual,
    deshacerSerie,
    celebrarNuevoPR,
    sincronizarColaOffline,
    cargarAgendaDiaria,
    empezarEntrenamiento,
    obtenerEjercicioActual: () => estado.ejercicioActual,
  };

  // ------------------------------------------------------------------ arranque
  document.addEventListener('DOMContentLoaded', () => {
    if (estado.sesion) {
      establecerModo('foco');
      // Retomar el último ejercicio trabajado o el primero pendiente del plan.
      const ultima = estado.sesion.series[estado.sesion.series.length - 1];
      const objetivo = ultima
        ? progresoDe(ultima.ejercicio_id).hechas < progresoDe(ultima.ejercicio_id).objetivo
          ? { id: ultima.ejercicio_id, nombre: ultima.ejercicio_nombre, ultimo_peso: ultima.peso, ultimas_repeticiones: ultima.repeticiones }
          : siguientePendiente() || { id: ultima.ejercicio_id, nombre: ultima.ejercicio_nombre, ultimo_peso: ultima.peso, ultimas_repeticiones: ultima.repeticiones }
        : itemsRutina().find((it) => (Number(it.series_completadas_hoy) || 0) < (Number(it.series_objetivo) || 0));
      if (objetivo) seleccionarEjercicio(objetivo);
      else renderizarFoco();
    } else {
      establecerModo('previo');
    }
    renderizarPrevio();
    actualizarDisplays();
    sincronizarColaOffline();

    // Primera visita (o cambio de zona horaria): el HTML se calculó con el día UTC.
    if (window.ftZonaHorariaNueva) cargarAgendaDiaria(null);
  });
})();
