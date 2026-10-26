/**
 * cronometro.js — Cronómetro de descanso exacto por diferencia de timestamps Date.now() (RF-12).
 */
(function () {
  const TIMER_STORAGE_KEY = 'fittracker_rest_timer_end';
  let intervalId = null;

  const bannerEl = document.getElementById('cronometro-banner');
  const relojEl = document.getElementById('cronometro-reloj');
  const estadoTextoEl = document.getElementById('cronometro-estado-texto');
  const btnMas15 = document.getElementById('btn-timer-mas15');
  const btnMenos15 = document.getElementById('btn-timer-menos15');
  const btnSaltar = document.getElementById('btn-timer-saltar');

  function formatearSegundos(totalSegundos) {
    const seg = Math.max(0, Math.floor(totalSegundos));
    const minutos = String(Math.floor(seg / 60)).padStart(2, '0');
    const resto = String(seg % 60).padStart(2, '0');
    return `${minutos}:${resto}`;
  }

  function iniciar(segundos) {
    const duracion = Math.max(1, Number(segundos) || 90);
    const endTime = Date.now() + duracion * 1000;
    localStorage.setItem(TIMER_STORAGE_KEY, String(endTime));

    if (bannerEl) {
      bannerEl.hidden = false;
      bannerEl.classList.remove('is-finished');
    }
    if (estadoTextoEl) {
      estadoTextoEl.textContent = 'Tiempo de descanso activo';
    }
    ejecutarTick();
    if (intervalId) clearInterval(intervalId);
    intervalId = setInterval(ejecutarTick, 250);
  }

  function ajustarSegundos(deltaSegundos) {
    const guardado = Number(localStorage.getItem(TIMER_STORAGE_KEY));
    if (!guardado) return;
    const nuevoFin = Math.max(Date.now(), guardado + deltaSegundos * 1000);
    localStorage.setItem(TIMER_STORAGE_KEY, String(nuevoFin));
    ejecutarTick();
  }

  function detener() {
    localStorage.removeItem(TIMER_STORAGE_KEY);
    if (intervalId) {
      clearInterval(intervalId);
      intervalId = null;
    }
    if (bannerEl) {
      bannerEl.hidden = true;
    }
  }

  function ejecutarTick() {
    const fin = Number(localStorage.getItem(TIMER_STORAGE_KEY));
    if (!fin) {
      if (intervalId) clearInterval(intervalId);
      return;
    }

    const restantes = Math.ceil((fin - Date.now()) / 1000);
    if (restantes > 0) {
      if (relojEl) relojEl.textContent = formatearSegundos(restantes);
      if (bannerEl) bannerEl.hidden = false;
    } else {
      if (relojEl) relojEl.textContent = '00:00';
      localStorage.removeItem(TIMER_STORAGE_KEY);
      if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      }
      if (bannerEl) {
        bannerEl.hidden = false;
        bannerEl.classList.add('is-finished');
      }
      if (estadoTextoEl) {
        estadoTextoEl.textContent = '¡Descanso terminado! A por la siguiente serie';
      }
      if (typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function') {
        navigator.vibrate([200, 100, 200]);
      }
    }
  }

  if (btnMas15) {
    btnMas15.addEventListener('click', () => ajustarSegundos(15));
  }
  if (btnMenos15) {
    btnMenos15.addEventListener('click', () => ajustarSegundos(-15));
  }
  if (btnSaltar) {
    btnSaltar.addEventListener('click', detener);
  }

  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) ejecutarTick();
  });

  window.FitTrackerCronometro = {
    iniciar,
    ajustarSegundos,
    detener,
  };

  document.addEventListener('DOMContentLoaded', () => {
    const fin = Number(localStorage.getItem(TIMER_STORAGE_KEY));
    if (fin && fin > Date.now()) {
      if (bannerEl) bannerEl.hidden = false;
      ejecutarTick();
      intervalId = setInterval(ejecutarTick, 250);
    }
  });
})();

