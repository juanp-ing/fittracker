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

  async function cargarResumenMensual() {
    const contenedorResumen = document.getElementById('resumen-mensual-contenedor');
    if (!contenedorResumen) return;

    try {
      const resp = await fetch('/api/resumen-mensual', {
        headers: { Accept: 'application/json' },
      });
      if (!resp.ok) return;
      const data = await resp.json();

      const kpiSesiones = document.getElementById('kpi-total-sesiones');
      const kpiSeries = document.getElementById('kpi-total-series');
      const kpiVolumen = document.getElementById('kpi-volumen-total');
      const kpiPrs = document.getElementById('kpi-nuevos-prs');

      if (kpiSesiones) kpiSesiones.textContent = String(data.total_sesiones || 0);
      if (kpiSeries) kpiSeries.textContent = String(data.total_series || 0);
      if (kpiVolumen) kpiVolumen.textContent = `${Math.round(data.volumen_total_kg || 0)} kg`;
      if (kpiPrs) kpiPrs.textContent = String(data.nuevos_prs || 0);

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
      renderizarListaPRs(
        document.getElementById('lista-prs-mes'),
        data.prs_detalle || []
      );
    } catch (err) {
      console.warn('Error cargando resumen mensual:', err);
    }
  }

  function renderizarListaClasificacion(el, items, tipo) {
    if (!el) return;
    if (!items.length) {
      el.innerHTML = `<p style="color:var(--color-charcoal); font-weight:700; margin:0;">Sin ejercicios en esta categoría este mes.</p>`;
      return;
    }
    const badgeClass =
      tipo === 'MEJORO' ? 'status-badge--mejoro' : 'status-badge--estancado';
    const badgeTexto = tipo === 'MEJORO' ? '¡MEJORÓ!' : 'ESTANCADO';

    el.innerHTML = items
      .map(
        (item) => `
        <div class="duo-card" style="display:flex; justify-content:space-between; align-items:center; padding:0.7rem 0.9rem;">
          <div>
            <strong style="font-family:var(--font-display); color:var(--color-night-ink);">${item.nombre}</strong>
            <div style="font-size:0.82rem; font-weight:700; color:var(--color-charcoal);">
              Actual: ${item.max_peso_actual} kg · Previo: ${item.max_peso_previo} kg (${item.sesiones_actual} sesiones)
            </div>
          </div>
          <span class="status-badge ${badgeClass}">${badgeTexto}</span>
        </div>
      `
      )
      .join('');
  }

  function renderizarListaPRs(el, prs) {
    if (!el) return;
    if (!prs.length) {
      el.innerHTML = `<p style="color:var(--color-charcoal); font-weight:700; margin:0;">Aún no hay récords registrados en los últimos 30 días.</p>`;
      return;
    }
    el.innerHTML = prs
      .map(
        (pr) => `
        <div class="duo-card duo-card--highlight" style="display:flex; justify-content:space-between; align-items:center; padding:0.7rem 0.9rem;">
          <div>
            <strong style="font-family:var(--font-display); color:var(--color-night-ink);">${pr.ejercicio_nombre}</strong>
            <div style="font-size:0.82rem; font-weight:700; color:var(--color-charcoal);">
              Récord de Peso Máximo
            </div>
          </div>
          <span class="status-badge status-badge--mejoro">${pr.peso} KG</span>
        </div>
      `
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
