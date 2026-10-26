# DESIGN.md — Sistema de Diseño y Reglas UI/UX para FitTracker Web App

## 1. Principio Rector (Regla de Oro UX)
FitTracker está diseñada para registrar una serie de gimnasio (peso y repeticiones) en **menos de 10 segundos** usando **una sola mano (pulgar)** y **sin abrir el teclado virtual del móvil**.
- **Cero recargas de página:** Todas las acciones de entrenamiento usan `fetch` asíncrono.
- **Zonas táctiles (Thumb-Zone):** Todo botón interactivo durante el entrenamiento (`+/-`, `Guardar Serie`, controles de cronómetro) debe tener un área mínima de `48px × 48px` (`min-height: 3rem`).

---

## 2. Dirección Estética y Paleta de Colores (Dark Athletic UI)
- **Fondo Principal (`--bg-primary`):** `#0B0F17` (Obsidian Gym Dark — máximo contraste bajo luces de gimnasio y ahorro de batería OLED).
- **Superficie / Tarjetas (`--bg-surface`):** `#151C28` con borde sutil `#232F42`.
- **Superficie Elevada (`--bg-elevated`):** `#1E293B`.
- **Texto Primario (`--text-primary`):** `#F8FAFC` (números tabulares `font-variant-numeric: tabular-nums` para peso, repeticiones y cronómetro).
- **Texto Secundario (`--text-secondary`):** `#94A3B8`.
- **Acento Primario / Acción (`--accent-primary`):** `#10B981` (Emerald Energy — acción principal de registrar serie y músculo primario activo).
- **Acento Secundario / Músculo Secundario (`--accent-secondary`):** `#F59E0B` (Amber — activación muscular secundaria y alertas de descanso).
- **Récord Personal (`--accent-pr`):** `#8B5CF6` / `#FACC15` (insignia destacada de Nuevo PR).
- **Peligro / Finalizar (`--danger`):** `#EF4444`.

---

## 3. Tipografía y Escala Numérica
- **Fuente UI:** `Inter`, `system-ui`, `-apple-system`, sans-serif.
- **Números Tabulares (`tabular-nums`):** Obligatorios en contadores de peso (`kg`), repeticiones, volumen y cronómetro (`MM:SS`) para evitar saltos de layout al pulsar `+/-`.
- **Tamaños clave:**
  - Display de Cronómetro / Peso Activo: `2rem` – `2.5rem` (`font-weight: 800`).
  - Botones `+/-`: `1.5rem` (`font-weight: 700`).
  - Títulos de Sección: `1.25rem` (`font-weight: 700`).
  - Cuerpo / Etiquetas: `0.9375rem` (`15px`).

---

## 4. Componentes Críticos Mobile-First
1. **Control Stepper Sin Teclado (`+/-`):**
   - Precarga automática con el último peso y repeticiones registrados por el usuario en ese ejercicio.
   - Botones de incremento/decremento rápido (`-2.5`, `+2.5` kg para peso; `-1`, `+1` para repeticiones) al alcance del pulgar.
2. **Cronómetro Flotante Persistente (`localStorage`):**
   - Se activa automáticamente al guardar una serie con el `descanso_segundos` configurado.
   - Botones rápidos `+15s`, `-15s` y `Saltar` sin bloquear la navegación.
3. **Mapa Muscular Anatómico SVG (Vista Frontal y Posterior):**
   - Coloreado dinámico:
     - Músculo primario (`es_primario = true`): `--accent-primary` (`#10B981`).
     - Músculo secundario (`es_primario = false`): `--accent-secondary` (`#F59E0B`).
     - Sin actividad: `#1E293B`.
4. **Barra de Navegación Inferior (Bottom Tab Bar):**
   - Fija en la parte inferior del viewport móvil (`Entrenar`, `Rutinas`, `Ejercicios`, `Progreso / Resumen`).

