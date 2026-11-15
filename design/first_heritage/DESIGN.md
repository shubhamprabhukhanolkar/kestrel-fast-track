---
name: First Heritage
colors:
  surface: '#fcf8ff'
  surface-dim: '#dad8ef'
  surface-bright: '#fcf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f2ff'
  surface-container: '#efecff'
  surface-container-high: '#e8e6fe'
  surface-container-highest: '#e3e0f8'
  on-surface: '#1a1a2b'
  on-surface-variant: '#594140'
  inverse-surface: '#2f2f41'
  inverse-on-surface: '#f2efff'
  outline: '#8d706f'
  outline-variant: '#e0bfbd'
  surface-tint: '#b02c33'
  primary: '#7a0014'
  on-primary: '#ffffff'
  primary-container: '#9d1d27'
  on-primary-container: '#ffafac'
  inverse-primary: '#ffb3b0'
  secondary: '#006495'
  on-secondary: '#ffffff'
  secondary-container: '#7cc5fe'
  on-secondary-container: '#00517b'
  tertiary: '#5c2f00'
  on-tertiary: '#ffffff'
  tertiary-container: '#7d4200'
  on-tertiary-container: '#ffb477'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdad8'
  primary-fixed-dim: '#ffb3b0'
  on-primary-fixed: '#410006'
  on-primary-fixed-variant: '#8e101e'
  secondary-fixed: '#cbe6ff'
  secondary-fixed-dim: '#90cdff'
  on-secondary-fixed: '#001e30'
  on-secondary-fixed-variant: '#004b71'
  tertiary-fixed: '#ffdcc3'
  tertiary-fixed-dim: '#ffb77d'
  on-tertiary-fixed: '#2f1500'
  on-tertiary-fixed-variant: '#6e3900'
  background: '#fcf8ff'
  on-background: '#1a1a2b'
  surface-variant: '#e3e0f8'
  crimson-dark: '#7A141D'
  crimson-light: '#C92A36'
  surface-cream: '#FDFBF7'
  surface-pearl: '#F4F4F6'
  gold-light: '#FDE68A'
  gold-dark: '#B45309'
  midnight-slate: '#25243B'
typography:
  display-hero:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '800'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-hero-mobile:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '800'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.04em
  financial-display:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 0.75rem
  margin: 2rem
  margin-mobile: 1rem
  space-2xs: 0.25rem
  space-xs: 0.5rem
  space-sm: 0.75rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
  space-2xl: 3rem
  space-3xl: 4rem
---

## Brand & Style

This design system embodies the ethos of a modern, institutional powerhouse tailored for retail consumers and SME commercial growth. Blending contemporary precision with traditional heritage, it projects unwavering trust, financial security, and customer-first clarity.

The visual style is **Contemporary Corporate Banking with Tactile Warmth**. It combines structured modularity, generous hierarchy, rich tactile gradients, and crisp architectural boundaries. Rather than cold tech minimalism, the design embraces warmth via cream-tinted micro-surfaces, balanced by deep crimson, navy-infused charcoal, and amber highlights. The resulting emotional tone conveys fiscal authority, effortless digital utility, and celebratory Indian prosperity.

## Colors

The palette is anchored by the signature deep crimson, communicating institutional heritage and high-impact identity. 

- **Primary (`#9D1D27`)**: Governs high-priority calls to action, active navigation states, primary banking tiles, and brand hero banners.
- **Secondary (`#287CB1`)**: Deployed for digital trust cues, alternative savings/investment feature sets, loan modules, and informative tags.
- **Tertiary (`#D97706`)**: Functions as the catalyst color for milestone rewards, financial calculators, interest highlights, and promotional accents.
- **Neutral (`#1E1E2F`)**: A warm midnight-charcoal providing high-contrast readability across all typographic levels, grounding cards and forms with corporate stability.

### Canvas & Surface Hierarchy
- `surface-cream` (`#FDFBF7`) serves as the base body background to soften high-contrast white spaces.
- `surface-pearl` (`#F4F4F6`) creates contrast for structured cards, nested calculation containers, and input bays.
- Micro-dividers utilize muted strokes at 10%–15% opacity over crimson or dark midnight backgrounds to maintain subtle containment without visual clutter.

## Typography

The design system utilizes **Inter** across all roles to achieve unmatched typographic clarity, tabular digit alignment, and high-density readability required for complex transactional workflows.

- **Numerics & Financial Metrics**: All currency, interest rates, and calculator totals use tabular figures (`font-variant-numeric: tabular-nums`) with tight tracking to ensure rapid scanning and alignment across ledger rows.
- **Headlines & Section Prompts**: Display weights (700–800) bring bold institutional presence. Titles must maintain snug line heights to preserve visual cohesion against high-impact card tiles.
- **Micro-Copy**: Labels and metadata utilize medium-to-bold weights with uppercase or title casing to preserve legibility at small sizes.

## Layout & Spacing

A responsive 12-column grid is enforced on desktop and tablet, converting to a dynamic 4-column structure on mobile devices.

### Form Factors & Adaptation
- **Desktop (≥ 1024px)**: 12 columns, `1.5rem` (24px) gutters, `2rem` (32px) margins. Maximum content boundary capped at `1280px` for optimal reading spans.
- **Tablet (768px – 1023px)**: 8 columns, `1rem` (16px) gutters, `1.5rem` (24px) margins. Banking modules shift from multi-row 4-column blocks to 2-column stacked grids.
- **Mobile (< 768px)**: 4 columns, `0.75rem` (12px) gutters, `1rem` (16px) margins. Product matrices convert into horizontal carousels or full-width vertical card stacks.

### Density & Rhythms
Spacing operates on an absolute 8pt grid with 4pt half-steps for micro-components (buttons, badge tags, icon gaps). Financial calculation panels utilize tighter inner padding (`space-md`) to maximize vertical real estate, whereas marketing headers utilize generous vertical blocks (`space-2xl` to `space-3xl`).

## Elevation & Depth

Visual hierarchy is maintained through structured tonal contrast paired with warm, low-opacity ambient shadows. The system avoids harsh dropped drop-shadows in favor of grounded physical tiers.

- **Flat/Subsurface (Level 0)**: Background canvases (`surface-cream` or pure white) with zero elevation.
- **Contained Surface (Level 1)**: Primary product cards, standard calculator boxes, and list containers use a `1px` subtle border in `#E5E7EB` along with a diffused shadow: `0 2px 4px -1px rgba(37, 36, 59, 0.04), 0 4px 6px -1px rgba(37, 36, 59, 0.02)`.
- **Raised/Interactive (Level 2)**: Hover states, active dropdown lists, and floating tooltips use an elevated shadow with a warm undertone: `0 10px 15px -3px rgba(37, 36, 59, 0.08), 0 4px 6px -2px rgba(37, 36, 59, 0.04)`.
- **Overlay/Modal (Level 3)**: Quick-action drawers, verification modals, and high-impact loan calculators use a deep projection: `0 20px 25px -5px rgba(37, 36, 59, 0.12), 0 10px 10px -5px rgba(37, 36, 59, 0.04)`.
- **Vibrant Tonal Tiles**: Signature crimson and navy product cards rely on pure color saturation rather than dark drop shadows, floating naturally through distinct chromatic weight.

## Shapes

The design system implements a refined **Level 2 (Rounded)** shape language. The curvature gives UI components a friendly, contemporary touch while maintaining the structural rigidity expected of a financial institution.

- Standard buttons, text inputs, and chips feature `0.5rem` (8px) corner radii.
- Medium components, such as product feature cards, calculators, and informational banners, utilize `rounded-lg` (`1rem` / 16px).
- Major container sections, hero highlight wrappers, and modal panels scale to `rounded-xl` (`1.5rem` / 24px).
- Circular rounding (`9999px`) is reserved exclusively for numerical badges, avatar frames, pill tags, and quick-action icon containers.

## Components

### Buttons
- **Primary**: Solid crimson background (`#9D1D27`), white text, `0.5rem` border radius, high-weight typography (`label-lg`). Hover shifts to `#7A141D` with subtle forward transition.
- **Secondary / Ghost**: High-contrast border (`1.5px` solid `#9D1D27` or `#FFFFFF` over dark backgrounds), transparent body, label inherits border color.
- **Action Links**: Text-only button accompanied by an inline right-facing chevron (`→`), animated on hover with a `2px` translateX nudge.

### Product & Feature Cards
- **Signature Crimson Tile**: Deep `#9D1D27` fill, white typography, subtle corner watermark icon at 15% opacity, and clean white borderless pill CTAs inside.
- **Digital Service Tile**: Deep slate `#287CB1` fill, featuring white icon outlines and dedicated secondary CTA links.
- **Standard Outline Card**: Pure white background, `1px` stroke in `#E5E7EB`, hover elevation lift to Level 2 with top-border highlight in tertiary amber.

### Financial Calculators
- Dynamic calculation blocks utilize light pearl backgrounds (`surface-pearl`) encased in white master cards.
- **Range Sliders**: Filled track in `#9D1D27`, background track in `#E5E7EB`, and an oversized white thumb handle with a `2px` crimson ring border and Level 2 elevation.
- **Total Display Block**: High-contrast, highlighted with light amber background tint and bold tabular numbers in `financial-display`.

### Form Fields & Inputs
- Height standardized to `48px` on desktop and touch targets of `48px` minimum on mobile.
- Base border `1px` solid `#D1D5DB`. On focus, shifts to a `2px` `#9D1D27` ring with `0 0 0 3px rgba(157, 29, 39, 0.12)`.
- Currency prefix symbols (`₹`) are anchored inside a gray fixed-width container on the input's leading edge.

### Chips & Filter Tabs
- Segmented pills with `9999px` radius. Inactive states use `surface-pearl` with muted text; active states invert to solid crimson with white text.

### Trust & Metric Badges
- Floating round or soft-square pill badges celebrating ratings (e.g., "4.9 ★"), featuring amber tertiary fills (`#D97706`), bold white numbers, and micro-labeling beneath.