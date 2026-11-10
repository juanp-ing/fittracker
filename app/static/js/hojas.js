/**
 * FitTracker — Gesto de arrastre para cerrar las hojas inferiores.
 *
 * El asa gris (.sheet-handle) invita a tirar de la hoja hacia abajo. Al soltarla más allá
 * del umbral se cierra reutilizando el cierre de cada pantalla (el mismo que al tocar el
 * fondo oscuro); si no, la hoja vuelve a su sitio.
 */
(function () {
  'use strict';

  const UMBRAL_CIERRE_PX = 90;
  let arrastre = null;

  function soltar(cerrar) {
    if (!arrastre) return;
    const { hoja, fondo, asa } = arrastre;
    arrastre = null;
    asa.classList.remove('is-dragging');

    if (cerrar) {
      // Cada pantalla ya cierra su hoja al tocar el fondo: se reutiliza ese camino.
      fondo.dispatchEvent(new MouseEvent('click', { bubbles: true }));
      hoja.style.transition = '';
      hoja.style.transform = '';
      hoja.style.animation = '';
      return;
    }
    hoja.style.transition = 'transform 160ms ease-out';
    hoja.style.transform = '';
  }

  document.addEventListener('pointerdown', (e) => {
    const asa = e.target.closest && e.target.closest('.sheet-handle');
    if (!asa) return;
    const hoja = asa.closest('.bottom-sheet');
    const fondo = hoja && hoja.closest('.bottom-sheet-backdrop');
    if (!fondo) return;

    arrastre = { asa, hoja, fondo, inicioY: e.clientY, deltaY: 0, punteroId: e.pointerId };
    asa.classList.add('is-dragging');
    if (asa.setPointerCapture) asa.setPointerCapture(e.pointerId);
    // La animación de entrada fija transform; se anula para que la hoja siga al dedo.
    hoja.style.animation = 'none';
    hoja.style.transition = 'none';
  });

  document.addEventListener('pointermove', (e) => {
    if (!arrastre || e.pointerId !== arrastre.punteroId) return;
    arrastre.deltaY = Math.max(0, e.clientY - arrastre.inicioY);
    arrastre.hoja.style.transform = `translateY(${arrastre.deltaY}px)`;
  });

  document.addEventListener('pointerup', (e) => {
    if (!arrastre || e.pointerId !== arrastre.punteroId) return;
    soltar(arrastre.deltaY > UMBRAL_CIERRE_PX);
  });

  document.addEventListener('pointercancel', (e) => {
    if (!arrastre || e.pointerId !== arrastre.punteroId) return;
    soltar(false);
  });
})();
