/**
 * graficas.js — Gráficas de progreso con Chart.js y tarjetas del Resumen Mensual 30d (RF-14, RF-15).
 */
(function () {
  let instanciaChart = null;

  async function cargarProgresoEjercicio(ejercicioId) {
    const canvas = document.getElementById('grafica-progreso-canvas');
    const prBadgeEl = document.getElementById('progreso-pr-historico');
    if (!canvas || !ejercicioId) return;

    try {
      const resp = await fetch(`/api/progreso/${encodeURIComponent(ejercicioId)}`, {
        headers: { Accept: 'application/json' },
      });
      if (!resp.ok) return;
      const data = await resp.json();

      if (prBadgeEl) {
        prBadgeEl.textContent = `PR Histórico: ${data.pr_historico || 0} kg`;
      }

      if (typeof window.Chart === 'undefined') return;
      if (instanciaChart) {
        instanciaChart.destroy();
      }

      instanciaChart = new window.Chart(canvas.getContext('2d'), {
        type: 'line',
        data: {
          labels: data.fechas || [],
          datasets: [
            {
              label: 'Peso Máximo (kg)',
              data: data.pesos_maximos || [],
              borderColor: '#58cc02',
              backgroundColor: '#d7ffb8',
              borderWidth: 3,
              pointRadius: 5,
              pointBackgroundColor: '#58cc02',
              tension: 0.2,
            },
            {
              label: 'Volumen Máx Serie (kg)',
              data: data.volumenes || [],
              borderColor: '#1cb0f6',
              backgroundColor: '#ffffff',
              borderWidth: 3,
              pointRadius: 4,
              pointBackgroundColor: '#1cb0f6',
              tension: 0.2,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              labels: {
                color: '#000437',
                font: { family: 'Nunito', weight: '800' },
              },
            },
          },
          scales: {
            x: { ticks: { color: '#4b4b4b', font: { weight: '700' } } },
            y: { ticks: { color: '#4b4b4b', font: { weight: '700' } } },
          },
        },
      });
    } catch (err) {
      console.warn('No se pudo renderizar la gráfica de progreso:', err);
    }
  }

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
