# Modo oscuro de FitTracker

> Estado: **implementado** (2026-11-18) en una versión simplificada.
> El tema y sus tokens se documentan en `DESIGN.md` §2.1. Esto es el registro de decisiones.

## Decisiones

- **Paleta:** la oscura de Duolingo (fondo `#131f24`, superficies `#202f36`, bordes `#37464f`,
  texto `#f1f7fb`, verde `#93d333`, azul `#49c0f8`). La app sigue el sistema visual de
  Duolingo, así que se copia su tema oscuro en vez de diseñar uno propio.
- **Texto sobre botones de color:** en oscuro es tinta oscura (`#131f24`), como en Duolingo:
  9,29:1 sobre el verde. En claro se queda blanco (2,09:1); ver «Pendiente».
- **Activación:** *Automático* por defecto (`prefers-color-scheme`), forzable en
  **Perfil → Apariencia** (Automático · Claro · Oscuro). Se guarda en
  `localStorage['fittracker_tema']`, por dispositivo. Un script en el `<head>` fija
  `data-theme` antes de cargar el CSS, así que no hay destello.

## Qué se hizo (y qué se simplificó respecto al primer plan)

El primer plan proponía cuatro PR y una capa nueva de tokens semánticos. Bastó con algo menor:

1. **Se mantienen los tokens actuales y se redefinen en oscuro.** El único con doble uso era
   `--color-paper-white`, que hacía de superficie y de texto sobre botones. Esos 13 usos de
   texto pasan a un token nuevo, `--color-on-accent`. Los fondos tras las hojas pasan a
   `--color-overlay`.
2. **Mapa muscular:** no hizo falta reescribir sus 149 colores. La silueta gris clara se lee
   bien sobre fondo oscuro y las cajas de nombre son blancas con texto oscuro en ambos temas.
   Solo los títulos «VISTA …» y las líneas guía pasan a `--color-night-ink` desde CSS.
3. **Gráfica:** `graficas.js` lee el color de la línea del token del tema.
4. **`color-scheme`** en `:root`, para que los controles nativos (selects, teclado) también se
   vean oscuros; y dos `<meta name="theme-color">`, una por tema.

## Verificación

- Pruebas: `tests/integration/test_modo_oscuro.py`. Comprueba que los bloques automático y
  forzado declaran los mismos tokens, que ningún texto usa `paper-white`, que el script de tema
  va antes del CSS y que existe el selector en Perfil.
- Navegador (Chromium a 390×844, `prefers-color-scheme` emulado):
  - Capturas de Hoy, modo foco, Rutinas, famosas, hoja de rutina, Tu mes, mapa (con nombres),
    hoja de músculo, gráfica, Perfil y onboarding.
  - Escaneo de contraste de todos los textos visibles: en oscuro todos pasan AA.
  - Selector: forzar claro con el sistema en oscuro, forzar oscuro con el sistema en claro,
    volver a Automático, y comprobar que la elección persiste al navegar.

## Pendiente (fuera de este cambio)

- **Contraste del tema claro:** el escaneo marcó textos bajo AA que ya existían, todos de la
  paleta de Duolingo: verde `#58cc02` sobre blanco (2,09), verde `#46a302` como texto (3,23),
  azul `#1899d6` como texto (3,20) y blanco sobre los botones verdes (2,09) y azules (2,44).
  Arreglarlo cambia la marca, así que lo decide el usuario.
- Guardar el tema en la cuenta (hoy es por dispositivo).
