# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A financial simulation web application built with PyWire that visualizes historical stock market performance across countries, inflation data, and provides tools for retirement planning (contributions, withdrawals, medical receipts).

## Development Commands

```bash
# Install/sync dependencies
uv sync

# Run development server (with hot-reload)
uv run pywire dev

# The dev server starts on http://localhost:8000 by default
```

## Architecture

### PyWire Framework

This project uses **PyWire**, a Python web framework with path-based routing. Key concepts:

- **Pages directory**: `src/pages/` - routes are automatically mapped from file structure
- **`.wire` files**: Combine Python logic and HTML templates in a single file
  - Python code goes at the top (before `--- html ---`)
  - HTML goes after the `--- html ---` separator
  - Python variables can be interpolated into HTML using `{variable_name}` syntax
- **Layouts**: `__layout__.wire` files define templates for nested routes
  - `src/pages/__layout__.wire` - root layout with navigation
  - `src/pages/dashboard/__layout__.wire` - dashboard-specific layout
  - Child pages are inserted via `<slot />` tag
- **PJAX enabled**: Partial page updates for faster navigation (configured in [main.py:6](src/main.py#L6))

### Route Structure

```
/                   -> src/pages/index.wire (landing page with feature cards)
/globalmarket       -> src/pages/globalmarket.wire (country stock market data)
/contributions      -> src/pages/contributions.wire (retirement contributions)
/withdrawals        -> src/pages/withdrawals.wire (retirement withdrawals)
/medicalreceipts    -> src/pages/medicalreceipts.wire (HSA receipts)
/pricing           -> src/pages/pricing.wire
/login             -> src/pages/login.wire
/dashboard/*       -> src/pages/dashboard/ (protected area)
```

### Data Layer

**Financial data utilities** ([financial_data.py](src/financial_data.py)):
- Fetches stock market data via yfinance API (`get_sp500_returns`, `get_us_total_market_returns`, `get_global_market_returns`)
- Provides inflation data with fallback to hardcoded values (`get_inflation_data`)
- Returns data as `{dates: [], values: []}` with compounded values starting at 1.0

**World Bank data utilities** ([worldbank_data.py](src/worldbank_data.py)):
- Loads S&P Global Equity Indices from CSV file in `data/` directory
- Provides country-specific stock market returns (`get_country_stock_returns`)
- Lists 84+ countries with available data (`get_available_countries`)
- Default focus countries defined in `DEFAULT_COUNTRIES` list

**Database models** ([models.py](src/models.py)):
- SQLAlchemy ORM with declarative base
- `User` model: email, created_at
- `Subscription` model: user_id, stripe_customer_id, status (linked to Stripe integration)

### Application Entry Point

[main.py](src/main.py) creates the PyWire application instance with:
- Pages directory: `src/pages`
- PJAX enabled for SPA-like behavior
- Debug mode on

## Data Files

World Bank stock market data is stored in `data/API_CM.MKT.INDX.ZG_DS2_en_csv_v2_10345.csv` containing S&P Global Equity Indices (annual percentage changes) for 84+ countries from 1960-2024.

## Styling

Uses Pico CSS (minimal classless CSS framework) loaded from CDN in the root layout.

## Page-Specific Notes

### [withdrawals.wire](src/pages/withdrawals.wire)

- Reactive state: `stocks_balance`, `bonds_balance`, `bills_balance` (all `wire(0.0)`)
- `calc_chart_data()` returns JSON for a stacked percentage bar chart projected over 20 years using per-asset return rates (`STOCKS_RETURN=0.10`, `BONDS_RETURN=0.04`, `BILLS_RETURN=0.015`)
- Chart uses Chart.js 4.4.1 with `type: 'bar'`, `stacked: true`, Y-axis 0–100%
- Dollar inputs use the focus/blur/comma-formatting pattern (see PyWire Patterns below)

### [index.wire](src/pages/index.wire)

- Feature card gradients use the darker palette from `contributions.wire` (not the bright pastels)
- Colors: Global Market `#4e62c8→#8030b8`, Contributions `#c038a8→#b82040`, Withdrawals `#2868cc→#0898a8`, Medical `#28a860→#108898`

### [contributions.wire](src/pages/contributions.wire)

- Most complex page; the dollar input pattern, deferred PyWire update pattern, and chart integration pattern all originate here — reference it first when building similar functionality

## PyWire Patterns (Learned from This Project)

### Function Calls in Templates

Always call functions **with parentheses** in HTML attribute bindings:

```html
<!-- CORRECT — explicitly calls the function -->
<div data-chart={calc_chart_data()}>

<!-- WRONG — renders the bound method object as a string e.g. "<bound method ...>" -->
<div data-chart={calc_chart_data}>
```

### Accessing Variables Inside Methods

Class-level non-wire variables (e.g. `current_age = 45`) are **not accessible by name** from inside PyWire methods. Either inline the values or compute them locally:

```python
# BAD — years_to_retirement is a class-level var, not accessible in a method
def calc_chart_data():
    years = list(range(2026, 2026 + years_to_retirement))  # NameError

# GOOD — compute inline
def calc_chart_data():
    n_years = 65 - 45
    years = list(range(datetime.now().year, datetime.now().year + n_years))
```

Wire variables (`wire()`) ARE accessible normally via `.value`.

### Chart.js Integration (`$permanent` + MutationObserver)

The standard pattern for reactive charts across all pages:

```html
<!-- In HTML: $permanent prevents PyWire from wiping the canvas;
     data-chart={func()} updates the attribute on every reactive change -->
<div $permanent id="chart-container" data-chart={calc_chart_data()}>
    <canvas id="myChart"></canvas>
</div>
```

```javascript
// In JS: read initial data, then watch for attribute changes
const container = document.getElementById('chart-container');
const chart = new Chart(ctx, { /* init with JSON.parse(container.dataset.chart) */ });

new MutationObserver(mutations => {
    mutations.forEach(m => {
        if (m.attributeName === 'data-chart') {
            const data = JSON.parse(container.dataset.chart);
            // update chart.data.datasets[n].data = data.field
            chart.update();
        }
    });
}).observe(container, { attributes: true });
```

- `$permanent` stops PyWire patching children, but PyWire **still updates attributes** on the element itself
- Always use Chart.js `animation: false` with this pattern to avoid jank on reactive updates

### PJAX and Script Execution

With PJAX enabled, navigating between pages does **not** trigger a full page reload. Consequences:

- `window.addEventListener('load', ...)` — **will NOT fire** on PJAX navigation; scripts using this will silently not run after the first page load
- `document.addEventListener('DOMContentLoaded', ...)` — same problem
- **IIFEs** `(function() { ... })()` — **DO work** because script tags are re-executed when injected via PJAX fetch

Always wrap page scripts in an IIFE:

```javascript
<script>
    (function () {
        // runs correctly on both initial load and PJAX navigation
    })();
</script>
```

### Dollar Input Pattern (Deferred PyWire Updates)

For currency inputs that format with commas and only send updates to PyWire on blur:

**HTML:**

```html
<input type="text" class="dollar-input" data-initial-value={my_wire.value}
       placeholder="0" @input={my_handler} style="..." />
```

- Use `type="text"` not `type="number"` — number inputs reject comma-formatted values

**Python handler** must strip commas before parsing:

```python
def my_handler(event):
    try:
        my_wire.value = float(str(event.value).replace(',', ''))
    except (ValueError, TypeError):
        my_wire.value = 0.0
```

**JavaScript** (two-pass over `.dollar-input` elements):

1. **Focus/blur formatting**: on focus move current value to `placeholder`, clear field; on blur restore or reformat with commas
2. **Capture-phase interception**: intercept all `input` events before PyWire sees them (`e.stopImmediatePropagation()` in capture phase), do live comma formatting locally, then on blur dispatch a synthetic `isFinalUpdate` event that PyWire processes

```javascript
// Pass 1: focus/blur UX
input.addEventListener('focus', function() {
    this.dataset.oldValue = this.value;
    this.placeholder = this.value || '0';
    this.value = '';
});
input.addEventListener('blur', function() {
    if (this.value === '' && this.dataset.oldValue) this.value = this.dataset.oldValue;
    else if (this.value) {
        const n = parseInt(this.value.replace(/[^\d]/g, ''), 10);
        this.value = n > 0 ? n.toLocaleString('en-US') : '';
    }
    delete this.dataset.oldValue;
});

// Pass 2: defer PyWire update to blur
let pending = false;
input.addEventListener('input', function(e) {
    if (e.isFinalUpdate) return;
    // ... live comma formatting ...
    pending = true;
    e.stopImmediatePropagation();  // block PyWire from seeing this event
}, true);  // <-- capture phase is required

input.addEventListener('blur', function() {
    if (pending) {
        pending = false;
        const ev = new Event('input', { bubbles: true });
        ev.isFinalUpdate = true;
        this.dispatchEvent(ev);  // now PyWire processes it
    }
});
```

## PyWire Context

This project uses a new Python web framework that is not widespread on the internet and is likely missing from most LLM training datasets. Here is some information provided by the documentation at [nightly.pywire.dev/docs](https://nightly.pywire.dev/docs).
