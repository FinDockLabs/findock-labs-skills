# Page Quality — Responsive Design & Conversion Best Practices

Required reading (together with `accessibility.md`) before building ANY page. These rules
apply to every page the skill produces. Conversion practices are distilled from Stripe's
payment page guidance (stripe.com/resources/more/payment-page-template-best-practices) and
adapted to FinDock contexts (donation pages, checkouts, sign-ups).

---

## Responsive / mobile requirements (every page)

Most payment traffic is mobile. Build mobile and desktop as equals — never desktop-first
with an afterthought breakpoint.

- **Works from 320px to widescreen** with no horizontal scrolling and no content loss.
  Test mentally at 320 / 375 / 768 / 1024+.
- **Single column on mobile**: multi-column grids (`field-group`, two-panel layouts)
  collapse below ~760px. Order summaries move above the form (`order: -1`) or into a
  collapsible section on mobile.
- **Tap targets ≥ 44×44 CSS px** for primary actions on mobile (WCAG 2.5.8 minimum is 24px,
  but 44px is the practical target for payment buttons, radio rows, amount presets).
- **Inputs ≥ 16px font-size on mobile** — anything smaller triggers automatic zoom on iOS
  and breaks the layout. Use `font-size: 1rem` (or a mobile media query bumping it).
- **Mobile keyboards**: set `inputmode` and `type` so the right keyboard opens —
  `type="email"`, `inputmode="numeric"` for amounts/postcodes/card fields,
  `inputmode="tel"` for phone, `autocomplete` attributes throughout.
- **Sticky elements**: a sticky pay button or order total on mobile is good practice, but
  it must not obscure focused fields (WCAG 2.4.11) — add `scroll-padding-bottom`.
- **`viewport` meta** with `width=device-width, initial-scale=1` (never
  `user-scalable=no` — blocking zoom is an accessibility failure).
- **Performance**: single-file pages, system/Google fonts with `display=swap`, SVG logos
  from FinDock CDNs, no heavy libraries for simple forms. Slow pages lose payments.

## Conversion best practices (Stripe-derived)

### Always include
1. **Transparent totals** — show the full amount including any fees up front; update the
   total in real time when the payer changes options. Never "fees may apply". For
   checkouts: itemised order summary with a visible final total. The summary is the
   receipt preview — it prevents disputes.
2. **Lean forms** — every extra field is a drop-off point. Collect only what's needed to
   process the payment (plus org deduplication needs). Never force account creation.
   This pairs with WCAG 3.3.7 (no redundant entry in multi-step flows).
3. **Multiple payment methods** — offer at least one alternative to cards, regionally
   relevant (use the payment-methods-catalogue reference). Surface familiar local methods
   (iDEAL in NL, Swish in SE, etc.).
4. **A specific, prominent pay button** — exact amount in the label ("Pay €43.20",
   "Donate €25/month"), visually distinct, at the bottom where expected. Keep the label
   amount in sync with the live total.
5. **Trust indicators** — security reassurance copy ("Your payment is encrypted"),
   recognisable payment method logos (from FinDock CDN), placed near the payment fields.
6. **Real-time validation** — validate inline as the payer types or on blur, never only
   on submit. Error message next to the field, stating how to fix it. (Combine with the
   aria-invalid / aria-describedby pattern from accessibility.md.)
7. **Progress indicator on multi-step flows** — numbered steps with clear titles so the
   payer knows where they are and how much is left.
8. **Policy links in the footer** — privacy, terms, refund policy; for payments add
   binding language near the button ("By paying, you agree to ...").
9. **A support path** — an email/phone/chat line near the footer so a stuck payer has a
   lifeline instead of abandoning.
10. **Brand consistency** — the page must feel like it belongs to the organisation: logo
    placement, colours, typography, familiar language. Generic-looking payment pages read
    as suspicious.

### Never do
- **Clutter at the last step** — no upsells, exit popups, full navigation menus, or
  competing CTAs on the payment step. The page has one job.
- **Hidden costs** — surprise fees at the final step tank trust and conversion.
- **Tiny tap targets, overlapping fields, forms that don't scroll on small screens** —
  the classic mobile failures; test the full flow at mobile sizes.
- **Account walls** — guest payment always possible.

### Optional, when relevant
- **Promo/discount code field** (checkouts): unobtrusive, collapsible if rarely used,
  clearly labelled — never dominant in the layout.
- **Impact hints** (donations): small labels on preset amounts ("€25 plants a tree")
  measurably help conversion on charity pages.

## Delivery self-check

1. Resize to 320px — single column, nothing clipped, no horizontal scroll?
2. Are all totals visible and live-updating, with the exact amount in the pay button?
3. Inputs ≥16px on mobile, correct keyboards (`inputmode`/`type`), `autocomplete` set?
4. Trust copy + method logos near the payment fields; policy + support links in footer?
5. Validation fires inline with field-level messages, not just on submit?
6. Nothing on the payment step competes with the pay button?
