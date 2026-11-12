/**
 * graficas.js — Gráficas de progreso con Chart.js y tarjetas del Resumen Mensual 30d (RF-14, RF-15).
 */
(function () {
  let instanciaChart = null;
  // Peso (~60 kg) y volumen de la mejor serie (~600 kg) no caben en el mismo eje:
  // se muestra una métrica cada vez y el usuario la cambia con el control segmentado.
  let metricaProgreso = 'peso';
  let ultimoProgreso = null;

  const METRICAS = {
    peso: { campo: 'pesos_maximos', nombre: 'Peso máximo', color: '#58cc02', relleno: 'rgba(88, 204, 2, 0.12)' },
    volumen: { campo: 'volumenes', nombre: 'Mejor serie', color: '#1cb0f6', relleno: 'rgba(28, 176, 246, 0.12)' },
  };

  /** '2026-10-02' → '2 oct' (sin desfase de zona: se fija el mediodía local). */
  function formatearFechaCorta(iso, conAnio = false) {
    const fecha = new Date(`${iso}T12:00:00`);
    if (Number.isNaN(fecha.getTime())) return iso;
    const opciones = { day: 'numeric', month: 'short' };
    if (conAnio) opciones.year = 'numeric';
    return fecha.toLocaleDateString('es', opciones).replace(/\./g, '');
  }

  function formatearNumero(valor) {
    const n = Number(valor) || 0;
    return n.toLocaleString('es', { maximumFractionDigits: 2 });
  }

  function pintarGraficaProgreso() {
    const canvas = document.getElementById('grafica-progreso-canvas');
    const contenedor = document.getElementById('progreso-grafica');
    const vacioEl = document.getElementById('progreso-vacio');
    const data = ultimoProgreso;
    if (!canvas || !data) return;

    const fechas = data.fechas || [];
    if (instanciaChart) {
      instanciaChart.destroy();
      instanciaChart = null;
    }
    const metricasEl = document.getElementById('progreso-metricas');
    if (metricasEl) metricasEl.hidden = !fechas.length;
    if (!fechas.length) {
      if (contenedor) contenedor.hidden = true;
      if (vacioEl) {
        vacioEl.textContent = `Aún no registraste series de ${data.ejercicio_nombre || 'este ejercicio'}. Cuando lo hagas, aquí verás cómo evoluciona.`;
        vacioEl.hidden = false;
      }
      return;
    }
    if (contenedor) contenedor.hidden = false;
    if (vacioEl) vacioEl.hidden = true;
    if (typeof window.Chart === 'undefined') return;

    const metrica = METRICAS[metricaProgreso];
    const valores = data[metrica.campo] || [];
    const puntos = data.puntos || [];
    const estilos = getComputedStyle(document.documentElement);
    const fuente = estilos.getPropertyValue('--font-sans').trim() || 'sans-serif';
    const tinta = estilos.getPropertyValue('--color-charcoal').trim() || '#4b4b4b';
    const rejilla = estilos.getPropertyValue('--color-border-light').trim() || '#e5e5e5';

    instanciaChart = new window.Chart(canvas.getContext('2d'), {
      type: 'line',
      data: {
        labels: fechas.map((f) => formatearFechaCorta(f)),
        datasets: [
          {
            label: metrica.nombre,
            data: valores,
            borderColor: metrica.color,
            backgroundColor: metrica.relleno,
            fill: true,
            borderWidth: 3,
            pointRadius: fechas.length > 20 ? 0 : 4,
            pointHoverRadius: 6,
            pointBackgroundColor: metrica.color,
            tension: 0.25,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: (items) => formatearFechaCorta(fechas[items[0].dataIndex], true),
              label: (item) => {
                const punto = puntos[item.dataIndex] || {};
                if (metricaProgreso === 'peso') {
                  return ` ${formatearNumero(item.parsed.y)} kg × ${punto.repeticiones || '?'} reps`;
                }
                return ` ${formatearNumero(item.parsed.y)} kg movidos en una serie`;
              },
            },
          },
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: {
              color: tinta,
              font: { family: fuente, weight: '700', size: 12 },
              maxRotation: 0,
              autoSkip: true,
              maxTicksLimit: 5,
            },
          },
          y: {
            grace: '10%',
            grid: { color: rejilla },
            border: { display: false },
            ticks: {
              color: tinta,
              font: { family: fuente, weight: '700', size: 12 },
              maxTicksLimit: 5,
              callback: (valor) => `${formatearNumero(valor)} kg`,
            },
          },
        },
      },
    });
  }

  async function cargarProgresoEjercicio(ejercicioId) {
    const prBadgeEl = document.getElementById('progreso-pr-historico');
    if (!ejercicioId) return;

    try {
      const resp = await fetch(`/api/progreso/${encodeURIComponent(ejercicioId)}`, {
        headers: { Accept: 'application/json' },
      });
      if (!resp.ok) return;
      ultimoProgreso = await resp.json();

      if (prBadgeEl) {
        const pr = Number(ultimoProgreso.pr_historico) || 0;
        prBadgeEl.textContent = `Récord: ${formatearNumero(pr)} kg`;
        prBadgeEl.hidden = pr <= 0;
      }
      pintarGraficaProgreso();
    } catch (err) {
      console.warn('No se pudo renderizar la gráfica de progreso:', err);
    }
  }

  document.querySelectorAll('[data-metrica-progreso]').forEach((btn) => {
    btn.addEventListener('click', () => {
      metricaProgreso = btn.getAttribute('data-metrica-progreso');
      document.querySelectorAll('[data-metrica-progreso]').forEach((b) => {
        const activa = b === btn;
        b.classList.toggle('is-active', activa);
        b.setAttribute('aria-pressed', activa ? 'true' : 'false');
      });
      pintarGraficaProgreso();
    });
  });

  function escapeHtml(str) {
    return String(str == null ? '' : str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function formatearKg(valor) {
    return `${Math.round(Number(valor) || 0).toLocaleString('es')} kg`;
  }

  function formatearPeso(valor) {
    const n = Number(valor) || 0;
    return Number.isInteger(n) ? String(n) : String(Math.round(n * 100) / 100);
  }

  /** Texto y tono de la comparación con el mes anterior. */
  function pintarDelta(el, actual, previo, unidad) {
    if (!el) return;
    el.classList.remove('is-up', 'is-down');
    if (!previo) {
      el.textContent = 'Primer mes';
      return;
    }
    const diferencia = actual - previo;
    if (diferencia === 0) {
      el.textContent = 'Igual';
      return;
    }
    el.classList.add(diferencia > 0 ? 'is-up' : 'is-down');
    el.textContent = `${diferencia > 0 ? '▲' : '▼'} ${Math.abs(diferencia).toLocaleString('es')}${unidad} ${diferencia > 0 ? 'más' : 'menos'}`;
  }

  async function cargarResumenMensual() {
    const contenedorResumen = document.getElementById('resumen-mensual-contenedor');
    if (!contenedorResumen) return;

    try {
      const resp = await fetch('/api/resumen-mensual', {
        headers: { Accept: 'application/json' },
      });
      if (!resp.ok) return;
      const data = await resp.json();
      const comparativa = data.comparativa || {};
      const hayDatos = Number(data.total_series) > 0;

      document.getElementById('resumen-vacio').hidden = hayDatos;
      document.getElementById('resumen-datos').hidden = !hayDatos;
      contenedorResumen.setAttribute('aria-busy', 'false');
      if (!hayDatos) return;

      document.getElementById('kpi-volumen-total').textContent = formatearKg(data.volumen_total_kg);
      document.getElementById('kpi-total-sesiones').textContent = String(data.total_sesiones || 0);
      document.getElementById('kpi-total-series').textContent = String(data.total_series || 0);
      document.getElementById('kpi-nuevos-prs').textContent = String(data.nuevos_prs || 0);

      const deltaVolumen = document.getElementById('kpi-volumen-delta');
      deltaVolumen.classList.remove('is-up', 'is-down');
      if (comparativa.variacion_volumen_pct === null || comparativa.variacion_volumen_pct === undefined) {
        deltaVolumen.textContent = 'Primer mes con datos';
      } else if (comparativa.variacion_volumen_pct === 0) {
        // El porcentaje llega redondeado: 0 % no siempre significa volumen idéntico.
        deltaVolumen.textContent =
          Number(data.volumen_total_kg) === Number(comparativa.volumen_kg)
            ? 'Igual que el mes anterior'
            : 'Casi igual que el mes anterior (menos de 1 %)';
      } else {
        const sube = comparativa.variacion_volumen_pct > 0;
        deltaVolumen.classList.add(sube ? 'is-up' : 'is-down');
        deltaVolumen.textContent = `${sube ? '▲' : '▼'} ${Math.abs(comparativa.variacion_volumen_pct)} % vs mes anterior`;
      }
      pintarDelta(document.getElementById('kpi-sesiones-delta'), data.total_sesiones || 0, comparativa.sesiones || 0, '');
      pintarDelta(document.getElementById('kpi-series-delta'), data.total_series || 0, comparativa.series || 0, '');

      const primeras = Number(data.primeras_marcas) || 0;
      document.getElementById('kpi-prs-nota').textContent =
        primeras > 0 ? `+${primeras} ${primeras === 1 ? 'estreno' : 'estrenos'}` : '';
      const notaPrimeras = document.getElementById('nota-primeras-marcas');
      notaPrimeras.hidden = primeras === 0;
      notaPrimeras.textContent =
        primeras === 1
          ? 'Además estrenaste 1 ejercicio: su primera marca será tu referencia para batir.'
          : `Además estrenaste ${primeras} ejercicios: sus primeras marcas serán tu referencia para batir.`;

      renderizarListaPRs(document.getElementById('lista-prs-mes'), data.prs_detalle || []);
      renderizarListaClasificacion(
        document.getElementById('lista-ejercicios-mejorados'),
        data.ejercicios_mejorados || [],
        'MEJORO'
      );
      renderizarListaClasificacion(
        document.getElementById('lista-ejercicios-estancados'),
        data.ejercicios_estancados || [],
        'ESTANCADO'
      );
    } catch (err) {
      console.warn('Error cargando resumen mensual:', err);
    }
  }

  function renderizarListaClasificacion(el, items, tipo) {
    if (!el) return;
    if (!items.length) {
      el.innerHTML = `<li class="plain-list__empty">${
        tipo === 'MEJORO'
          ? 'Cuando superes el peso del mes anterior en un ejercicio, aparecerá aquí.'
          : 'Ninguno: todo lo que entrenas sigue avanzando.'
      }</li>`;
      return;
    }
    el.innerHTML = items
      .map((item) => {
        const detalle = item.max_peso_previo
          ? `${formatearPeso(item.max_peso_previo)} → ${formatearPeso(item.max_peso_actual)} kg`
          : `${formatearPeso(item.max_peso_actual)} kg`;
        return `
        <li class="plain-list__row">
          <span class="plain-list__main">
            <strong>${escapeHtml(item.nombre)}</strong>
            <span>${item.sesiones_actual} sesiones este mes</span>
          </span>
          <span class="plain-list__value ${tipo === 'MEJORO' ? 'is-up' : ''}">${detalle}</span>
        </li>`;
      })
      .join('');
  }

  function renderizarListaPRs(el, prs) {
    if (!el) return;
    if (!prs.length) {
      el.innerHTML =
        '<li class="plain-list__empty">Sin récords todavía. Sube un poco el peso en tu próxima sesión.</li>';
      return;
    }
    el.innerHTML = prs
      .map(
        (pr) => `
        <li class="plain-list__row">
          <span class="plain-list__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M8 4h8v5a4 4 0 01-8 0V4zM8 6H4v1a3 3 0 003 3M16 6h4v1a3 3 0 01-3 3M12 13v4M8 20h8"/></svg>
          </span>
          <span class="plain-list__main">
            <strong>${escapeHtml(pr.ejercicio_nombre)}</strong>
            <span>Peso máximo</span>
          </span>
          <span class="plain-list__value is-up">${formatearPeso(pr.peso)} kg</span>
        </li>`
      )
      .join('');
  }

  const selectorEjercicioGrafica = document.getElementById('selector-ejercicio-progreso');
  if (selectorEjercicioGrafica) {
    selectorEjercicioGrafica.addEventListener('change', (e) => {
      cargarProgresoEjercicio(e.target.value);
    });
  }

  window.FitTrackerGraficas = {
    cargarProgresoEjercicio,
    cargarResumenMensual,
  };

  document.addEventListener('DOMContentLoaded', () => {
    if (selectorEjercicioGrafica && selectorEjercicioGrafica.value) {
      cargarProgresoEjercicio(selectorEjercicioGrafica.value);
    }
    if (document.getElementById('resumen-mensual-contenedor')) {
      cargarResumenMensual();
    }
  });
})();
