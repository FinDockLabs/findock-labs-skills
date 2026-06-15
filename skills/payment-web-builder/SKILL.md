---
name: payment-web-builder
description: >
  Build payment pages, donation forms, checkout flows, and membership sign-ups on the FinDock
  Payment API — standalone (hosted anywhere) or on-platform in Salesforce (Experience Cloud,
  Multi-Framework React, Lightning, Flow, Apex). Use whenever someone wants a payment page,
  donation form, checkout flow, or any UI that connects to FinDock. Trigger phrases: "build a
  payment form", "create a donation page", "payment page for FinDock", "checkout flow",
  "payment website", "integrate FinDock", "FinDock Payment API", "cpm.API_PaymentIntent_V2",
  "FinDock LWC/Flow/Apex payment", "payment form in Salesforce", "Multi-Framework payment",
  "Experience Cloud donation page". Supplies FinDock-specific knowledge (method catalogue,
  PaymentIntent contract, on-platform Apex entry points, enum/parameter rendering, UX rules)
  and adapts: carries the full standalone stack (proxy, auth, credentials) with no Salesforce
  host, and defers Salesforce scaffolding to the host (Vibes, Claude Code, Codex, Copilot,
  Cursor, …) when present.
---

## Tool compatibility & install

This is a single skill that adapts to where it runs (see "Division of labour" below). It
follows the open Agent Skills spec (agentskills.io) — the same `SKILL.md` + `references/`
structure consumed by Claude Code, OpenAI Codex, GitHub Copilot, Cursor, Gemini CLI,
**Salesforce Agentforce Vibes**, and 60+ other agents, all with the same progressive loading
(body on trigger, `references/` only when referenced).

- **Most agents (Claude Code, Codex, Copilot, Cursor, …)**: install with the open `skills` CLI —
  `npx skills add <owner>/<repo>` — which auto-detects your installed agents and links the skill
  into each. See the repo README for global (`-g`) and per-agent (`--agent`) options.
- **Agentforce Vibes**: Vibes does **not** auto-install third-party skills (only Salesforce's own
  `sf-skills`). Place the `payment-web-builder/` directory (name must match the `name` field) into
  `.a4drules/skills/` in your workspace, or `~/.a4drules/skills/` for global, and verify in the
  Skills panel.

This skill does not bundle or depend on any Salesforce CLI / `sf` tooling skill. When a task
actually involves deploying or manipulating a Salesforce org, tell the user that Salesforce
tooling (e.g. the `sf` CLI, or the org-aware features of your host) is needed for that step and
let them use it — do not try to reproduce it here. This skill's job is the FinDock contract and
the front-end, not the Salesforce platform mechanics.


# FinDock Payment Web Builder

Builds websites, payment forms, and front-end flows on top of the **FinDock Payment API v2** —
both standalone (hosted anywhere) and on-platform (inside Salesforce).

Always ground the code in the live FinDock docs before writing it — they are the source of truth
for endpoints, payload schemas, and processor-specific requirements. If the **FinDock docs MCP**
is configured (recommended), query it. If it isn't (common on Codex / Copilot / Cursor), fetch the
docs directly from `https://docs.findock.com` instead. Either way, do not guess the contract from
memory. See `references/docs-access.md` to wire up the docs MCP per tool, or for the fetch fallback.

---

## Division of labour — adapt to the host environment

This skill always supplies the **FinDock-specific knowledge** the host doesn't have: the
payment-method catalogue, the PaymentIntent contract, the on-platform Apex entry points
(`cpm.API_PaymentIntent_V2.postPaymentIntent`, `cpm.API_PaymentMethod_V2.getPaymentMethods`),
enum/parameter rendering, the page/UX rules, and the intake flow.

What it does with the *surrounding* mechanics depends on where it's running:

- **Inside an org-aware host with Salesforce tooling** (Agentforce Vibes, or Claude Code / Codex /
  Copilot / Cursor with the `sf` CLI or a Salesforce MCP available):
  let the host generate the Salesforce scaffolding — LWC boilerplate, `*.js-meta.xml`, Apex
  class structure, test classes, deployment, org metadata, permission sets, SFDX setup. Hand
  off with a clear FinDock spec (e.g. "generate an `@AuraEnabled` Apex method that calls
  `cpm.API_PaymentIntent_V2.postPaymentIntent` and returns the response") and fill in the
  FinDock specifics. Don't hand-roll what the host does better with live org awareness.
- **Standalone / external builds, or any host without Salesforce tooling**: this skill carries
  the full stack itself — standalone site scaffolding, the server-side OAuth proxy
  (`references/authentication.md`), the credential setup + doctor tooling
  (`references/credentials-setup.md`), the REST payment patterns, and Multi-Framework
  scaffolding. Use these directly.

Rule of thumb: if the deployment target is **Anywhere (standalone)**, you own the whole stack
(including auth/credentials). If it's **on-platform** (Experience Cloud, Multi-Framework,
Lightning, Flow) and an org-aware host is available, supply the FinDock contract and defer the
platform plumbing to the host. The intake's deployment question (Q2) determines which path you
are on.

---

## Workflow

### Step 0 — Intake (always run first, before writing any code)

Before doing anything else, ask the user these three questions in a single message.
Do not skip this step even if the request seems clear — the answers shape every decision.

**Question 1 — Form flow**
Ask whether the form should be single-step or multi-step:
- **Single-step** — everything on one page (personal details, payment method, submit). Simpler,
  faster to build, works well for short forms.
- **Multi-step** — split across multiple screens with a progress indicator (e.g. step 1: personal
  details → step 2: payment method → step 3: confirm & pay). Better UX for longer forms or when
  you want to reduce perceived complexity.

**Question 2 — Deployment target**
Ask where the page will be hosted. Present these four options (same list in all contexts):
- Anywhere (Netlify, Vercel, own server) — standalone web app, needs a server proxy for auth
- Salesforce Multi-Framework (Beta) — React running natively on the platform
- Salesforce Experience Cloud — FinDock Payment Experiences (native LWC components) or custom LWC + Apex
- Not sure yet

**If the user selects Experience Cloud, ask two follow-up sub-questions** (see
`references/experience-cloud.md` for the full product detail):
- `references/payment-method-selector-config.md` — Payment Method Selector component config (DRAFT schema; output feeds Pay Button / PaymentIntent)

- **2a. Which approach?**
  - FinDock out-of-the-box LWC components (managed Pay Button + Payment Method Selector + unmanaged Amount/Frequency selector)
  - Custom LWC + Apex (full control, hand-rolled around `cpm.API_PaymentIntent_V2`)

- **2b. If they chose the out-of-the-box components, ask how to assemble the form:**
  - Flow as the form builder (low-code, admin-maintained; FinDock provides Flow templates)
  - Build the whole form in LWC (embed the managed components in a custom LWC)

  > Note: the **Payment Method Selector is not yet LWC-enabled** — it currently works only in
  > the Flow builder. If they choose "build the whole form in LWC" and need method selection,
  > that part requires custom development today (render methods from
  > `cpm.API_PaymentMethod_V2.getPaymentMethods()` yourself). Flag this to the user. The Pay
  > Button and the unmanaged Amount & Frequency selector can be used in custom LWC now.

  > FinDock Payment Experiences is in a closed pilot — tell the user to contact FinDock Support
  > to participate, and verify current details against the docs MCP.

  > ⚠️ PUBLIC SITE PREREQUISITE — if the Experience Cloud page is public (guest users), WARN the
  > user: the **FinDock | ProcessingHub** must be installed *and connected* (from FinDock Setup),
  > the integration user the ProcessingHub is connected with must have the **FinDock Integration
  > User** permission set group, and the **FinDock Experience Cloud** permission set (included in
  > that package) must be assigned to the site's Guest User — or guest-user payments will fail.
  > See `references/experience-cloud.md`.

**Question 3 — Page type**
Ask what kind of page they want to build. Examples to offer:
- Donation page (one-time or recurring)
- Checkout / invoice payment
- Membership or subscription sign-up
- Fundraising campaign page
- Virtual terminal (staff-facing, internal)
- Something else (ask them to describe)

**Question 4 — Design reference**
Ask if they have screenshots, mockups, or example pages to use as visual reference.
- If yes: ask them to upload the image(s) before proceeding. Use the screenshots to inform layout, field order, colour choices, and copy.
- If no: proceed with a clean, functional default layout; offer to match a specific style if they describe it.

**Question 5 — Payment methods and processors**
Ask which payment methods and processors should be used — unless already specified in the prompt.

**Read `references/payment-methods-catalogue.md` first** and present options from the FinDock
catalogue, not from the org. The catalogue is the full list of what FinDock supports;
`GET /PaymentMethods` only returns what happens to be activated in one org and is for runtime
use, not for this conversation.

How to ask:
- First ask (or infer from the page type/context) which country or region the payers are in,
  then offer the relevant subset from the catalogue (e.g. Netherlands → iDEAL, Card, SEPA DD,
  PayPal, Tikkie; UK → Card, Bacs DD, wallets).
- If they pick methods: use those as the form's options, with processors from the catalogue.
- If they're not sure: default to a dynamic form that loads options from `GET /PaymentMethods`
  at runtime, so the form works regardless of org configuration.
- If chosen methods may not be activated in their org yet: mention that the relevant payment
  extension must be installed/activated in FinDock Setup → Processors & Methods.

Only move to Step 1 once all five questions are answered (or the user explicitly says to proceed without them).

---

### Step 1 — Clarify remaining technical details

With the intake answers in hand, fill in any remaining gaps:
- One-time payment, recurring, or both?
- Is there an existing Salesforce org to target, or is this a generic example?

> **Multi-Framework chosen in Step 0?** Follow the dedicated section and reference file below.
> Key difference: authentication is handled automatically by `@salesforce/sdk-data` — no OAuth proxy needed.

### Step 2 — Fetch the API contract from FinDock docs

Always query the MCP for the relevant endpoints before writing any code.
See the "Using the FinDock Docs MCP" section below.

### Step 3 — Build the flow

Follow the canonical payment flow (see below). Apply any design reference from the screenshots.

### Step 4 — Handle webhooks or polling

If the user needs post-payment status updates, implement webhook handling or
`/PaymentIntent/{ID}` polling as appropriate.

### Step 5 — Review and package

Present the final code with clear `// FinDock:` inline comments at each FinDock-specific step.

### Step 6 — Verify credentials (standalone targets only)

For "Anywhere" deployments, ship the credentials tooling from
`references/credentials-setup.md`: `setup.mjs`, `.env.example`, a gitignored `.env`, and
`setup`/`doctor` npm scripts. Then tell the user to run `npm run setup` (auto-detects an
authenticated Salesforce CLI — no Connected App needed for dev) followed by `npm run doctor`
(verifies the token, the FinDock Integration User permission set, and active payment methods,
with a specific fix per failure). If shell access is available, offer to run both directly
and interpret the results. Skip this step for Multi-Framework, Experience Cloud, and on-platform Apex/LWC/Flow targets —
the platform handles auth there (on-platform calls the Apex class directly, no token at all).

---

## The Canonical FinDock Payment Flow

Every FinDock-powered front-end follows this sequence:

```
1. GET /PaymentMethods       → discover available processors & methods
2. GET /SourceConnector      → discover available source connectors
3. GET /PackageActions       → discover any package-specific actions (e.g. Gift Aid)
4. POST /PaymentIntent       → submit payment, receive RedirectURL
5. Redirect payer to URL     → PSP handles the payment
6. PSP redirects to          → SuccessURL / FailureURL (you provide these in step 4)
7. Webhook / GET /PaymentIntent/{ID} → confirm final status
```

Steps 1–3 are informational and should be called at page load (or cached) to build a dynamic UI.

---

## Key API Concepts

### Base URL
```
https://{instance}.my.salesforce.com/services/apexrest/cpm/v2
```

### Authentication
OAuth2 Bearer token. For browser-based apps this typically means:
- A server-side component handles token acquisition/refresh
- The front-end calls a thin backend proxy that adds the `Authorization` header
- Never expose `client_id` / `client_secret` in browser JS

When the user asks how to set up authentication, or when building a full working integration
(not just a front-end snippet), read `references/authentication.md` and include the relevant
steps. It covers:
- Creating a Connected App in Salesforce (Consumer Key + Secret)
- The OAuth2 web server flow (browser login → auth code → access + refresh tokens)
- Using the access token in proxy calls to the FinDock API
- Refreshing the token when it expires (with 401 retry pattern)
- JWT Bearer Flow for headless / service-to-service integrations

For standalone builds, also ship the guided setup tooling from
`references/credentials-setup.md` (`npm run setup` with sf CLI auto-detect + `npm run doctor`
verification) — see Workflow Step 6.

### PaymentIntent payload structure
```json
{
  "SuccessURL": "https://yoursite.com/thank-you",
  "FailureURL": "https://yoursite.com/payment-failed",
  "WebhookURL": "https://yoursite.com/api/webhook",  // optional
  "Payer": {
    "Contact": {
      "SalesforceFields": {
        "FirstName": "Jane",
        "LastName": "Doe",
        "Email": "jane@example.com"
      }
    }
  },
  "OneTime": {
    "Amount": 25.00,
    "PaymentMethod": "CreditCard",
    "Target": "Stripe1"           // OPTIONAL — omit to use the org's default processor
  }
}
```

For recurring, replace `OneTime` with `Recurring` (or include both for PSPs that require
an initial authorisation payment alongside a recurring setup).

### Payer object
- Use `Contact` for individuals, `Account` for organisations
- Use `Account` with `RecordTypeName: "PersonAccount"` for NPC/Fundraising orgs
- Always include enough fields to satisfy the org's deduplication rules (ask user)

### Dynamic vs static forms
- **Static**: hardcode `PaymentMethod` — fine for single-PSP setups
- **Dynamic**: call `GET /PaymentMethods` first, render a method selector, then populate
  `PaymentMethod` (and optionally `Target`) from the response — recommended for multi-PSP orgs

### Target is optional
If `Target` is omitted from the payload, FinDock automatically uses the **default processor**
configured for that payment method in the org. Default to omitting it; only set `Target`
explicitly when the user wants to override the default (e.g. multiple processors for the
same method).

### SuccessURL / FailureURL
These are PSP redirect targets after the payer completes/cancels. Pass them in the
PaymentIntent body. The PSP redirects the browser here; you can append query parameters
server-side to carry the `PaymentIntentId` through.

---

## Code Patterns

### Pattern 1 — Minimal one-time payment (plain HTML + fetch)

See `references/one-time-payment.md` for a full annotated HTML example.

### Pattern 2 — Dynamic payment method selector

See `references/dynamic-payment-methods.md` for a full React example that:
- Calls `GET /PaymentMethods` on mount
- Renders method options
- Submits a PaymentIntent with the selected method

### Pattern 3 — Recurring payment form

See `references/recurring-payment.md` for recurring setup with optional initial payment.

### Pattern 4 — Webhook handler (Node.js / Express)

See `references/webhook-handler.md` for parsing `installment.status_change` and
`paymentIntent.processed` events.

### Pattern 5 — React on Salesforce (Multi-Framework beta)

See `references/salesforce-multi-framework.md` for a full walkthrough: scaffold, SDK setup,
FinDock PaymentIntent call without a proxy, and deploy steps.

### Parameter rendering — enums, labels, images

See `references/parameters-and-enums.md` — **required reading whenever a form renders
method-specific parameters** (iDEAL issuer, card brand, ACH account type, etc.).
Enum parameters in the `/PaymentMethods` response contain `value` + `label` + `image.svg`
per option: show the label and image, send the value, never hardcode option lists.
Also contains the tokenization field inventory (card / bankAccount forms) per processor
with length constraints.

### Pattern 6 — Experience Cloud (FinDock Payment Experiences)

See `references/experience-cloud.md`. Two routes: **(A) FinDock out-of-the-box LWC components**
(managed Pay Button + Payment Method Selector + unmanaged Amount/Frequency selector), assembled
either via **Flow** (low-code, templates available) or **custom LWC**; or **(B) custom LWC + Apex**
around `cpm.API_PaymentIntent_V2.postPaymentIntent()`. The Payment Method Selector is not yet
LWC-enabled (Flow only) — in a custom LWC, method selection needs custom development today.
FinDock Payment Experiences is in a closed pilot; verify current details via the docs MCP.

### Pattern 7 — On-platform: Apex / LWC / Flow

See `references/on-platform-apex-lwc-flow.md`. For integrations that run **inside Salesforce**
rather than as an external site: call the FinDock managed Apex methods directly —
`cpm.API_PaymentIntent_V2.postPaymentIntent()` to create/pay/update payments and
`cpm.API_PaymentMethod_V2.getPaymentMethods()` to list methods — with LWC and Flow layers on
top (no proxy, token, or CORS). **Do NOT call the public REST endpoint from Experience Cloud
or any on-platform code** — the REST API is for external clients only. All UI rules (selector
layout, enums, WCAG, responsive) still apply to the LWC layer; the authentication reference and
credentials setup (Step 6) do NOT apply. Verify exact method parameter/return types against the
docs MCP and the FinDockLabs repo before finalizing.

---

## Salesforce Multi-Framework (Beta)

Use this when the payment form should run **natively inside Salesforce** as a Multi-Framework
React app — accessible from the App Launcher or embedded in an Experience Cloud site.

### When to suggest this target

- The user is building an internal employee-facing payment tool (e.g. virtual terminal, invoice
  payment portal) inside Salesforce
- They want to avoid building and hosting a separate web server
- The org is already on sandbox/scratch org with Multi-Framework enabled
- They want to reuse the Salesforce session — no separate login for the payment form

### Key difference from standalone React

In a standalone app you need a server proxy to hold the Bearer token. In a Multi-Framework app,
`@salesforce/sdk-data` handles Salesforce auth automatically. You can call Apex methods or
GraphQL directly. For the FinDock Payment API specifically, you have two options:

| Approach | How |
|----------|-----|
| **Call via Apex** | Write an Apex method that calls the FinDock Payment API internally, invoke it from React using `sdk.fetch()` — no CORS, no token handling |
| **Call the REST API directly** | Use the session token from `createDataSDK()` as the Bearer token; add the Salesforce origin to CORS in Setup |

The Apex approach is cleaner for production. The direct REST call is simpler for prototyping.

### Beta constraints to communicate

Always tell the user when generating Multi-Framework output:
- **Beta only** — sandbox and scratch orgs only; English default language orgs only
- Cannot be deployed to production orgs yet
- Lightning App Builder drag-and-drop not yet supported
- Enabling Multi-Framework **cannot be undone** in the org

### Project structure

```
force-app/main/default/
└── uiBundles/
    └── findockPayment/
        ├── findockPayment.uiBundle-meta.xml
        └── src/
            ├── main.tsx
            ├── App.tsx
            └── components/
                └── PaymentForm.tsx
```

### Scaffold command

```bash
sf template generate ui-bundle --name findockPayment
```

Read `references/salesforce-multi-framework.md` for the full component code, Apex proxy
pattern, and deployment steps.

---

## Using the FinDock Docs MCP

Include the MCP in all research calls:

```javascript
mcp_servers: [
  {
    "type": "url",
    "url": "https://docs.findock.com/mcp",
    "name": "findock-docs"
  }
]
```

Query it for:
- Exact endpoint schemas before building a payload
- Payment method–specific parameters (e.g. IBAN for SEPA, phone for Swish m-commerce)
- Processor-specific requirements (e.g. Adyen requires `ReturnURL`, Stripe uses redirect)
- Source connector field names (NPSP, NPC/Fundraising, standard FinDock)
- Package action schemas (Gift Aid, etc.)

---

## CORS Setup (important for browser-based testing)

If calling the Salesforce API directly from a browser (only for dev/testing):
1. Salesforce Setup → Security → CORS
2. Add the origin of your page (e.g. `https://yoursite.com` or `https://localhost:3000`)
3. Enable "CORS for OAuth endpoints"

For production, always use a server-side proxy to keep credentials out of the browser.

---

## Page Quality Requirements (mandatory for every page)

Before building ANY page, read BOTH:
- `references/accessibility.md` — every page MUST be WCAG 2.2 AA compliant (focus-visible
  everywhere, no display:none on radio inputs, 4.5:1 text / 3:1 border contrast, aria-invalid
  + aria-describedby on errors, role="alert"/"status" on messages, aria-pressed on toggles,
  reduced-motion support)
- `references/page-quality.md` — every page MUST be responsive/optimized for both web and
  mobile (320px+, single column on mobile, 44px tap targets, 16px+ inputs, correct
  inputmode/autocomplete) and follow the conversion best practices (transparent live totals,
  exact amount in the pay button, lean forms, trust indicators, inline real-time validation,
  policy + support links, no clutter on the payment step)

These are not optional polish steps — non-compliant output is incomplete output.

Also mandatory for every form (see `references/required-fields-and-errors.md`):
- **Required fields**: validate client-side before submitting. At minimum a Contact payer
  needs FirstName + LastName (+ Email for receipts/dedup); Amount must be > 0; a method must be
  selected; and every parameter marked `Required: true` in the `/PaymentMethods` response must
  be present (IBAN, account/routing, issuer, etc.). Block submit until valid with inline,
  field-level messages.
- **Response handling**: always resolve the response — RedirectURL → PSP (which returns to
  SuccessURL/FailureURL); non-redirect success → success state; Errors → categorized handling.
  Never leave the payer on a spinning button. Success/failure may be built into the form or a
  standalone page, but one must always be reached.
- **Error categorization**: error codes **201–205 are the ONLY payer-recoverable** ones (bad
  IBAN/BIC/sort code/address for SEPA/Bacs) — show field-level guidance and let them retry.
  Every other code (010–012, 200, 206, 998, 999, any 4xx/5xx/network) is NOT recoverable →
  log for devs, show ONE generic error message (or go to the failure page). Never surface raw
  error text/codes to the payer for non-recoverable errors.
- **Donation pages need full page structure**: a donation page is never a bare form card.
  Always include a top nav bar, an org/campaign header (logo + cause name), a hero (headline +
  supporting copy + relevant image), the form card, and a donation-relevant footer (charity/tax
  info, policy links, support contact, security line). Add supporting content (impact framing,
  trust signals, a short "why"). See `references/donation-page-structure.md`. Checkouts and
  sign-ups also get a header and footer, adapted to their context.
- **Payment method icons**: every method option in a selector MUST display its logo, read
  from `PaymentMethods.Processors[].image.svg` (the image is on the PROCESSOR, not the
  method — `method.image.svg` does not exist). Never omit the icon or use generic
  placeholders. Full guidance in the "Payment method, issuer, and card brand images" section.

## Output Guidelines

- Always include a `// FinDock:` inline comment at each FinDock-specific step so the
  developer understands what's happening and why
- Separate concerns clearly: data collection form, API call logic, redirect/status handling
- If producing a multi-file output, show the structure first:
  ```
  payment-form/
  ├── index.html     (or App.jsx)
  ├── api.js         (FinDock API calls)
  └── webhook.js     (optional — server-side webhook handler)
  ```
- When the user hasn't specified a framework, default to **plain HTML + vanilla JS** for
  simplicity; offer to convert to React if they prefer
- Never hardcode `client_id`, `client_secret`, or Bearer tokens in browser-facing files —
  always show a placeholder comment and note that a proxy is needed

### Form field order (always follow this sequence)

1. Personal details (name, email, address, etc.)
2. Payment method selection
3. Method-specific fields (IBAN, phone number, etc.)
4. Submit button

### Payment method selector row layout (always this order, left to right)

1. Radio button (the visible radio indicator comes FIRST)
2. Payment method icon/logo
3. Payment method label

Never place the radio indicator at the end of the row. The same order applies to enum
option rows (issuers, card brands).

Never put payment method selection above personal details, even if it seems logical to
filter the form first. Collecting the payer's identity first is the correct UX pattern.

### Payment method, issuer, and card brand images (REQUIRED — do not skip)

Every payment method option in a selector MUST show its official FinDock logo. There are
exactly two valid sources for the image, and FinDock hosts the only correct artwork. **Never
hand-draw, approximate, inline, or substitute a generic/placeholder icon, an emoji, or a
third-party CDN logo.** "The controller returned no image URL, so I drew my own SVG" is a
bug to fix in the data source — not an acceptable outcome (see the anti-pattern callout).

**1. Authoritative source — the `/PaymentMethods` response.** The image lives on the
**processor**, not the method: `PaymentMethods.Processors[].image.svg`. A common bug is
reading `method.image.svg` — that path does NOT exist, renders an empty `<img>`, and drops
the icon. Always read it from the processor object and use the URL **verbatim**.

```javascript
// FinDock: iterate methods, pick the default (or chosen) processor, read image off THAT.
methods.forEach(method => {
  const proc = method.Processors?.find(p => p.IsDefault) ?? method.Processors?.[0];
  const imgUrl = proc?.image?.svg;   // ← correct path: method.Processors[].image.svg
  const img = imgUrl
    ? `<img src="${imgUrl}" alt="${method.Name}" height="24"
           onerror="this.style.display='none'">`
    : '';
  // ... render: radio first, then img, then label (see selector layout rule)
});
```

**2. Fallback / explanation — the URL pattern.** The `image.svg` value above always resolves
to this pattern, so you can construct it yourself when you don't have the live response
(e.g. a hardcoded list, or an Apex controller that reads methods from a picklist instead of
calling `/PaymentMethods`):

```
https://external.findock.com/icon/payment-methods/<name>.svg
```

`<name>` = the payment-method **Name lowercased with ALL non-alphanumeric characters
removed**. Worked examples (verified against a live org):

| Method Name | `<name>` | Icon URL |
|---|---|---|
| `CreditCard` | `creditcard` | `…/icon/payment-methods/creditcard.svg` |
| `SEPA Direct Debit` | `sepadirectdebit` | `…/icon/payment-methods/sepadirectdebit.svg` |
| `ACH Direct Debit` | `achdirectdebit` | `…/icon/payment-methods/achdirectdebit.svg` |
| `Przelewy24` | `przelewy24` | `…/icon/payment-methods/przelewy24.svg` |
| `PAD` | `pad` | `…/icon/payment-methods/pad.svg` |

```javascript
const iconUrl = name =>
  `https://external.findock.com/icon/payment-methods/${name.toLowerCase().replace(/[^a-z0-9]/g, '')}.svg`;
```

This same normalization maps a **`cpm__Installment__c.cpm__Payment_Method__c` picklist
value** directly to its icon filename — the picklist values equal the API method Names. So a
form (or Apex controller) that reads available methods from the picklist can resolve every
icon **without an extra `/PaymentMethods` callout**, just by normalizing the picklist value.

**Delivery — pick one, both are valid:**

- **(a) Hotlink** the response's `image.svg` (or the constructed URL) directly. Requires
  adding `external.findock.com` — and `images.findock.com` for issuer/brand enum images — as
  a **CSP Trusted Site** (Setup → Security → CSP Trusted Sites) so the browser can load them.
- **(b) Bundle** the SVGs as a **static resource** and serve them same-origin. No CSP Trusted
  Site needed. **Preferred for Experience Cloud / guest-user sites**, where you control the
  exact method set and want to avoid a cross-origin dependency on the guest page. Download
  each method's SVG from the URL pattern above, name the files by the normalized `<name>`,
  and resolve `staticResource + '/' + <name> + '.svg'`.

**Anti-pattern — read this before improvising an icon.** If your data source doesn't surface
an image URL (e.g. an Apex controller built off the picklist that doesn't add one), the fix
is to **add the URL via the normalization rule** or to call `/PaymentMethods` — NOT to
fabricate artwork. Never ship hand-drawn SVGs, font/emoji glyphs, generic card icons, or
"close enough" brand logos. A missing real icon is a data-source bug; a fake icon is a
visual-correctness bug shipped to the payer.

**Issuer & card-brand enum images** (e.g. iDEAL `issuer`, `cardBrand`) follow the same rules
but live in **per-method sub-folders** and are documented in full — including the URL pattern,
the `images.findock.com` vs `external.findock.com` distinction, and the rendering pattern —
in `references/parameters-and-enums.md`. Always render them from the response's `Enum` array
(label + `image.svg`), never as free text or hardcoded lists.

---

## Common Mistakes to Avoid

| Mistake | Correct approach |
|---------|-----------------|
| Sending `client_secret` from browser | Use a server proxy |
| Hardcoding `Target` unnecessarily | Omit it — FinDock uses the org default; only set to override |
| Assuming `RedirectURL` in response is optional | Always handle it — most PSPs require a redirect |
| Using `Contact.Email` (non-existent SF field) | Use `Contact.SalesforceFields.Email` |
| Forgetting CORS configuration | Required for direct browser calls (dev only) |
| Ignoring `PackageActions` | Required for Gift Aid and some other extensions |
| Assuming a flat recurring object | Some orgs use NPSP (RecurringDonation) or NPC (GiftCommitment) |
| Building a proxy for Multi-Framework apps | Use `@salesforce/sdk-data` or an Apex method — auth is free |
| Deploying Multi-Framework to production | Beta: sandbox/scratch orgs only |
| Putting payment method selector before personal details | Personal details always come first |
| Omitting method icons / reading `method.image.svg` | Image is on the PROCESSOR: `method.Processors[].image.svg`. Always render it, never a placeholder |
| Hand-drawing / faking an icon when the controller returns no image URL | Fix the data source: read `image.svg` from `/PaymentMethods`, or build `external.findock.com/icon/payment-methods/<name>.svg` from the normalized method name (or picklist value). Never ship invented artwork |
| Donation page = bare form card | Build full page: nav, org header, hero+image+copy, form, donation-relevant footer (see donation-page-structure.md) |
| Public Experience Cloud page without ProcessingHub | Warn: install AND connect FinDock \| ProcessingHub (from FinDock Setup), assign FinDock Integration User permission set group to the ProcessingHub's integration user, and assign FinDock Experience Cloud permission set to the Guest User — else guest payments fail |
| Hardcoding enum options (issuers, brands, account types) | Render from the response's `Enum` array: show `label` + `image.svg`, send `value` |
| Hiding radio inputs with `display:none` | Breaks keyboard access — use the visually-hidden pattern from accessibility.md |
| Desktop-only layouts, <16px mobile inputs, tiny tap targets | Follow page-quality.md: 320px+, 44px targets, 16px inputs |
| Validation only on submit, generic error text | Inline real-time validation with specific fix guidance |
| Calling the REST endpoint from Experience Cloud / on-platform | Use Apex `cpm.API_PaymentIntent_V2.postPaymentIntent()` + `cpm.API_PaymentMethod_V2.getPaymentMethods()` — REST is external-only |
| Not validating required fields before submit | Validate Contact FirstName+LastName, Amount>0, method, and all `Required:true` params client-side |
| Leaving the payer on a spinner / no success or failure outcome | Always route to success or failure (in-form panel or standalone page) |
| Showing raw error text/codes for non-recoverable errors | Only 201–205 are payer-recoverable (inline); all others → one generic message + log for devs |
