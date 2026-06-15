# Donation Page Structure & Content

A donation page is never just a bare payment card. Always build a complete, branded page with
supporting structure and content around the form — the form is one section of a page, not the
whole page. This applies to donation pages specifically (checkouts and sign-ups have their own
conventions); for those, still include a header and footer but adapt the surrounding content.

## Required page anatomy (donation pages)

Build these sections every time, top to bottom:

1. **Top navigation bar** — a slim site-level bar with a back link or the parent org/site name
   (e.g. "← FinDock"). Distinct from the campaign header below it.
2. **Organisation / campaign header** — the org logo + name lockup (e.g. a leaf mark +
   "FinDock for Gibbons"). This is the brand identity for the cause, sitting above the hero.
3. **Hero section** — a compelling headline (e.g. "Give Monthly. Create Change") plus
   supporting content: a short emotional subheadline/paragraph about the cause AND a relevant
   image or illustration. On a two-column layout the hero/imagery sits beside the form; on
   mobile it stacks above the form.
4. **The donation form** — the stepped or single-step form (per the intake), presented in a
   card. Includes the amount/frequency selection, payer details, and payment.
5. **Footer** — a real footer relevant to a donation page (see below).

Use a **two-column layout on desktop** (story/imagery on one side, form card on the other) that
collapses to a single column on mobile with the form below the hero content — per the
responsive rules in `page-quality.md`.

## Supporting content to include (pick what fits the cause)

The page should feel like a real campaign page, not a form with a logo. Include a selection of:

- **A cause-driven headline + subheadline** that states the impact, not just "Donate".
- **A hero image/illustration** relevant to the cause (use a real `<img>` with meaningful
  `alt`; if none is supplied, use a tasteful placeholder and tell the user to swap it).
- **Impact framing** — e.g. preset amounts annotated with what they fund ("$60 feeds a family
  for a month"), or a short impact stats strip ("2,847 animals rescued").
- **Trust/reassurance** — a short line on security ("Your donation is encrypted"), tax-receipt
  or charity-registration info where relevant, and recognisable payment method logos.
- **A short "why" paragraph or mission statement** near the hero or below the form.
- Optional: testimonial/quote, "where your money goes" breakdown, or supporter count.

Keep it focused — the page has one job (complete the donation). Don't bury the form under
marketing; the supporting content frames and motivates it.

## Footer (donation-page-relevant)

Always include a footer with content appropriate to a donation page, such as:

- Organisation name + registered charity / tax ID number where applicable
- Links: Privacy policy, Terms, Refund/cancellation policy, Contact
- A support path (email/phone) so a stuck donor has a lifeline
- A short line on payment security / "Payments processed securely via FinDock"
- Optional: copyright line, social links, "registered 501(c)(3) / ANBI / charity no." text

The footer is also a trust signal — a page with a proper footer reads as legitimate; a bare
form card does not.

## Header (donation-page-relevant)

The header is the two stacked elements from the anatomy: the slim top nav bar (site/back) and
the org/campaign lockup (logo + cause name). Keep the brand identity prominent — donors need to
trust who they're giving to.

## Reference example (the shape to aim for)

A monthly-giving page with: a top bar ("← FinDock"); an org lockup (leaf logo + "FinDock for
Gibbons"); a hero with a headline ("Give Monthly. Create Change") beside a circular cause image;
and a 3-step form card (Amount → Information → Payment) with a Give once / Monthly toggle,
preset amount grid ($5–$250), an "Other amount" field, and a Next button. The form is clearly
one part of a fuller, branded page — replicate that completeness.

## All other rules still apply

Field order (personal details before payment method), radio-first selector layout, method icons
from the response, enum label+image rendering, required-field validation, success/failure
routing, WCAG 2.2 AA, and responsive/mobile — all still apply to the form section within this
page structure.
