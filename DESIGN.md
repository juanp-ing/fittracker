# DESIGN.md — Sistema de Diseño Oficial (Light Theme Gamificado de Duolingo)

## 1. Filosofía Visual y UX Mobile-First
FitTracker adopta el **Light Theme Gamificado de Duolingo**: superficies planas blancas (`#ffffff`), alto contraste legible a plena luz del gimnasio, geometría redondeada amigable (`border-radius: 12px`), y botones físicos táctiles tipo sticker/3D con borde inferior de `4px` que descienden `2px` al presionarlos (`:active`).
- **Cero gradientes, cero sombras difusas (`box-shadow` borroso), cero glassmorphism.**
- **Operación en `< 10` segundos sin teclado:** Controles gigantes `−` y `＋` (`min-height: 56px; min-width: 64px;`) operables con el pulgar de una sola mano.

---

## 2. Tokens de Color Oficiales (`:root`)
- `--color-eager-green: #58cc02` — CTAs primarios («¡SERIE TERMINADA!»), serie completada, récord personal (PR) logrado y músculo primario en el mapa SVG.
- `--color-eager-green-shade: #46a302` — Borde inferior 3D (`4px`) de botones primarios verdes.
- `--color-storybook-green: #d7ffb8` — Fondos suaves de énfasis, chips seleccionados y pestaña activa en el Bottom Nav.
- `--color-spark-blue: #1cb0f6` — Acciones secundarias, cronómetro de descanso activo y enlaces.
- `--color-spark-blue-shade: #1899d6` — Borde inferior 3D (`4px`) de botones azules.
- `--color-fresh-leaf: #a5ed6e` — Activación de músculo secundario en el mapa anatómico SVG.
- `--color-night-ink: #000437` — Títulos de alto contraste y números grandes de peso/repeticiones/cronómetro.
- `--color-paper-white: #ffffff` — Superficie principal y fondo de tarjetas.
- `--color-snow-bg: #f7f7f7` — Fondo sutil exterior del contenedor móvil en escritorio.
- `--color-charcoal: #4b4b4b` — Texto de cuerpo principal y etiquetas.
- `--color-pencil-gray: #777777` — Texto secundario, metadatos y subtítulos.
- `--color-faded-gray: #afafaf` — Bordes estructurales (`2px solid`) y estados inactivos.
- `--color-swan-border: #e5e5e5` — Divisores y bordes de tarjetas en reposo.

---

## 3. Tipografía
- **Display y Títulos (`--font-display`):** `'Nunito'`, sans-serif (`font-weight: 800` / `900`) — sustituto web de `feather`.
- **Cuerpo y Controles (`--font-sans`):** `'Nunito Sans'`, sans-serif (`font-weight: 500` / `700`) — sustituto web de `duolingo-sans`.
- **Números Tabulares:** `font-variant-numeric: tabular-nums` en contadores de peso (`kg`), repeticiones y cronómetro (`MM:SS`) para evitar saltos horizontales al tocar `−` / `＋`.

---

## 4. Arquitectura del Mobile Viewport Shell
- Contenedor `.mobile-shell` con `max-width: 430px; min-height: 100dvh; margin: 0 auto; background: var(--color-paper-white);`.
- `touch-action: manipulation;` y `-webkit-tap-highlight-color: transparent;` en todos los controles interactivos.
- **Bottom Navigation Bar fija (`min-height: 64px`)** con 4 pestañas de acceso directo (`min-height: 56px`):
  1. **Hoy (Entrenar)**
  2. **Rutinas**
  3. **Mapa/PRs**
  4. **Resumen 30d**
