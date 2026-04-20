# CLAUDE.md

Guidance for Claude Code working in this repo.

## Project Overview

PyWire app for financial simulation: historical stock/inflation data, retirement contribution planning, withdrawal strategy, HSA medical receipts. Uses local Postgres + Stripe-linked user/subscription models, optional auth middleware.

## Development Commands

```bash
# Docker Compose (http://localhost:3000, hot-reload, src/ mounted)
cp .env.example .env  # set POSTGRES_PASSWORD
source .env
docker compose up -d --build

# Local, no DB/auth (https://localhost:8765 with local mkcert cert)
uv sync
uv run pywire dev
```

The Docker image uses `pywire dev --no-tui --host 0.0.0.0 --reload` over plain HTTP. **Do not add mkcert to the Dockerfile** — the container-generated cert won't be trusted by the host browser.

## Architecture

### PyWire Framework

- **Pages**: `src/pages/*.wire` — routes auto-derived from filename
- **Components**: `src/components/*.wire` — snake_case filename → PascalCase import (`modal.wire` → `Modal`)
- **Layouts**: `__layout__.wire` wraps its sibling/descendant pages. Slot via `{$render children}`
- **Error page**: `__error__.wire` renders on exceptions
- **PJAX**: enabled in `main.py` — SPA-like partial updates via WebSocket

### `.wire` File Structure

```pywire
---
# Frontmatter — Python module scope (imports, wires, derived, functions, @props)
from pywire import wire, derived

count = wire(0)

@derived
def doubled():
    return count.value * 2

def increment(event):
    count.value += 1
---
<!-- Template — HTML + pywire directives -->
<button @click={increment}>Count: {count.value}, doubled: {doubled.value}</button>

<style scoped>
button { font-size: 1rem; }
</style>
```

Single `---` line opens and closes frontmatter. **No `--- html ---` separator** — that's a doc error from old CLAUDE memory.

### Routes

```text
/                 -> src/pages/index.wire
/globalmarket     -> src/pages/globalmarket.wire
/contributions    -> src/pages/contributions.wire
/withdrawals      -> src/pages/withdrawals.wire
/medicalreceipts  -> src/pages/medicalreceipts.wire
/pricing          -> src/pages/pricing.wire
/login            -> src/pages/login.wire
```

### Application Entry Point

[src/main.py](src/main.py) constructs `PyWire(enable_pjax=True, debug=True, middleware=auth_middleware_stack())`. The `middleware` kwarg takes a Starlette-style list: bare classes or `(cls, kwargs)` tuples. Order is outermost-first.

### Auth

[src/auth_middleware.py](src/auth_middleware.py) declares `SessionMiddleware` + `AuthMiddleware` explicitly.

**Why explicit**: PyWire only auto-installs `SessionMiddleware` when `interactive_server_mode=False`. Interactive mode (default) keeps session state in the WebSocket — HTTP scope has no `scope["session"]` unless you add it yourself.

`AuthMiddleware` reads `scope["session"]["user_id"]` and writes to the `current_user_id` ContextVar (see [src/context.py](src/context.py)) so `.wire` pages can `from context import current_user_id`.

Alternative (not used here): `pywire_auth.connect_auth(app, ...)` auto-installs PyWire's own `SessionMiddleware` + `AuthMiddleware` + routes + policy engine. Use it if/when migrating off the DIY stack.

### Data Layer

- [src/financial_data.py](src/financial_data.py): yfinance-backed returns + inflation fallback. Returns `{dates: [], values: []}` with compounded values starting at 1.0.
- [src/worldbank_data.py](src/worldbank_data.py): S&P Global Equity Indices CSV loader. ~84 countries, 1960–2024.
- [src/models.py](src/models.py): SQLAlchemy ORM. `User` (email, created_at), `Subscription` (user_id, stripe_customer_id, status).

### Data Files

`data/API_CM.MKT.INDX.ZG_DS2_en_csv_v2_10345.csv` — World Bank S&P Global Equity Indices annual % changes.

### Styling

Pico CSS (classless) from CDN, loaded in `__layout__.wire`.

## PyWire Patterns

### Reactive State

- `wire(v)` → reactive cell. Read/write via `.value`
- `@derived` → cached computed cell; returns a `Derived` instance. Read via `.value`
- Plain `def` frontmatter functions → auto-called by the compiler in template expressions. `{func}` runs `func()`

### Template Expression Rules

| Frontmatter | Template | Renders |
|---|---|---|
| `x = wire(5)` | `{x.value}` | `5` |
| `@derived def doubled(): ...` | `{doubled.value}` | computed |
| `@derived def doubled(): ...` | `{doubled}` | compile error — it's an instance |
| `def fmt(): return "..."` | `{fmt}` | auto-called |
| `def fmt(): return "..."` | `{fmt()}` | also works |

Rule of thumb: `@derived` → always `.value`. Plain defs → either `{func}` or `{func()}`.

### Attribute Bindings

`data-chart={calc_chart_data.value}` — binds a string, JSON, etc. into an attribute.

### Events

- **DOM events on regular HTML**: `@click`, `@input`, `@submit`, etc. Handler receives an `event` with `.value`, `.target`, etc.
- **Component callbacks**: use `on_` prop convention, typed `EventHandler[...]`. `@event` is DOM-only.

### Slots / Children

Both layouts and components use `Children` + `{$render children}`:

```pywire
---
@props
class Props:
    children: Children
---
<div class="modal">
  {$render children}
</div>
```

### `$permanent`

Marks an element whose subtree PyWire will NOT morph across updates. Useful for Chart.js canvases, third-party widget roots, etc. Attributes on the element itself **do** still update — that's how the MutationObserver chart pattern works.

Scripts **inside** a `$permanent` element are skipped on re-execution (they already ran once).

### Chart.js Integration

```html
<div $permanent id="chart-container" data-chart={calc_chart_data.value}>
  <canvas id="myChart"></canvas>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script>
  (() => {
    const container = document.getElementById('chart-container');
    if (!container) return;
    const prior = Chart.getChart(document.getElementById('myChart'));
    if (prior) prior.destroy();
    const chart = new Chart(document.getElementById('myChart'), {
      type: 'line',
      data: JSON.parse(container.dataset.chart),
      options: { animation: false, responsive: true },
    });
    new MutationObserver(muts => {
      muts.forEach(m => {
        if (m.attributeName === 'data-chart') {
          const d = JSON.parse(container.dataset.chart);
          chart.data = d; chart.update();
        }
      });
    }).observe(container, { attributes: true });
  })();
</script>
```

Notes:
- Always `Chart.getChart(canvas).destroy()` before `new Chart(...)` — hot-reload and SPA-nav-back both leave stale instances.
- `animation: false` avoids jank on each reactive update.
- Non-async `<script src>` before an inline script now blocks correctly on SPA nav (fixed in pywire ≥ commit that lands after 0.11.0). So Chart.js CDN + inline init works first time.

### Scripts and PyWire Interop

PyWire extracts every `<script>` tag from incoming HTML before morphdom runs, then re-executes them in order afterwards. Every SPA navigation *and* every region update re-runs the inline scripts on the page. Two consequences drive the rules below:

1. Scripts run multiple times per session. They must be idempotent.
2. Page content is delivered via WebSocket and fed through the client DOM diff — the browser doesn't parse a fresh document, and the usual lifecycle events don't fire.

#### Always-apply rules

- **Wrap everything in an IIFE.** Top-level `let`/`const` in inline scripts would leak into global scope and collide on the next run.
  ```html
  <script>(() => { /* page code */ })();</script>
  ```
- **Pick unique identifiers.** If you have two `<script>` blocks on a page, each IIFE has its own scope, but any identifier you write to `window` or expose globally (helpers like `exportCSV`, event-listener wrappers) must be unique per-page.
- **Don't rely on `DOMContentLoaded` or `window.load`.** They do not fire on SPA nav. Use the lifecycle events below.
- **Query the DOM fresh on every run.** Don't cache element references in outer closures across updates — the element may have been morphed.

#### Lifecycle events (dispatched on the morph target)

| Event | When | Typical use |
|---|---|---|
| `pywire:preupdate` | before morphdom | capture animation/scroll state, cancel transitions |
| `pywire:update` | per morphed element | re-init a widget on a specific node |
| `pywire:postupdate` | after morph + scripts ran | global reinit that depends on DOM being settled |
| `pywire:navigate` | SPA nav only (not per-state-change) | analytics pings, history-only side effects |

```js
document.addEventListener('pywire:postupdate', () => { /* re-bind */ });
```

#### Guard against double-init (the Chart.js trap)

Region updates re-run your script even when the target DOM survived via `$permanent`. Calling `new Chart(canvas, ...)` twice throws `Canvas is already in use`. Guard at the top of every widget init:

```js
(() => {
  const canvas = document.getElementById('myChart');
  if (!canvas || typeof Chart === 'undefined') return;
  if (Chart.getChart(canvas)) return;   // <-- already initialized, bail
  // ... new Chart(canvas, ...)
})();
```

The first-run IIFE typically sets up a `MutationObserver` on the `$permanent` container's `data-chart` attribute; that observer stays alive across updates, so later script runs have nothing to do.

#### `$permanent` interaction

- DOM subtree is preserved across morphs.
- Scripts **inside** a `$permanent` element run **once** and are skipped on subsequent re-executions (pywire flags them via `data-pw-permanent`).
- Attributes on the `$permanent` element itself still update — that's how reactive values reach preserved widgets (e.g. `data-chart={calc_chart_data.value}`).

#### `<script src="...">` execution order

PyWire sequences non-async `<script src>` loads before subsequent inline scripts on SPA nav (pywire ≥ 0.11.3). Rule of thumb:

- `<script src="cdn">` followed by `<script>init code</script>` — works first time on SPA nav; the inline script runs after the CDN script finishes loading.
- Add `async` to a `<script src>` only if the subsequent inline script doesn't need it.
- `<script type="module">` does **NOT** re-execute on SPA nav (browser spec limits — modules are cached by specifier). Prefer classic scripts or move module init into a `pywire:postupdate` handler.

#### Strings that look like structural HTML tags

Inline scripts can safely embed `'</head>'`, `'</body>'`, `'<style>'`, or `'<title>'` as string literals — pywire's server-side tag injectors skip `<script>`/`<style>`/`<textarea>`/`<title>` bodies when looking for injection points (pywire ≥ 0.11.3).

The one string that's still dangerous is a literal `</script>`, because the HTML parser terminates the `<script>` element on sight. Split it with string concatenation:

```js
printWindow.document.write('<' + '/script>');   // survives the HTML parser
```

#### Capture-phase interception

When you want to stop PyWire from seeing a DOM event, register a capture-phase listener and call `e.stopImmediatePropagation()` in it. This is the basis of the dollar-input deferred-update pattern.

```js
input.addEventListener('input', function (e) {
    if (e.isFinalUpdate) return;
    // your local handling here
    e.stopImmediatePropagation();
}, true);  // <-- capture phase is required
```

### `<style scoped>`

Scoped styles get a `data-ph-{hash}` attribute appended to each selector in the rule set. `@keyframes`, `@font-face`, etc. are emitted verbatim (global). Nested at-rules (`@media`, `@supports`, `@container`, `@layer`) recurse.

Rule: put page-specific animations in `<style scoped>` alongside their usage. Cross-page/shared animations belong in a component's own scoped style or in the global layout.

### `{$head} ... {/head}`

Frontmatter-driven `<head>` contributions from pages or components:

```pywire
{$head}
  <link rel="stylesheet" href="/static/chart-extras.css">
  <meta name="description" content="Withdrawal planning">
{/head}
```

Appended to the document head. Use this instead of manually injecting into `<head>` via JS.

### Dollar Input Pattern (Deferred PyWire Updates)

Currency inputs that display comma-formatted and only push to PyWire on blur.

```html
<input type="text" class="dollar-input" data-initial-value={my_wire.value}
       placeholder="0" @input={my_handler} />
```

- `type="text"` not `type="number"` — number inputs reject comma-formatted values.

Python handler strips commas:

```python
def my_handler(event):
    try:
        my_wire.value = float(str(event.value).replace(',', ''))
    except (ValueError, TypeError):
        my_wire.value = 0.0
```

JS: two passes in an IIFE.

1. **Focus/blur UX**: on focus stash current value in `placeholder`, clear field; on blur reformat with commas.
2. **Capture-phase input interception**: stop PyWire from seeing keystroke events, then on blur dispatch a synthetic `input` marked `isFinalUpdate` that PyWire does process.

See [src/pages/contributions.wire](src/pages/contributions.wire) for the canonical implementation.

## Page-Specific Notes

### [contributions.wire](src/pages/contributions.wire)

Most complex page in the repo. Reference it first for: dollar-input pattern, deferred PyWire-update pattern, Chart.js integration with MutationObserver on `data-chart`, collapsible detail sections with `@click` toggles.

### [withdrawals.wire](src/pages/withdrawals.wire)

- Single reactive `assets_json = wire(json.dumps([...]))` stores the whole asset list as JSON. Add/remove/edit rows are done JS-side, then synced via a hidden `<input>` that dispatches an `input` event.
- Chart: stacked line, Y-axis 0–100%, projects 20 years forward using per-asset `return_rate`.

### [index.wire](src/pages/index.wire)

Feature-card gradients use the darker palette from `contributions.wire`: Global Market `#4e62c8→#8030b8`, Contributions `#c038a8→#b82040`, Withdrawals `#2868cc→#0898a8`, Medical `#28a860→#108898`.

### [medicalreceipts.wire](src/pages/medicalreceipts.wire)

Self-contained inline modal (does NOT use `components/modal.wire`). Its own keyframes live in its scoped `<style>` block — don't dedupe them into `modal.wire` since the pages are independent.

## Components

### Defining

```pywire
---
from pywire import props, expose

@props
class Props:
    card_title: str
    action: Optional[str] = None
    children: Children            # slot content
    on_click: Optional[EventHandler[dict]] = None  # callback prop convention
---
<div class="card">
  <h1>{card_title}</h1>
  <div class="card-content">{$render children}</div>
  {$if action}<button @click={on_click}>{action}</button>{/if}
</div>

<style scoped>
.card { border: 1px solid black; }
</style>
```

Conventions:
- Always exactly one `@props` class, always named `Props`. LSP + compiler enforce it.
- Snake_case props (`card_title`) are passed as kebab-case in HTML (`card-title`).
- `@event` decorator is **DOM-only** (for `@click` handlers inside an element). For component callback props, use `on_<name>: EventHandler[T]`.

### Using

```pywire
---
from components.my_component import MyComponent

ref_a = ref[MyComponent]()
---
<MyComponent card-title="Hi" $ref={ref_a}>
  <p>child content</p>
</MyComponent>

<button @click={ref_a.my_exposed_method()}>Call method</button>
```

### Exposing Methods / Properties

```pywire
@expose
def my_exposed_method():
    ...

@expose
@property
def llm_content() -> str:
    return "..."
```

Accessed via the parent's `ref[Component]()` binding.

### Known Issues

- Hot reload of component changes sometimes requires a full browser reload.
- PJAX-nav away-and-back into a page using a component can leave stale state — hard-reload to recover.
- Spreading unknown attributes through to the root element doesn't always work — declare every attribute you want to accept explicitly in `Props`.

## PyWire Context

PyWire is a relatively new framework and is likely under-represented in LLM training data. When in doubt, consult [nightly.pywire.dev/docs](https://nightly.pywire.dev/docs) or check `packages/pywire/` in the sibling monorepo at `~/projects/pywire-monorepo`.
