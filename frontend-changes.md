# Frontend Changes: Code Quality Tooling

## Summary

Added Prettier as an automatic code formatter for the frontend (HTML, CSS, JavaScript), providing the frontend equivalent of black for Python. This enforces consistent formatting across all frontend files and gives developers scripts to check or auto-fix formatting.

---

## New Files

### `frontend/.prettierrc`
Prettier configuration file. Key settings:
- `printWidth: 100` — wraps lines longer than 100 characters (mirrors black's default line length)
- `tabWidth: 4` — 4-space indentation matching the existing codebase style
- `singleQuote: true` — single quotes for JS strings
- `trailingComma: "es5"` — trailing commas where valid in ES5
- `endOfLine: "lf"` — consistent LF line endings

### `frontend/.prettierignore`
Tells Prettier to skip `node_modules/` and `package-lock.json`.

### `frontend/package.json`
npm package manifest with:
- `prettier@^3.4.2` as a dev dependency
- Three scripts:
  - `npm run format` — auto-formats all `*.html`, `*.css`, `*.js` files in-place
  - `npm run format:check` — checks formatting without modifying files (returns exit 1 if issues found; suitable for CI)
  - `npm run lint` — alias for `format:check`

### `format-frontend.sh`
Root-level shell script for convenience:
```bash
./format-frontend.sh          # Check formatting only
./format-frontend.sh --fix    # Auto-fix formatting in place
```
Automatically runs `npm install` inside `frontend/` if `node_modules/` is missing.

---

## Modified Files

### `frontend/index.html`
- `<!DOCTYPE html>` → `<!doctype html>` (lowercase, per HTML spec recommendation)
- `<head>` and `<body>` are now indented inside `<html>`
- Void elements (`<meta>`, `<link>`, `<input>`) now have self-closing slashes (`/>`)
- Long `data-question` button attributes are split across multiple lines for readability
- `&quot;` HTML entity replaced with actual double quotes (using single-quote wrapper for the attribute)
- Added newline at end of file

### `frontend/script.js`
- Removed trailing whitespace on blank lines
- Collapsed double blank lines to single blank lines
- Added trailing commas to object and function-argument lists
- Arrow function single parameters now wrapped in parentheses: `button =>` → `(button) =>`
- Long `addMessage(...)` call wrapped across multiple lines
- Added newline at end of file

### `frontend/style.css`
- Combined selector `*, *::before, *::after` split to one selector per line
- Long `font-family` value wrapped onto a continuation line
- Single-line rules (e.g. `.message-content h1 { font-size: 1.5rem; }`) expanded to multi-line blocks
- Keyframe selector `0%, 80%, 100%` split to one value per line
- Added newline at end of file

### `.gitignore`
- Added `frontend/node_modules/` and `frontend/package-lock.json` to prevent committing generated files.

---

## Developer Workflow

**First-time setup** (installs Prettier):
```bash
cd frontend && npm install
```

**Check formatting** (e.g. in CI or before committing):
```bash
./format-frontend.sh
# or
cd frontend && npm run format:check
```

**Auto-fix formatting**:
```bash
./format-frontend.sh --fix
# or
cd frontend && npm run format
```
