# DESIGN.md — Sistema de Diseño Oficial (Tema Gamificado de Duolingo, claro y oscuro)

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
- `--color-pencil-gray: #737373` — Texto secundario, metadatos y subtítulos (4,74:1 sobre blanco, cumple AA; antes #777777, que daba 4,48:1).
- `--color-faded-gray: #afafaf` — Bordes estructurales (`2px solid`) y estados inactivos.
- `--color-swan-border: #e5e5e5` — Divisores y bordes de tarjetas en reposo.

- `--color-on-accent: #ffffff` — Texto sobre botones de color (verde, azul, rojo). **No usar `--color-paper-white` como color de texto:** es la superficie y en oscuro se vuelve casi negra.
- `--color-overlay` — Fondo que oscurece la pantalla tras una hoja inferior.

### 2.1 Tema oscuro (paleta oscura de Duolingo)
Se redefinen **los mismos tokens**; los componentes no cambian. Se activa con `prefers-color-scheme: dark` (opción «Automático», por defecto) o forzado con `data-theme="dark"`/`"light"` en `<html>`, que fija un script en el `<head>` de `base.html` antes de cargar el CSS (sin destello). La elección se guarda en `localStorage['fittracker_tema']` desde **Perfil → Apariencia**.

| Token | Claro | Oscuro |
|---|---|---|
| `--color-paper-white` (superficie) | `#ffffff` | `#131f24` |
| `--color-surface-muted` | `#f7f7f7` | `#202f36` |
| `--color-night-ink` (títulos) | `#000437` | `#f1f7fb` |
| `--color-charcoal` (cuerpo) | `#4b4b4b` | `#dce6ec` |
| `--color-pencil-gray` | `#737373` | `#8fa3ad` |
| `--color-faded-gray` / `--color-border-light` | `#afafaf` / `#e5e5e5` | `#37464f` |
| `--color-eager-green` / `-shade` | `#58cc02` / `#46a302` | `#93d333` / `#79b933` |
| `--color-fresh-leaf` (secundario) | `#a5ed6e` | `#3f6e1e` |
| `--color-storybook-green` | `#d7ffb8` | `#24391a` |
| `--color-spark-blue` / `-shade` | `#1cb0f6` / `#1899d6` | `#49c0f8` / `#1cb0f6` |
| `--color-danger-red` / `-shade` | `#ff4b4b` / `#ea2b2b` | `#ff6b6b` / `#ee5555` |
| `--color-on-accent` | `#ffffff` | `#131f24` (texto oscuro sobre botón, como Duolingo) |

En oscuro todos los textos de las pantallas principales pasan WCAG AA (comprobado el 2026-11-18). Al añadir un color nuevo, decláralo en `:root` **y** en los dos bloques oscuros de `styles.css` (una prueba exige que coincidan).

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
