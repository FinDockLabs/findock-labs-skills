---
name: generate-payment-config
description: >
  Generate or reset paymentMethodConfiguration.js for this LWC project.
  Four modes: (1) empty template for pre-org planning/specs, (2) full list of
  all methods for a given processor or region using a static example library,
  (3) selective — only the methods the user names, from the same static
  library, (4) generate from a live, connected org via
  `npm run generate:config -- --org <alias>` — real processors, methods, and
  parameters, optionally narrowed to specific methods after generation.
  Trigger phrases: "generate payment config", "create paymentMethodConfiguration",
  "payment config template", "payment config for Stripe", "payment config for Netherlands",
  "fill payment methods", "empty payment config", "no org yet", "from my org",
  "from the org", "real parameters", "live data", "org alias", "generate:config".
---

Generates `force-app/main/default/lwc/paymentForm/paymentMethodConfiguration.js`.

## Compact args syntax

Users may pass args inline after `/generate-payment-config`. Parse in this order:

```
/generate-payment-config [empty]
/generate-payment-config <orgAlias> [<processor>] [target="<value>"]
/generate-payment-config <processor|region> [target="<value>"]
```

| Pattern | Mode |
|---|---|
| `empty` | A |
| starts with an org alias (e.g. `MyScratch`, `LWCScratch`) | D |
| starts with a processor name (`Stripe`, `GoCardless`, `Mollie`) or region | B |
| lists specific method names, no org alias | C |

When all required info is present in args, skip questions and execute immediately.

**Full args syntax:**
```
/generate-payment-config <orgAlias> [<processor>] [<method1>,<method2>,...] [target="<value>"]
```

- `<orgAlias>` — Salesforce org alias (e.g. `MyScratch`). Triggers Mode D.
- `<processor>` — optional filter: `Stripe`, `GoCardless`, `Mollie`. Keep only entries matching this processor after the script runs.
- `<method1>,<method2>` — optional comma-separated list of method names to keep (e.g. `CreditCard,Ideal`). Applied after processor filter.
- `target="<value>"` — set this string on every remaining entry's `target` field.

**Common invocations:**
```
/generate-payment-config MyScratch
/generate-payment-config MyScratch Stripe target="My Stripe Account"
/generate-payment-config MyScratch Stripe CreditCard,Ideal target="My Stripe Account (New)"
/generate-payment-config Stripe
/generate-payment-config Netherlands
/generate-payment-config empty
```

---

## Mode detection (when args are absent or ambiguous)

| Signal | Mode |
|---|---|
| "empty", "no methods yet", "no org", "planning", "template" | **A** |
| "all methods", "all Stripe methods", "all for [region]" (no real org) | **B** |
| names specific methods, no real org | **C** |
| names an org alias, "from my org", "real data", "live data", "generate:config" | **D** |
| no signal | Ask ONE question: "Empty template, all methods for a processor (static), specific methods (static), or from a live org?" |

Live org always wins. If the user names both an org alias AND specific methods, use Mode D + Step D3 narrowing.

---

## Mode A — Empty template

Write immediately, no questions:

```javascript
/**
 * Payment method configuration for the paymentForm component.
 * Edit to match the payment methods and processors activated in your org.
 *
 * HOW TO POPULATE:
 *   npm run generate:config -- --org <orgAlias>   (auto-generate from org)
 *   /generate-payment-config <orgAlias>            (via Claude Code)
 *
 * TARGET FIELD: FinDock Setup → Processors & Methods → [processor] → Accounts tab.
 */
export const PAYMENT_METHOD_CONFIG = [];
```

---

## Mode B — Full list (static library)

Read `references/entries-library.md` first. Use ALL entries for the requested processor.
Set `isDefaultOneTime: true` on the first `enabledOneTime` entry, `isDefaultRecurring: true` on the first `enabledRecurring` entry. Leave `target: ''`.

If the user named a region, use the regional presets table in `references/entries-library.md`.

After writing, tell the user: entries come from the static library (not org-verified) — parameters may differ from what the org actually exposes. Mode D pulls real data.

---

## Mode C — Selective (static library)

Read `references/entries-library.md` first. Generate only the requested entries.
If a method is missing from the library, add a placeholder entry with `// TODO: verify parameters`.
Set defaults as in Mode B.

---

## Mode D — Generate from a live org

### D1 — Identify the org alias
If named in args → use it. Otherwise ask: "Which org alias? (from `sf org list`)"

### D2 — Run the generator
```
npm run generate:config -- --org <orgAlias>
```
This calls `GET /PaymentMethods` via anonymous Apex and overwrites `paymentMethodConfiguration.js` with every active method from the org, including its full real `parameters` list. `target` is always left empty by the script.

Surface any failure verbatim (auth errors, org not found, no active methods). Do NOT fall back to the static library on failure.

### D3 — Set target (if provided in args)
If the user passed `target="<value>"`, after the script succeeds read the generated file and set that value on every entry's `target` field.

### D4 — Narrow (if specific methods/processor named)
If the user also named specific methods or a processor, remove non-matching entries from the generated file. Keep the real `parameters` arrays — do not replace with static library versions. Re-assign `isDefaultOneTime`/`isDefaultRecurring` if needed.

### D5 — Report
Tell the user: org alias used, total entries from org, entries remaining after narrowing (if any), and that `target` needs manual fill-in unless it was passed in args.
