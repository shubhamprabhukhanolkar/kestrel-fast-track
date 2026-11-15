---
name: Obsidian Violet
colors:
  surface: '#131315'
  surface-dim: '#131315'
  surface-bright: '#39393b'
  surface-container-lowest: '#0e0e10'
  surface-container-low: '#1c1b1d'
  surface-container: '#201f21'
  surface-container-high: '#2a2a2c'
  surface-container-highest: '#353437'
  on-surface: '#e5e1e4'
  on-surface-variant: '#c9c4d3'
  inverse-surface: '#e5e1e4'
  inverse-on-surface: '#313032'
  outline: '#938f9d'
  outline-variant: '#484551'
  surface-tint: '#c9beff'
  primary: '#c9beff'
  on-primary: '#301d7c'
  primary-container: '#998aeb'
  on-primary-container: '#2f1c7b'
  inverse-primary: '#5f50ad'
  secondary: '#c0c1ff'
  on-secondary: '#1000a9'
  secondary-container: '#3131c0'
  on-secondary-container: '#b0b2ff'
  tertiary: '#4edea3'
  on-tertiary: '#003824'
  tertiary-container: '#00ac77'
  on-tertiary-container: '#003723'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e6deff'
  primary-fixed-dim: '#c9beff'
  on-primary-fixed: '#1b0063'
  on-primary-fixed-variant: '#473793'
  secondary-fixed: '#e1e0ff'
  secondary-fixed-dim: '#c0c1ff'
  on-secondary-fixed: '#07006c'
  on-secondary-fixed-variant: '#2f2ebe'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#131315'
  on-background: '#e5e1e4'
  surface-variant: '#353437'
  surface-deep: '#0A0A0C'
  surface-base: '#111116'
  surface-raised: '#18181F'
  surface-overlay: '#22222B'
  border-subtle: '#262635'
  border-highlight: '#38364D'
  accent-lavender-glow: '#AB9FF2'
  accent-violet-deep: '#221438'
  neon-mint: '#10B981'
  neon-cyan: '#06B6D4'
  status-danger: '#EF4444'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 56px
    fontWeight: '700'
    lineHeight: 64px
    letterSpacing: -0.03em
  display-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 38px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.025em
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '600'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
  label-lg:
    fontFamily: Space Grotesk
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.02em
  label-md:
    fontFamily: Space Grotesk
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.04em
  label-sm:
    fontFamily: Space Grotesk
    fontSize: 10px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.06em
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-md: 1.5rem
  gutter-lg: 2rem
  margin: 1rem
  margin-md: 2rem
  margin-lg: 3rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system delivers a premier, institutional-grade Web3 consumer experience. It balances cryptic luxury with effortless clarity, stripping away raw technical noise in favor of luminous hierarchy and fluid accessibility. Tailored for decentralized finance power users, digital asset collectors, and forward-thinking consumers, the interface instills utmost trust and security while exuding bleeding-edge digital craftsmanship.

The visual style merges **Dark Mode Minimalism** with refined **Glassmorphism** and subtle **Radiant Glows**. The aesthetic relies on ultra-deep graphite obsidian canvases, high-luminance lavender and violet interactive focal points, crisp 1px borders, and mint-neon verification signals. Interfaces feel frictionless, deliberate, and weightless.

## Colors

The palette operates in strict dark mode, anchored by layered obsidian and deep graphite foundations (`#0A0A0C` to `#22222B`) rather than flat pure blacks.

- **Primary (`#998AEB`)**: The signature electric lavender, reserved for core call-to-actions, focused highlights, interactive states, and essential brand presence.
- **Secondary (`#6366F1`)**: Rich indigo-violet that powers linear gradients, secondary interactive controls, and depth transitions.
- **Tertiary (`#10B981`)**: Radiant neon mint, serving as confirmation, portfolio yield growth, verified security credentials, and affirmative transactional feedback.
- **Neutral (`#0A0A0C`)**: Obsidian ground plane, providing deep contrast for translucent cards and floating overlays.

Surfaces employ a strict elevation hierarchy: canvas sits at `surface-deep`, root cards at `surface-base`, popovers and item containers at `surface-raised`, and elevated modals at `surface-overlay`. Accent borders (`#262635` and `#38364D`) establish crisp separation without visual clutter.

## Typography

Typography pairs the fluid geometry of **Plus Jakarta Sans** for primary reading flows with the technical precision of **Space Grotesk** for addresses, metrics, identifiers, and pill badges.

- **Primary Headings & Body:** Set in Plus Jakarta Sans. Negative tracking on headline levels tightens visual cohesion in dense numeric and asset lists.
- **Labels, Telemetry, & Badges:** Set in Space Grotesk. Uppercase styles use generous letter spacing (`0.04em` to `0.06em`) for immediate scannability on cryptographic hashes, network selectors, and status chips.
- **Numeric Clarity:** Numbers within portfolio balances and token quantities must use proportional lining figures with tabular spacing enabled (`font-variant-numeric: tabular-nums`) to prevent layout shifts during live data streaming.

## Layout & Spacing

The layout model implements a fluid 12-column grid on desktop screens transitioning to an 8-column layout on tablet (`768px`) and a 4-column layout on mobile (`<480px`). Extension popovers and compact web3 wallet modals anchor to fixed width constraints (380px to 440px) while maintaining internal fluid gutters.

- **Rhythm:** Spacing follows a modular 4px/8px base scale. Inner component layouts prioritize vertical breathing room around primary key-performance indicators and balance cards.
- **Outer Shell & Gutters:** On desktop viewport, outer margin scales up to `margin-lg` (`3rem`) with `gutter-lg` (`2rem`). Mobile viewports snap to compact `margin` (`1rem`) and `gutter` (`1rem`).
- **Nesting:** Child containers within list views use strict `space-xs` (4px) to `space-sm` (8px) gaps, enforcing visual grouping against the wider card padding (`space-lg`).

## Elevation & Depth

Visual hierarchy uses dark translucent surfaces, precise 1px borders, and targeted soft-light ambient glows instead of standard dark-cast drop shadows.

- **Ground (Canvas):** Pure `#0A0A0C`, non-reflective, anchoring the application background.
- **Surface Level 1 (Panels & Master Cards):** `#111116` with a uniform 1px solid border in `#262635`. Translucent variations apply `rgba(17, 17, 22, 0.75)` with `backdrop-filter: blur(16px)`.
- **Surface Level 2 (Nested Items & Hover States):** `#18181F` with a 1px border shifting towards `#38364D`.
- **Surface Level 3 (Modals, Toasts, & Dropdowns):** `#22222B` bounded by a 1px boundary of `rgba(171, 159, 242, 0.2)`. Casts a dual diffuse shadow: `0 12px 32px -4px rgba(0, 0, 0, 0.65), 0 0 24px 0 rgba(153, 138, 235, 0.08)`.
- **Accent Glows:** Primary active elements emit a subtle 12px radial blur tinted with `rgba(153, 138, 235, 0.25)`, providing a luminous feedback state.

## Shapes

The interface embraces a fluid, pill-infused curvature philosophy (`roundedness: 3`).

- **Micro Controls & Badges:** Network status pills, token tags, and actionable mini chips use full continuous pill rounding (`rounded-full` / 9999px).
- **Core Cards & Panels:** Enclosed at `rounded-xl` (24px to 32px), creating a friendly yet secure enclosure reminiscent of modern mobile hardware shells.
- **Form Inputs & Action Buttons:** Standard interactive inputs utilize `rounded-lg` (16px), harmonizing with the overarching circular geometry without swallowing interior label clearance.

## Components

### Buttons
- **Primary:** Full pill radius, solid `#998AEB` background, `#0A0A0C` bold text. On hover, background shifts to `#AB9FF2` with an ambient glow (`box-shadow: 0 0 20px rgba(153, 138, 235, 0.4)`). Active state applies a scale transform (`scale(0.98)`).
- **Secondary:** Dark surface container (`#18181F`) with 1px border `#262635` and `#FFFFFF` text. Hover prompts border illumination (`#38364D`) and surface lightening (`#22222B`).
- **Ghost / Tertiary:** Transparent background, `#AB9FF2` text, transitioning to `rgba(153, 138, 235, 0.1)` on hover.

### Chips & Badges
- Pill-shaped with horizontal padding `space-md` (12px) and vertical padding `space-xs` (4px). Space Grotesk font at `label-sm` or `label-md`.
- **Verified / Positive:** `rgba(16, 185, 129, 0.12)` background, `1px solid rgba(16, 185, 129, 0.3)` border, `#10B981` text with an inset pulse dot.
- **Network Tag:** Obsidian base (`#18181F`), 1px neutral border, subtle lavender text.

### Cards & Asset Tiles
- **Base Card:** Structured using `surface-base` (`#111116`), 1px border `#262635`, padding `space-lg`.
- **Interactive Asset Tile:** Nested inside lists with `surface-raised` background (`#18181F`). Displays coin icon on left, primary typography title and balance top-aligned, and monospace address/secondary value bottom-aligned. Hover transitions background to `surface-overlay` with a smooth 150ms bezier curve.

### Inputs & Search Bars
- Background: `#111116`. Border: 1px `#262635`. Radius: `16px`.
- Placeholder text: `rgba(255, 255, 255, 0.35)`.
- Focused: Border transitions to `#998AEB` with an outer ring blur: `box-shadow: 0 0 0 3px rgba(153, 138, 235, 0.15)`.

### Checkboxes & Toggle Switches
- **Toggle Switches:** Track measures 44px by 24px, pill rounded. Inactive track is `#18181F` with `#262635` border; active track transitions to `#998AEB`. Thumb is solid white, shifting right smoothly with `cubic-bezier(0.16, 1, 0.3, 1)`.
- **Checkboxes:** 20px rounded squircle (6px radius). When checked, fills with `#998AEB` featuring an obsidian checkmark.

### Additional Crypto-Specific Components
- **Key-Value Telemetry Rows:** Used for gas estimates, slippage, and transaction simulation; values set in tabular Space Grotesk.
- **Address Badge:** Compact pill displaying truncated public keys (`0x1a...4b8`) with an instant one-click copy feedback animation that pulses `#10B981`.