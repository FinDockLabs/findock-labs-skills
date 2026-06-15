# Accessibility — WCAG 2.2 AA (required for every page)

Every page this skill produces MUST be WCAG 2.2 AA compliant. This is not optional and not
a polish step — build it in from the first line. This checklist is tailored to payment forms.

## Perceivable

- **Contrast (1.4.3)**: body text ≥ 4.5:1 against its background; large text (≥24px or
  ≥18.5px bold) ≥ 3:1. Watch out for "muted" helper text and semi-transparent white text on
  hero sections — check actual computed contrast, don't guess. Greys lighter than ~#767676
  on white fail.
- **Non-text contrast (1.4.11)**: input borders, radio/checkbox outlines, and focus
  indicators ≥ 3:1 against adjacent background. Default light-grey borders (#ccc, #e4e4e7)
  FAIL — use ≥ #767676-equivalent (e.g. #8a8a93 on white) or add another visible boundary.
- **Images (1.1.1)**: payment method / issuer / brand logos get meaningful `alt` (e.g.
  alt="iDEAL"). Decorative emoji and icons get `aria-hidden="true"`.
- **Use of colour (1.4.1)**: errors and selected states never communicated by colour alone —
  pair with text, icon, or border-weight change (e.g. radio dot + border).
- **Reflow / resize (1.4.4, 1.4.10)**: use relative font sizes; page must work at 320px
  width and 200% zoom without horizontal scrolling or loss of content.

## Operable

- **Keyboard (2.1.1)**: everything operable by keyboard. CRITICAL TRAP: hiding radio inputs
  with `display: none` or `visibility: hidden` removes them from the tab order. Use a
  visually-hidden pattern instead and style the parent on `:focus-within` /
  `:has(input:focus-visible)`:
  ```css
  .pm-option input {
    position: absolute; opacity: 0; width: 1px; height: 1px;
    overflow: hidden; clip-path: inset(50%);
  }
  .pm-option:has(input:focus-visible) {
    outline: 3px solid var(--accent); outline-offset: 2px;
  }
  ```
- **Focus visible (2.4.7) + appearance (2.4.13 is AAA but aim high)**: never
  `outline: none` without an equal-or-better replacement. Add a global rule:
  ```css
  :focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
  ```
- **Target size (2.5.8, new in 2.2)**: interactive targets ≥ 24×24 CSS px (buttons,
  radio rows, step indicators). Payment buttons should comfortably exceed this.
- **Focus not obscured (2.4.11, new in 2.2)**: sticky headers/summaries must not cover the
  focused element; test tabbing through with sticky elements present.
- **Multi-step navigation**: step indicators that allow going back must be real `<button>`
  elements (or have full keyboard handling), with `aria-current="step"` on the active step.

## Understandable

- **Labels (3.3.2, 2.4.6)**: every input has a programmatically associated `<label for>`.
  Placeholder is never the only label.
- **Error identification (3.3.1, 3.3.3)**: on validation failure set `aria-invalid="true"`
  on the field and associate the error text via `aria-describedby`. Error text states what's
  wrong and how to fix it ("Enter a valid email address", not "Invalid").
- **Redundant entry (3.3.7, new in 2.2)**: multi-step forms must not re-ask information
  already provided in an earlier step (show a summary instead — which is also better UX).
- **Autocomplete (1.3.5)**: use `autocomplete` attributes on personal fields
  (given-name, family-name, email, street-address, postal-code, etc.).
- **Language (3.1.1)**: `<html lang="...">` matches the page language.

## Robust

- **Status messages (4.1.3)**: success/error/processing messages announced without focus
  moves — give status containers `role="alert"` (errors) or `role="status"` /
  `aria-live="polite"` (progress, success).
- **Name, role, value (4.1.2)**:
  - Frequency / mode toggles built from `<button>`s need `aria-pressed` (kept in sync by JS)
    or be converted to radio groups.
  - Radio groups get `<fieldset>` + `<legend>` (or `role="group"` + `aria-label`).
  - Loading states: disable the submit button AND update its accessible name
    ("Processing…").
- **Reduced motion**: respect `prefers-reduced-motion: reduce` — disable step transitions
  and counters' animations.

## Quick self-check before delivering a page

1. Tab through the entire flow — can you reach and operate every control, and always see
   where focus is?
2. Are all radios/checkboxes real inputs that remain focusable (no `display:none`)?
3. Run the muted text and input borders through a contrast checker.
4. Trigger every validation error — is it announced (role="alert") and associated
   (aria-describedby + aria-invalid)?
5. Zoom to 200% and resize to 320px — anything broken or cut off?
6. Does the multi-step flow avoid re-asking anything (3.3.7)?
