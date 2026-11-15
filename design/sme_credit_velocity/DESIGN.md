---
name: SME Credit Velocity
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf7'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e6eeff'
  surface-container-high: '#dde9ff'
  surface-container-highest: '#d3e3ff'
  on-surface: '#0b1c30'
  on-surface-variant: '#434654'
  inverse-surface: '#213146'
  inverse-on-surface: '#ebf1ff'
  outline: '#747685'
  outline-variant: '#c4c6d6'
  surface-tint: '#2555cb'
  primary: '#0041b6'
  on-primary: '#ffffff'
  primary-container: '#2d5bd1'
  on-primary-container: '#d9e0ff'
  inverse-primary: '#b5c4ff'
  secondary: '#006a60'
  on-secondary: '#ffffff'
  secondary-container: '#94f0e1'
  on-secondary-container: '#006f64'
  tertiary: '#3c4c6a'
  on-tertiary: '#ffffff'
  tertiary-container: '#546483'
  on-tertiary-container: '#d5e1ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b5c4ff'
  on-primary-fixed: '#00174d'
  on-primary-fixed-variant: '#003dab'
  secondary-fixed: '#97f3e4'
  secondary-fixed-dim: '#7ad7c8'
  on-secondary-fixed: '#00201c'
  on-secondary-fixed-variant: '#005048'
  tertiary-fixed: '#d7e2ff'
  tertiary-fixed-dim: '#b7c7eb'
  on-tertiary-fixed: '#091b37'
  on-tertiary-fixed-variant: '#374765'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e3ff'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 26px
    fontWeight: '700'
    lineHeight: 34px
    letterSpacing: -0.015em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  title-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.005em
  title-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0.01em
  metric-num:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '700'
    lineHeight: 28px
    letterSpacing: -0.01em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1.25rem
  margin: 1.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

This design system establishes a high-conviction, deterministic workbench for credit underwriters and SME lending analysts handling fast-track decisions under ₹25L. The emotional tone is authoritative, composed, and analytically rapid: reducing cognitive friction in credit committee reviews while eliminating ambiguity during fast-turnaround underwriting.

The visual style pairs **Corporate Modernism** with **Precision Data Density**. Surfaces are structured, low-glare, and calm, using architectural hierarchy rather than decorative flourishes to guide focus. Key interactions present decisive visual feedback, reinforcing auditability, automated policy adherence, and verifiable AI agent recommendations without clinical coldness.

## Colors

The palette employs deep structural foundations, crisp functional contrasts, and specialized semantic indicators for underwriting states:

- **Structural Navy (`#10213D`):** Anchors headers, navigation rails, and master application boundaries.
- **Royal Blue (`#2D5BD1`, Hover `#2247A8`):** Designated exclusively for primary credit commitments, approvals, and focal call-to-actions.
- **Teal Focus (`#087C70`):** System-level highlights, active tab tracks, and telemetry metrics.
- **Canvases & Surfaces:** Soft Slate (`#F3F6FA`) frames the overall workspace, while Pure White (`#FFFFFF`) houses actionable cards, workbench tiers, and data grids. Crisp structural separation uses hairline borders (`#E0E7F0`).
- **Underwriting State Semantics:**
  - *Verified / Rule Passed:* Background `#E6F6EF` with text and hairline border `#08715F`.
  - *Policy Variance / Flag:* Background `#FFF3DC` with text and hairline border `#8A5A00`.
  - *GenAI Underwriting Copilot / Agent Action:* Background `#F0EBFF` with text and hairline border `#633DA3`.

## Typography

Inter serves as the sole typographic engine, providing crystalline legibility across micro-labels, rule triggers, and composite data grids. 

All financial metrics, rupee values (`₹`), timestamps, and bureau risk scores strictly enforce tabular lining numerals via `font-feature-settings: 'tnum' 1, 'cv05' 1`. This aligns decimals and commas across tabular scans without horizontal jitter. Labels under 12px leverage uppercase treatment with positive tracking to maintain immediate scannability during high-velocity underwriting sessions.

## Layout & Spacing

The operational interface uses a controlled, uncluttered master-detail layout model:
- **Primary Canvas:** Fixed 64px structural header with an optional collapsible 56px utility dock.
- **Two-Panel Limit:** The core workbench restricts content to a maximum of two side-by-side active operational panels on desktop (e.g., 60% Underwriting Dossier / Bureau Graph + 40% Rule Verification Engine & AI Copilot). This intentional constraint avoids multi-window fragmentation and prevents operator oversight.
- **Breakpoints:**
  - *Desktop (>1280px):* Two-panel split with 20px (`1.25rem`) gutters and 24px (`1.5rem`) page margin.
  - *Tablet (768px – 1279px):* Panels collapse into stacked segment tabs (Dossier vs. Verification Engine), retaining full component padding.
  - *Mobile (<767px):* Linear single-column flow with persistent pinned action tray for decisive approvals.

## Elevation & Depth

To maintain high data integrity and avoid visual distraction, depth is conveyed primarily through **tonal layering and low-contrast borders** rather than dramatic drop shadows.

- **Base Layer (L0):** Canvas backdrop in Soft Slate (`#F3F6FA`).
- **Workbench Cards (L1):** Pure White (`#FFFFFF`) surfaces defined by a crisp 1px solid border (`#E0E7F0`). Shadows are avoided or limited to an ambient footprint (`0 1px 3px rgba(16, 33, 61, 0.04)`).
- **Floating Modals / Flyout Trays (L2):** 1px border (`#E0E7F0`) paired with a directional, low-opacity shadow (`0 8px 24px -4px rgba(16, 33, 61, 0.12)`).
- **Copilot & AI Insights Layer:** Identified by a soft purple-tinted rim highlight rather than elevation, preserving the structural baseline while distinguishing autonomous recommendations from human decisions.

## Shapes

The design system maintains a **Soft (Level 1)** geometric discipline. Structural panels, tables, input fields, and metric cards apply a standard `0.25rem` (4px) corner radius, preserving a sharp, institutional, enterprise-grade feel. 

Interactive elements such as pill badges, status tags, and specific micro-indicators use `rounded-lg` (8px) or complete pill styles strictly when representing discrete, categorical state tokens (e.g., sanction readiness, GST status).

## Components

### Buttons
- **Primary Button:** Royal Blue (`#2D5BD1`) background with `#FFFFFF` text. Hover state shifts to `#2247A8`. Active state deepens to `#1A3782`. Focus utilizes a 2px outer ring in Teal (`#087C70`).
- **Secondary Button:** Surface `#FFFFFF`, 1px solid `#E0E7F0` border, Navy (`#10213D`) text. Hover introduces `#F3F6FA` fill.
- **Destructive/Reject Action:** Outlined `#D9383A` with low-opacity fill on hover, ensuring high friction before loan rejection.

### Status Chips & Badges
- **Verified Policy Chip:** Background `#E6F6EF`, text and border `#08715F`. Includes an inline checkmark glyph.
- **Variance Warning Chip:** Background `#FFF3DC`, text and border `#8A5A00`. Used for threshold policy deviations under ₹25L.
- **GenAI Copilot Chip:** Background `#F0EBFF`, text and border `#633DA3`. Accompanying agent synthesis cards utilize a matching 1px hairline border.

### Input Fields & Selectors
- Default state: Background `#FFFFFF`, 1px border `#E0E7F0`, text `#10213D`.
- Focus state: Border transitions to `#2D5BD1` with a `0 0 0 1px #2D5BD1` inner ring.
- Disabled/Read-only states: Background `#F3F6FA`, text `#607088`, preventing edit confusion during review stages.

### Checkboxes & Radios
- Box size 16x16px with a 2px corner radius. Unchecked state: 1.5px border `#E0E7F0`. Checked state: `#2D5BD1` fill with white indicator glyph.

### Cards & Metric Modules
- Encased in Pure White (`#FFFFFF`) with 1px border `#E0E7F0` and `space-md` (16px) internal padding.
- Key financial indicators (e.g., Calculated Loan Eligibility, Bank Turnover, GST Run-Rate) feature a top-anchored 11px uppercase label followed by `metric-num` typography with `tnum` enabled.

### Tables & Underwriting Grids
- Headers sit on `#F3F6FA` with 1px bottom border `#E0E7F0`, styled in `label-sm` Navy (`#10213D`).
- Row heights are compact (40px default) to maximize vertical information density. Zebra striping is omitted in favor of a subtle `#F3F6FA` hover state across the entire record line.