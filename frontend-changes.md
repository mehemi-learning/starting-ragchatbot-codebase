# Frontend Changes

## Dark / Light Theme Toggle

### Overview
Added a persistent dark/light theme toggle button positioned in the top-right corner of the viewport. The user's preference is saved to `localStorage` and restored on every page load.

---

### Files Modified

#### `frontend/index.html`
- Bumped cache-busting query strings: `style.css?v=10` → `v=11`, `script.js?v=10` → `v=11`.
- Added a `<button id="themeToggle" class="theme-toggle">` element directly inside `<body>`, before `.container`.
  - Contains two inline SVGs: `.icon-sun` (Feather "sun" icon) and `.icon-moon` (Feather "moon" icon).
  - `aria-label="Toggle light/dark theme"` and `title="Toggle theme"` for accessibility.
  - Both SVGs carry `aria-hidden="true"` since the button label is descriptive enough.

#### `frontend/style.css`
Added the following blocks (inserted before the existing "Base Styles" comment):

1. **`[data-theme="light"]` block** — overrides all dark-mode CSS custom properties:
   | Variable | Light value |
   |---|---|
   | `--background` | `#f8fafc` |
   | `--surface` | `#ffffff` |
   | `--surface-hover` | `#f1f5f9` |
   | `--text-primary` | `#1e293b` |
   | `--text-secondary` | `#64748b` |
   | `--border-color` | `#e2e8f0` |
   | `--shadow` | `0 4px 6px -1px rgba(0,0,0,0.1)` |
   | `--welcome-bg` | `#eff6ff` |
   | `--welcome-border` | `#bfdbfe` |
   Primary/accent colours (`--primary-color`, `--primary-hover`, `--user-message`, `--focus-ring`) remain the same blue in both themes.

2. **`.theme-transition *`** — a short-lived rule (applied/removed by JS within 300 ms) that adds `transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease !important` to every element during a theme switch, producing the smooth fade between themes without permanently overriding existing hover/focus transitions.

3. **`.theme-toggle` button styles**:
   - `position: fixed; top: 1rem; right: 1rem; z-index: 1000` — always visible in the top-right corner.
   - Circular (40 × 40 px, `border-radius: 50%`), uses `--surface`, `--border-color`, `--text-secondary`.
   - Hover: scales up 10 % and tints to `--primary-color`.
   - Focus: 3 px `--focus-ring` outline (keyboard-navigable).
   - Active: slight scale-down + 20° rotation for tactile feedback.

4. **Icon visibility rules**:
   - Default (dark mode): `.icon-sun` visible, `.icon-moon` hidden — sun icon signals "switch to light".
   - `[data-theme="light"]`: `.icon-moon` visible, `.icon-sun` hidden — moon icon signals "switch to dark".

5. **Light-mode overrides for hardcoded colours**:
   - `.message-content code` → `rgba(0,0,0,0.06)` background (softer than dark-mode `0.2`).
   - `.message-content pre` → `rgba(0,0,0,0.04)` background.
   - `.message.welcome-message .message-content` → lighter `box-shadow`.

#### `frontend/script.js`
- Added `themeToggle` to the DOM element variables.
- On `DOMContentLoaded`: reads `localStorage.getItem('theme')` and sets `data-theme="light"` on `<html>` before first paint (no flash of wrong theme).
- Registered `click` listener on `themeToggle` → calls `toggleTheme()`.
- **`toggleTheme()` function**:
  1. Adds `.theme-transition` to `<body>` to enable smooth transitions.
  2. Reads current `data-theme` attribute on `<html>`.
  3. Toggles between removing the attribute (dark) and setting `data-theme="light"`.
  4. Persists the choice to `localStorage` under key `"theme"`.
  5. Removes `.theme-transition` after 300 ms via `setTimeout`.

---

### Accessibility
- Button has an `aria-label` and `title` for screen readers and tooltips.
- Button is reachable via keyboard Tab; focus ring is visible.
- Colour contrast in both themes meets WCAG AA standards (dark text on light backgrounds, white text on blue button).
