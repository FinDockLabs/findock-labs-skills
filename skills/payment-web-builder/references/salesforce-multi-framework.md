# Pattern 5 — React on Salesforce Multi-Framework (GA)

Use this when the deployment target from intake Question 1 is **Salesforce Multi-Framework**: the
payment experience is (at least partly) **React**, built as a Salesforce **UI bundle** and served by
the platform — either as an **internal** app (App Launcher, `*.my.salesforce.app`) or as an
**external** app (a Digital Experience site, `*.my.site.com`, guest or authenticated).

> **Status / grounding (verified Sept 2026 against Salesforce docs).** Salesforce Multi-Framework is
> **generally available** since Summer '26: it deploys to **production**, sandbox, Developer Edition
> and scratch orgs on **Hyperforce** (Enterprise, Performance, Unlimited, Developer, Partner Developer;
> English default language; not Alibaba Cloud / Government Cloud). Remaining limitations that matter
> here: **packaging and namespaced orgs are unsupported**, a React Experience Cloud site **cannot be
> edited in Experience Builder**, React components **cannot yet be dropped onto Lightning / Experience
> Builder pages** (micro-frontends are a Developer Preview), and the Data SDK moved from
> `@salesforce/sdk-data` (beta) to **`@salesforce/platform-sdk`** (GA, breaking API change). FinDock
> Payment Experiences (the managed Pay Button / Payment Method Selector you may embed) is still in a
> closed pilot — see `experience-cloud.md`. Re-verify both before finalizing.

Sources (official): Multi-Framework guide — *React Development Using Multi-Framework*
(`developer.salesforce.com/docs/platform/multiframework/guide/reactdev-overview.html`), *Configure Your
Org for React App Development* (`…/reactdev-setup.html`), *Integrate Your React App with the Headless
360 Platform* (`…/reactdev-integrate.html`), *Multi-Framework Vs LWC* (`…/reactdev-lwc-diff.html`);
Developers blog *Build with React on Salesforce: Multi-Framework Is Now GA* (July 2026); LWC guide
*Use Components Outside Salesforce with Lightning Out 2.0* (`…/lwc/guide/lightning-out-intro.html`,
`lightning-out-architecture.html`, `lightning-out-events.html`, `lightning-out-limitations.html`);
Help *Prepare to Build / Set Up Authentication for / Build a Lightning Out 2.0 App*; recipes repo
`github.com/trailheadapps/multiframework-recipes` (React, Apex REST and micro-frontend samples).

---

## Building blocks (what every route below is made of)

| Piece | What it is | Notes |
|---|---|---|
| **UIBundle** | Metadata type holding the built React app (`force-app/main/default/uiBundles/<Name>/`, `<Name>.uibundle-meta.xml`, `ui-bundle.json`, `dist/`) | Up to 2,500 files. Versioned, deployed like any metadata. |
| **`<target>`** | `CustomApplication` (internal, App Launcher; needs `applications/*.app-meta.xml` with `<uiBundle>c__<Name></uiBundle>` + a permission set) or `Experience` (external; needs Network, CustomSite, DigitalExperienceConfig, DigitalExperienceBundle with `appContainer: true` / `appSpace: c__<Name>`) | The beta `AppLauncher` target is deprecated. A bundle without a target is not reachable anywhere. |
| **Templates** | `sf template generate ui-bundle -n <Name> --template reactbasic` (bundle only) or `sf template generate project` with `reactinternalapp` / `reactexternalapp` (bundle + required metadata) | External template ships the site shell, navigation, authentication, object search. |
| **Data SDK** | `@salesforce/platform-sdk`: `createDataSDK()` → `sdk.graphql?.query()` / `.mutate()` for records, `sdk.fetch?.()` for **Apex REST**, UI API, Connect | Handles session, CSRF and base URL. **`@AuraEnabled` Apex has no invocation path from React** — only `@RestResource` classes via `/services/apexrest/…`. |
| **CSP Trusted Sites** | `cspTrustedSites/*.cspTrustedSite-meta.xml` for every external origin the page touches (img/connect/font/style/media/frame) | Needed for `external.findock.com` / `images.findock.com` icons unless you bundle the SVGs. |
| **Salesforce app domain** | Internal apps run on `https://<org>--c.<instance>.my.salesforce.app/app/c__<Name>` | Enable under Setup → *React Development with Salesforce Multi-Framework*; Salesforce Edge Network required. |

Defer all of this scaffolding to the host's Salesforce tooling when available (`sf-skills`:
`building-ui-bundle-app`, `generating-ui-bundle-metadata`, `generating-ui-bundle-site`,
`generating-ui-bundle-custom-app`, `using-ui-bundle-salesforce-data`, `deploying-ui-bundle`). This
file supplies the FinDock contract and the route-specific wiring.

---

## Intake sub-question 1g — which Multi-Framework route?

Ask this **only after the user has explicitly chosen Salesforce Multi-Framework** in Question 1.
Present all four options:

1. **React shell + embedded Salesforce payment experience (Lightning Out 2.0).** An external React
   app (UI bundle on a Digital Experience site) owns the page; the FinDock **Flow + LWC** experience
   (Pay Button + Payment Method Selector in a Screen Flow) or a **custom LWC + managed LWC** form is
   rendered inside it through Lightning Out 2.0.
2. **React components next to the Flow + LWC / LWC + LWC components inside an Experience Cloud
   site.** The Experience Cloud (LWR) site stays the page; React is used for parts of it.
3. **Full React straight into the FinDock Payment API.** No managed components; React renders the
   whole form and calls the API through the platform SDK.
4. **Not sure — talk it through.** Run the discussion guide below and recommend a route.

Decision summary (details per route follow):

| | 1 — React shell + LO2 | 2 — React inside the EC site | 3 — Full React → API |
|---|---|---|---|
| Who owns the payment step | Salesforce (Flow/LWC, admin-maintained, managed Pay Button) | Salesforce (Flow/LWC) with React islands | You (React + Apex REST / FinDock REST) |
| Managed Pay Button / Selector | Yes, inside the iframe | Yes, on the page | No (you rebuild selector + PaymentIntent) |
| Public (guest) payers | Yes — the embed runs as the linked LWR site's Guest User (`lightning-out.md`) | Yes (standard EC guest rules) | Yes (site with guest access + FinDock guest prerequisites) |
| GA today | LO2 GA, Multi-Framework GA, FinDock components pilot | 2a (React-in-LWC) GA; 2b micro-frontends **Developer Preview**; 2c sibling sites GA | GA |
| Effort | Medium (two sites + LO2 app + allow-lists) | Low–medium (2a needs a UMD/IIFE React build) | Medium–high (full form, validation, icons, errors) |
| Best for | Rich React storytelling around an admin-owned payment step; reuse existing Flow | Adding React widgets to an existing EC donation page | Pixel-perfect React checkout, internal virtual terminal, multi-PSP dynamic forms |

---

## Intake sub-question 1h — start from the FinDock Labs example, or from scratch?

Ask this right after 1g, whatever route was picked. FinDock Labs publishes a complete, working
reference implementation of this target:

**`https://github.com/FinDockLabs/findock-multi-framework-react`** — a public (guest) donation page
for a fictional charity ("Tidewell Foundation"): React UI bundle `DonatePortal` (Vite, TypeScript,
Tailwind, shadcn/ui, three-step form, PSP return pages) on an Experience site at `/donate`, taking
one-time **and** monthly gifts through an Apex REST wrapper (`/services/apexrest/donate/v1/*`) that
calls the FinDock managed classes in-transaction. It is Route 3 end to end and doubles as the React
shell for Routes 1 and 2c.

Offer two choices:

1. **Use the example (recommended for Route 3, and as the shell for Routes 1 / 2c).** Clone or fork
   it, then:
   - Read its `README.md` (architecture, deploy order, porting table) and `AGENTS.md` (non-negotiable
     design decisions, org-verified FinDock facts, rebuild order, pitfalls) **before** changing anything.
   - Port to the target org by editing the `Donation_Page_Setting.Default` custom metadata record —
     currency, processor, payer record type (`PersonAccount` for Nonprofit Cloud + FinDock for
     Fundraising; blank = Contact for NPSP and standard orgs),
     offered methods per frequency, presets with impact hints, amount bounds, default campaign,
     origin, support email, allowed return hosts. Nothing org-specific lives in code.
   - Replace the fictional copy, hero illustration, charity registration number, policy links
     (`appLayout.tsx`, `Hero.tsx`, `ThankYou.tsx`).
   - For Route 1: keep the shell (site metadata, routes, `appUrl`, return pages, a11y CSS), drop the
     Apex wrapper and the payment step, and mount the Lightning Out 2.0 embed where the form was.
   - For Route 2c: keep the shell for the storytelling/amount/details steps and hand off to the LWR
     payment page instead of calling `/intent`.
2. **Start from scratch.** Scaffold with `sf template generate ui-bundle … --template reactbasic` (or
   `reactexternalapp`) and follow the route sections below. Still read the example's `AGENTS.md`
   "FinDock facts verified against the org" and "Pitfalls" sections — they save hours.

Either way, the facts below that were verified in the example's org apply to every route.

### Learnings from the example that apply to every on-platform build

- **The FinDock managed entry points are no-argument static methods that read and write
  `RestContext`.** `cpm.API_PaymentIntent_V2.postPaymentIntent()` and
  `cpm.API_PaymentMethod_V2.getPaymentMethods()` — `postPaymentIntent(String)` does **not compile**.
  Swap in a fresh `RestRequest`/`RestResponse`, call the method, read `RestContext.response`, and
  restore the originals in `finally` (see the gateway class in Route 3). The same pattern is used in
  the FinDockLabs `findock-experience-cloud-examples` repo and applies to `@AuraEnabled` controllers
  and invocable actions too (`on-platform-apex-lwc-flow.md`).
- **The guest user needs two assignments** for a public React site: the repo's least-privilege
  `Donation_Public_Access` permission set (execute access on the wrapper classes, **no object CRUD**)
  and the **FinDock Payer permission set group** (bundles FinDock Core Experience Cloud Run +
  FinDock Experience Cloud / `proh__FinDock_Experience_Cloud`). The example assigned the single
  `proh__FinDock_Experience_Cloud` set, which works, but the group is FinDock's current framework. All Payment /
  Installment / Gift Commitment writes happen asynchronously under the ProcessingHub integration
  user. No processor-specific permission set was needed for Stripe iDEAL / card / SEPA.
- **Return URLs must preserve the site path prefix.** Build them client-side from the platform-injected
  `SFDC_ENV.basePath` (`appUrl('/thank-you')`), never from `window.location.origin` alone or
  `import.meta.env.BASE_URL`, or the PSP returns the donor to the bare origin and off-site. Validate
  them server-side against the request `Host`, the org domain, `*.my.site.com`, `*.force.com`,
  `*.salesforce.com` and an allow-list so the endpoint is not an open redirect.
- **Payment methods are dynamic and filtered server-side**: read the live `/PaymentMethods`
  response, keep only the configured methods in configured order, resolve the processor
  (configured override → `IsDefault` → first) and pass logo (`Processors[].image.svg`),
  `SupportsRecurring`, `InitialPaymentOnRecurring` and parameter definitions (enum options with
  label + image) to the page. The org used had **no default processor**, so send `Processor`
  explicitly.
- **Donor-visible parameters** are those marked `Required` or carrying an `Enum`; optional free-text
  parameters (`locale`, `itemName`, `description`) are merchant concerns — hide them and let Apex fill
  `itemName` / `description` with "Gift to <org>" so the PSP page is not blank.
- **Recurring**: send `Recurring { Amount, Frequency: 'Monthly', StartDate, CurrencyISOCode }`. If the
  processor reports `InitialPaymentOnRecurring == 'required'` (older responses:
  `RecurringRequiresInitialPayment == true`), also send `OneTime { Amount }` and start the schedule at
  today + 1 month so the donor is not charged twice; tell the donor on the payment step.
- **Payer shape follows the nonprofit stack, so ask.** The example org runs **Nonprofit Cloud (NPC,
  Agentforce for Nonprofits) with FinDock for Fundraising**, where people are **Person Accounts**:
  `Payer.Account.RecordTypeName = PersonAccount` with `PersonEmail` (not `Email`), and recurring maps
  to Gift Commitment + Schedule. On **NPSP** or a standard org the payer is a plain `Contact` /
  `Account` (recurring → NPSP Recurring Donation / FinDock Recurring Payment). The example switches
  on the `Payer_Record_Type__c` setting: filled = Person Account block, blank = Contact block.
  `Frequency` values are Daily / Weekly / Monthly / Yearly.
- **Error routing** is done in Apex: FinDock codes 201–205 → `recoverable` with a field mapping
  (201 → account number, 202/203 → IBAN, 204 → BIC); everything else → `failed` with one generic
  message and the raw body only in `System.debug`. The page receives a normalised
  `redirect | success | recoverable | invalid | failed` status and always has a route.
- **Local dev**: `npm run dev` serves mock config by default (`mockDonationApi.ts`);
  `VITE_DONATION_API=org npm run dev` opts into the UI-bundle dev proxy (returned 401 in the lab org).
  Vitest needs the `@` alias in `vitest.config.ts`; Playwright must click `label.choice`, not the
  visually hidden radio.
- **Deploy order**: backend (CMT + Apex + tests + permission set + CSP) **together** with
  `-l RunSpecifiedTests`, then the built bundle, then the site metadata, then assign the
  permission set + FinDock Payer group to the guest user (`Site.GuestUserId`). Developer/production-type orgs roll back
  the whole deploy on any test failure; partial redeploys of `classes/` fail with "Invalid type"
  until the CMT exists.
- **Verification that counts as done**: anonymous `GET <site>/sf/api/services/apexrest/…/config` →
  200 with the offered methods; a policy-violating POST → 400 `status: invalid`; the smoke test
  navigates to a `redirect.*.findock.com/…/checkout` URL (this creates a real test PaymentIntent —
  say so).

---

## Route 1 — React shell (external UI bundle) embedding the Salesforce experience via Lightning Out 2.0

### What you get

```
https://ORG.my.site.com/donate            ← React external app (UIBundle, target Experience)
 ├─ nav / hero / impact copy / footer     ← React
 └─ <c-donation-flow-embed>               ← Lightning Out 2.0 web component (iframe, closed shadow DOM)
      └─ Screen Flow (cpm:paymentMethodSelector + cpm:payButton)  ← runs in Salesforce context,
         backed by an LWR Experience Cloud site (https://ORG.my.site.com/lo)
```

The LWC/Flow exposed through LO2 is exactly what `lightning-out.md` describes (a thin LWC wrapping
`<lightning-flow>`, or `c-payment-form` / your custom LWC). The **only new part is the host page**:
it is a React route inside a UI bundle instead of WordPress/Next.js.

### Prerequisites (Salesforce Help: *Prepare to Build a Lightning Out 2.0 App*)

- Host page over **HTTPS**, iframes allowed, **third-party cookies** allowed in the browser.
- Setup → **Session Settings → Trusted Domains for Inline Frames**: add the React site's domain
  (`ORG.my.site.com`, or the custom domain) with **IFrame Type = Lightning Out**. During local dev
  also add `http://localhost:5173` (remove before production).
- Setup → **My Domain → Routing and Policies**: *Require first-party use of Salesforce cookies* **off**.
- Setup → **CORS**: add the React site origin and *Enable CORS for OAuth endpoints* (required when the
  page calls the LO2 UI Bridge endpoint client-side; see Auth below).
- Setup → **Lightning Out 2.0 App Manager**: app **Enabled**, React site origin under **Host Page
  Domain Names**, and **every** component under **App Components** — the wrapper plus its children
  (`cpm-pay-button`, `cpm-payment-method-selector`, the templates' `c-amount-and-frequency`,
  `c-currency-picker`, `c-payment-selector`, `c-experience-progress-stages`, …). Undeclared children
  render blank.
- LO2 embeds **custom LWCs only** (no Aura, no bare base components, no `lightning/navigation`).
- The Experience Cloud side (LWR site, guest permissions, ProcessingHub) is unchanged from
  `lightning-out.md` / `experience-cloud.md`; emit the **public-site prerequisite warning** there.

> **Same-domain advantage.** A React external app and the LO2-backing LWR site are both Experience
> Cloud sites of the same org, so by default they share the host `ORG.my.site.com` and differ only
> by path prefix (`/donate` vs `/lo`). The iframe is then **first-party**, which removes most of the
> Safari / third-party-cookie fragility LO2 has on a foreign domain. Still register the domain in the
> allow-lists above. If either site uses a custom domain, you are back to cross-site cookies.

### Authentication — guest vs logged-in users

- **Public donors (guest, the common case).** No OAuth, no `frontdoor-url`. The LO2 app is linked to
  the LWR Experience Cloud site (*Linked Community Site*), the host page sets `org-url` (the LWR site
  origin) and `site-prefix` (its path prefix, `""` if none), and the embed runs as that site's Guest
  User — full setup in `lightning-out.md`. The Guest User needs the **FinDock Payer** permission set
  group, run access to the Flow (or the FinDockLabs guest permission set), and the ProcessingHub
  prerequisites from `experience-cloud.md`. Salesforce's *Lightning Out 2.0 Limitations* dev-guide page
  still says guest access "isn't supported yet"; that page lags the linked-site capability — do not
  let it derail the build, but do smoke-test with an anonymous browser like any public page.
- **Logged-in Salesforce users (portal members, staff).** Follow the Salesforce Help flow: an
  **External Client App** (OAuth web server with PKCE or JWT bearer; `web`/`full` scope; client
  credentials not allowed) → POST `access_token` + `lightning_out_app_id` to
  `https://ORG.my.salesforce.com/services/oauth2/lightningoutsingleaccess` → set the returned
  `frontdoor_uri` as `frontdoor-url` on `<lightning-out-application>`. The platform SDK gives the React
  app a data session, **not** an OAuth token, so run the ECA flow from React or from a small Apex REST
  endpoint that performs the JWT bearer exchange server-side and returns the frontdoor URL.

### React implementation

**1. Load the LO2 runtime once, from the host page.** It is served by the org, not by npm:

```html
<!-- index.html of the UI bundle — FinDock: LO2 runtime; keep async. -->
<script type="text/javascript" async
        src="https://ORG.my.salesforce.com/lightning/lightning.out.latest/index.iife.prod.js"></script>
```

> ⚠️ **CSP check (do this first in a sandbox).** UI bundles ship a Salesforce-managed Content
> Security Policy, and `CspTrustedSite` has no *script-src* flag. Salesforce's own React features
> (the Agentforce Conversation Client) load Lightning-Out-type iframes from UI bundles, so this is the
> sanctioned direction — but confirm the runtime script and the `my.salesforce.com` / `my.site.com`
> iframes load without CSP violations in **your** org. If the script is blocked, fall back to a plain
> `<iframe src="https://ORG.my.site.com/lo/donate-embed">` of the LWR page that hosts the Flow
> (needs a `CspTrustedSite` with `isApplicableToFrameSrc` for the site origin plus the site's
> clickjack allow-list) — same visual result, minus LO2's event bridge.

Add `CspTrustedSite` entries for the org origin and the LWR site origin with `connect-src` and
`frame-src` set to true (see `sf-skills/generating-ui-bundle-metadata`).

**2. Declare the custom elements for TSX** (`src/types/lightning-out.d.ts`):

```ts
declare namespace React.JSX {
  interface IntrinsicElements {
    'lightning-out-application': React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & {
      'app-id': string; components: string; 'frontdoor-url'?: string;
      'org-url'?: string; 'site-prefix'?: string;
    };
    'c-donation-flow-embed': React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & {
      'success-url'?: string; 'failure-url'?: string;
    };
  }
}
```

**3. Host component** (`src/components/SalesforcePaymentEmbed.tsx`). React 19 forwards unknown
attributes to custom elements, so the LO2 attributes can be set declaratively; events still need a
ref because LO2 events cross the iframe via `postMessage` and only `EventTarget` listeners see them.

```tsx
import { useEffect, useRef, useState } from 'react';
import { appUrl } from '../lib/appUrl';   // see Route 3 for the helper

type Props = {
  appId: string;                 // 18-char Lightning Out 2.0 app id
  siteOrigin: string;            // FinDock: LWR site origin, e.g. https://ORG.my.site.com
  sitePrefix: string;            // FinDock: LWR site path prefix, '' if none (guest flow — default)
  frontdoorUrl?: string;         // logged-in users only: set after the UI Bridge call
  onPaymentResult?: (detail: { status: 'success' | 'failure'; paymentIntentId?: string }) => void;
};

export function SalesforcePaymentEmbed({ appId, siteOrigin, sitePrefix, frontdoorUrl, onPaymentResult }: Props) {
  const appRef = useRef<HTMLElement>(null);
  const cmpRef = useRef<HTMLElement>(null);
  const [state, setState] = useState<'loading' | 'ready' | 'error'>('loading');
  const [message, setMessage] = useState<string>();

  useEffect(() => {
    const app = appRef.current, cmp = cmpRef.current;
    if (!app || !cmp) return;
    // FinDock: LO2 lifecycle events — never leave the payer on a blank box.
    const onReady = () => setState('ready');
    const onError = (e: Event) => { setState('error'); setMessage((e as CustomEvent).detail?.message); };
    app.addEventListener('lo.application.ready', onReady);
    app.addEventListener('lo.application.error', onError);
    cmp.addEventListener('lo.component.error', onError);
    // FinDock: custom event dispatched by the wrapper LWC (bubbles + composed) — optional analytics hook.
    const onResult = (e: Event) => onPaymentResult?.((e as CustomEvent).detail);
    cmp.addEventListener('paymentresult', onResult);
    return () => {
      app.removeEventListener('lo.application.ready', onReady);
      app.removeEventListener('lo.application.error', onError);
      cmp.removeEventListener('lo.component.error', onError);
      cmp.removeEventListener('paymentresult', onResult);
    };
  }, [onPaymentResult]);

  // FinDock: preserve the Experience site path prefix (SFDC_ENV.basePath is injected by the platform).
  const successUrl = appUrl('/thank-you');
  const failureUrl = appUrl('/payment-failed');

  return (
    <section aria-busy={state === 'loading'} aria-live="polite">
      {/* FinDock: one application element per page. Guests: org-url + site-prefix (even "").
          Logged-in users: additionally set frontdoor-url at run time. */}
      <lightning-out-application
        ref={appRef}
        app-id={appId}
        components="c-donation-flow-embed"
        org-url={siteOrigin}
        site-prefix={sitePrefix}
        frontdoor-url={frontdoorUrl}
      />
      {/* FinDock: the exposed LWC. Public @api props are passed as kebab-case attributes. */}
      <c-donation-flow-embed ref={cmpRef} success-url={successUrl} failure-url={failureUrl} />
      {state === 'loading' && <p>Loading secure payment form…</p>}
      {state === 'error' && <p role="alert">The payment form could not be loaded. Please try again later.</p>}
      {message && import.meta.env.DEV && <pre>{message}</pre>}
    </section>
  );
}
```

The React shell itself can be the FinDock Labs example (`findock-multi-framework-react`) with the
Apex wrapper and payment step removed — see intake 1h.

**4. Wrapper LWC** — as in `lightning-out.md`, plus expose `successUrl` / `failureUrl` as `@api`
properties, pass them into the Flow as input variables (`<lightning-flow flow-api-name="Donation_Flow"
flow-input-variables={inputs}>`) so the Pay Button's redirect targets land on the **React site's
routes**, and dispatch `new CustomEvent('paymentresult', { bubbles: true, composed: true, detail })`
if you want the React shell to react to Flow status changes. The Pay Button redirects the **top-level
page** to the PSP, so `/thank-you` and `/payment-failed` must exist as React routes (SPA fallback in
`ui-bundle.json`: `"routing": { "fallback": "index.html" }`).

**5. Theme.** The embed adopts the **LWR site's** theme. From the React page you can only pass CSS
custom properties / SLDS styling hooks via the element's `style` attribute
(`style="--slds-c-button-brand-color-background: #0b6b3a"`); plain CSS properties are not forwarded.

### Checklist

1. Build and test the Flow/LWC as a normal guest (or authenticated) page on the LWR site first.
2. Complete the LO2 checklist in `lightning-out.md` (site, allow-lists, LO2 app + components).
3. Scaffold the React external app (`reactexternalapp` or `reactbasic` + `generating-ui-bundle-site`),
   `enableGuestAccess` as needed, SPA fallback, CSP entries.
4. Add the LO2 runtime script, the `.d.ts`, the embed component, and the return routes.
5. Verify in a sandbox: script loads under CSP, iframe renders for an anonymous browser, and the PSP
   redirect returns to the React routes.

---

## Route 2 — React components with the Flow + LWC / LWC + LWC components inside an Experience Cloud site

Two facts shape this route: a React (UI bundle) site **cannot be edited in Experience Builder**, and
React components **cannot be placed on an Experience Builder page** through the builder today
(*"Integration of those components in Lightning Experience and other LWC-based environments requires
Micro-Frontend support"* — Multi-Framework guide; micro-frontends are a **Developer Preview**). So
"React inside the Experience Cloud site" is one of three concrete shapes:

### 2a — React inside a custom LWC (GA, same Experience Builder page as the FinDock components) — recommended

Bundle the React widget as a **static resource** and mount it from an LWC that sits on the same
Experience Builder page as the Flow or `c-payment-form`. This is Salesforce's documented third-party
library pattern (*Use Third-Party JavaScript Libraries*: static resource + `lightning/platformResourceLoader`
+ `lwc:dom="manual"`). Under Lightning Web Security most libraries, React included, run unchanged.

```bash
# vite.config.ts — build the widget as a single self-registering IIFE (no ESM import in LWC)
# build: { lib: { entry: 'src/widget.tsx', name: 'FinDockAmountWidget', formats: ['iife'], fileName: () => 'amountWidget.js' } }
npm run build && cp dist/amountWidget.js ../force-app/main/default/staticresources/amountWidget.js
```

```tsx
// src/widget.tsx — exposes a mount() that the LWC calls; emits the same 3 values the FinDock
// Amount & Frequency contract uses (amountOneTime, amountRecurring, frequency).
import { createRoot } from 'react-dom/client';
import { AmountPicker } from './AmountPicker';
declare global { interface Window { FinDockAmountWidget: { mount: typeof mount } } }
function mount(el: HTMLElement, opts: { currency: string; onChange: (d: AmountDetail) => void }) {
  const root = createRoot(el);
  root.render(<AmountPicker currency={opts.currency} onChange={opts.onChange} />);
  return () => root.unmount();
}
window.FinDockAmountWidget = { mount };
```

```html
<!-- reactAmountPicker.html -->
<template>
  <div class="react-root" lwc:dom="manual"></div>
</template>
```

```javascript
// reactAmountPicker.js
import { LightningElement, api } from 'lwc';
import { loadScript } from 'lightning/platformResourceLoader';
import AMOUNT_WIDGET from '@salesforce/resourceUrl/amountWidget';

export default class ReactAmountPicker extends LightningElement {
  @api currency = 'EUR';
  _unmount; _loaded = false;

  renderedCallback() {
    if (this._loaded) return; this._loaded = true;
    loadScript(this, AMOUNT_WIDGET).then(() => {
      const el = this.template.querySelector('.react-root');
      // FinDock: React → LWC bridge. Re-dispatch as the FinDock contract event so the host form
      // (c-payment-form / customPayment) can feed it into the PaymentIntent for <cpm-pay-button>.
      this._unmount = window.FinDockAmountWidget.mount(el, {
        currency: this.currency,
        onChange: (detail) => this.dispatchEvent(new CustomEvent('amountfrequencychanged',
          { detail, bubbles: true, composed: true })),
      });
    });
  }
  disconnectedCallback() { this._unmount?.(); }
}
```

Wire it exactly like the unmanaged `c-amount-and-frequency` in `experience-cloud.md`: the parent LWC
listens to `amountfrequencychanged`, rebuilds the PaymentIntent, and hands it to `<cpm-pay-button>`.
In a **Flow**, wrap the same LWC as a Flow screen component (`lightning__FlowScreen` target, outputs
via `FlowAttributeChangeEvent`) and map its outputs to the Pay Button like the template does.

Rules: React must not touch DOM outside its `lwc:dom="manual"` root; no `document.querySelector`;
styles inside the widget are scoped by LWC — ship them inside the IIFE (CSS-in-JS or injected
`<style>` into the root). Expose the React widget's inputs as `@api` design properties so admins
configure it in Experience Builder. Everything in `accessibility.md` / `page-quality.md` still applies
to the React markup.

### 2b — Micro-frontend embedding (Developer Preview — prototypes only)

Salesforce's `<lightning-ui-embedding>` base component (recipes repo, `microfrontend-recipes`) lets an
LWC host embed a React **guest** served from a UI bundle route (`/embedding/<recipe>`) in a sandboxed
iframe, with props, events, theme tokens and auto-resize exchanged over
`@salesforce/platform-sdk` (`import '@salesforce/platform-sdk/ui-embedding'`, then `getViewSDK()` →
`getUiState()`, `dispatchEvent()`). The host would forward the guest's `amountfrequencychanged`
into the PaymentIntent as in 2a. Today the sample hosts target `lightning__AppPage/RecordPage/HomePage`
only, the feature is behind the Dev Channel, and Salesforce's roadmap lists micro-frontends
(*"embed externally hosted React components in Lightning alongside Lightning web components and pass
events between them"*) as **not yet GA**. Do not ship payments on it; mention it as the future
replacement for 2a.

### 2c — Sibling sites on one domain (GA, no embedding)

Keep the payment step on the **LWR Experience Cloud site** (Flow or `c-payment-form`, admin-editable
in Experience Builder) and put everything else in a **React external app** on the same
`ORG.my.site.com` host: `/donate` (React: campaign story, amount, frequency, personal details) →
navigates to `/pay/checkout?amount=25&frequency=recurring&first=…` (LWR page whose Flow reads the URL
parameters as input variables) → Pay Button → PSP → SuccessURL/FailureURL back on the React site.
No CSP or LO2 work; the trade-off is a visible page hop and a theme seam between the two sites.

### Choosing within Route 2

- Must be **one page** with the FinDock components → **2a**.
- Team is fine with a hop and wants zero React-on-platform risk → **2c**.
- Exploring what GA micro-frontends will look like → **2b** in a scratch org only.

---

## Route 3 — Full React into the FinDock Payment API

React renders the whole form (amount → personal details → method selector + method parameters →
pay) and calls FinDock through the platform SDK. No proxy, no token, no CORS: the SDK adds the
session. **The reference implementation is `FinDockLabs/findock-multi-framework-react`** (intake 1h);
the shapes below are lifted from it.

### Architecture (as verified in the example)

```
React UI bundle (guest session, sdk.fetch)        Apex REST wrapper                     FinDock managed classes
GET  /services/apexrest/donate/v1/config  ─────▶  DonationPaymentResource  ──▶ Service ─▶ cpm.API_PaymentMethod_V2.getPaymentMethods()
POST /services/apexrest/donate/v1/intent  ─────▶  (policy, PaymentIntent) ──▶ Gateway ─▶ cpm.API_PaymentIntent_V2.postPaymentIntent()
◀── { status, redirectUrl, paymentIntentId, errors[] }                          (RestContext swap, in-transaction)
window.location = redirectUrl → PSP hosted checkout → /thank-you | /failed on the React site
```

**The browser never calls FinDock and is never trusted.** React UI bundles cannot call `@AuraEnabled`
Apex, so the wrapper is an `@RestResource`; all policy (amount bounds, frequency, offered methods,
declared parameters only, payer shape, return-URL origin) lives in Apex, and everything org-specific
lives in a custom metadata record. Calling FinDock's own `/services/apexrest/cpm/v2/…` resource
directly from `sdk.fetch` is *possible* in principle (same classes, different transport) but was not
what the example verified, gives you no server-side policy, and exposes the raw FinDock payload/error
contract to the browser — prefer the wrapper.

### Apex — gateway to the managed classes (copy as-is)

```apex
// FinDockRestContextGateway.cls — FinDock: the managed entry points take NO arguments; they read
// RestContext.request and write RestContext.response. Swap the context, call, capture, restore.
public with sharing class FinDockRestContextGateway implements FinDockGateway {
    private static final String PAYMENT_INTENT_URI  = '/services/apexrest/cpm/v2/PaymentIntent';
    private static final String PAYMENT_METHODS_URI = '/services/apexrest/cpm/v2/PaymentMethods';

    public FinDockGatewayResponse postPaymentIntent(String requestBody) {
        RestRequest req = new RestRequest();
        req.requestURI = URL.getOrgDomainUrl().toExternalForm() + PAYMENT_INTENT_URI;
        req.httpMethod = 'POST';
        req.addHeader('Content-Type', 'application/json');
        req.requestBody = Blob.valueOf(requestBody);
        return invoke(req, true);
    }

    public FinDockGatewayResponse getPaymentMethods() {
        RestRequest req = new RestRequest();
        req.requestURI = URL.getOrgDomainUrl().toExternalForm() + PAYMENT_METHODS_URI;
        req.httpMethod = 'GET';
        return invoke(req, false);
    }

    private FinDockGatewayResponse invoke(RestRequest req, Boolean isPost) {
        RestRequest originalRequest = RestContext.request;
        RestResponse originalResponse = RestContext.response;
        RestResponse res = new RestResponse();
        try {
            RestContext.request = req;
            RestContext.response = res;
            if (isPost) {
                cpm.API_PaymentIntent_V2.postPaymentIntent();      // FinDock: same as POST /PaymentIntent
            } else {
                cpm.API_PaymentMethod_V2.getPaymentMethods();      // FinDock: same as GET /PaymentMethods
            }
        } finally {
            RestContext.request = originalRequest;                 // we are inside our own REST request
            RestContext.response = originalResponse;
        }
        Integer status = res.statusCode == null ? 200 : res.statusCode;
        String body = res.responseBody == null ? '' : res.responseBody.toString();
        return new FinDockGatewayResponse(status, body);           // { statusCode, body, isSuccess() }
    }
}
```

`FinDockGateway` is a two-method interface so tests swap in a stub (`FinDockGatewayStub`) and never
contact a PSP. Cover the real gateway with a test that calls the managed methods with an empty body
and asserts the context is restored.

### Apex — REST wrapper + service (shape)

```apex
@RestResource(urlMapping='/donate/v1/*')
global with sharing class DonationPaymentResource {
    @HttpGet  global static void doGet()  { /* …/config  → DonationPaymentService.getConfig() */ }
    @HttpPost global static void doPost() { /* …/intent  → DonationPaymentService.createIntent(body, Host header) */ }
    // respond(): JSON body, Cache-Control: no-store; 400 for status=invalid, 502 for status=failed, else 200
}
```

`DonationPaymentService` does, in order: load `Donation_Page_Setting__mdt` → validate the request
(frequency, amount bounds + 2 decimals, names, email, method, **return URLs on this site**, campaign
id) → load live methods via the gateway and filter by the configured allow-list → validate parameters
against what FinDock declared (required, min/max length, enum membership, Integer) → build the
PaymentIntent (Payer as Person Account for NPC or Contact for NPSP/standard, `OneTime` / `Recurring` (+ initial `OneTime` when
`InitialPaymentOnRecurring == 'required'`, `StartDate` today + 1 month), `PaymentMethod { Name,
Processor, Parameters }`, `Settings.SourceConnector`, `CampaignId`, `Origin`) → call
`gateway.postPaymentIntent(JSON.serialize(intent))` → normalise to
`redirect | success | recoverable | invalid | failed` (201–205 recoverable, mapped to fields).

### React — data layer (GA SDK)

```ts
// src/api/donation/donationService.ts
import { createDataSDK } from '@salesforce/platform-sdk';
const BASE = '/services/apexrest/donate/v1';

async function platformFetch(path: string, init?: RequestInit) {
  const sdk = await createDataSDK();
  if (!sdk.fetch) throw new Error('Platform fetch is not available in this surface.');
  return sdk.fetch(`${BASE}${path}`, init);          // FinDock: session + CSRF added by the SDK, no token
}
const useMock = () => import.meta.env.DEV && import.meta.env.VITE_DONATION_API !== 'org';

export async function fetchDonationConfig(): Promise<DonationConfig> {
  if (useMock()) return mockConfig();
  const res = await platformFetch('/config');
  if (!res.ok) throw new Error(`Could not load donation settings (HTTP ${res.status}).`);
  return res.json();
}

export async function createDonationIntent(request: IntentRequest): Promise<IntentResponse> {
  if (useMock()) return mockCreateIntent(request);
  try {
    const res = await platformFetch('/intent', { method: 'POST',
      headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(request) });
    return normaliseIntentResponse(await res.json().catch(() => null), res.status);   // never throws for business outcomes
  } catch (err) {
    console.error('Donation intent request failed', err);
    return { status: 'failed', errors: [{ code: 'network', message: 'The donation could not be started.' }] };
  }
}
```

```ts
// src/lib/appUrl.ts — FinDock: SuccessURL / FailureURL must keep the Experience site prefix
export function getBasename(): string | undefined {
  const raw = (globalThis as { SFDC_ENV?: { basePath?: string } }).SFDC_ENV?.basePath;
  if (typeof raw !== 'string' || raw === '') return undefined;
  const trimmed = raw.replace(/\/+$/, '');
  return trimmed === '' ? '/' : trimmed;
}
export function appUrl(routePath: string): string {
  const base = getBasename() ?? '';
  const path = routePath.startsWith('/') ? routePath : `/${routePath}`;
  return `${window.location.origin}${base === '/' ? '' : base}${path}`;
}
```

Submit flow in the page: build `IntentRequest { frequency, amount, paymentMethod, parameters,
firstName, lastName, email, campaignId (from `?campaign=`), successUrl: appUrl('/thank-you'),
failureUrl: appUrl('/failed') }` → `switch (result.status)`: `redirect` →
`window.location.assign(redirectUrl)`; `success` → navigate to thank-you; `recoverable` / `invalid`
→ map `errors[].field` onto the form and stay on the step; `failed` → one generic alert with
"Nothing has been charged" and the support email.

### React — UI rules the example encodes

- Selector rows: visually-hidden-but-focusable radio (`.choice-input`) → logo from the config's
  `imageUrl` (= `Processors[].image.svg`) with `onError` hide → label. Enum parameters render the
  same way from `options[].label` + `imageUrl`; other parameters become inputs with FinDock's
  min/max length, `inputMode="numeric"` for `Integer`, uppercase for IBAN.
- Payment step shows a summary (gift, receipt email) with Edit links instead of re-asking (WCAG 3.3.7),
  the "first payment collected today" note when an initial charge is required, `aria-busy` on the
  submit button with the exact amount in its label, and a "you will be taken to … card details
  never touch this site" trust line.
- `role="status"` step announcements, `aria-invalid` + `aria-describedby` on every error,
  reduced-motion support, 44px targets, 16px inputs, one column at 390px, AA contrast tokens in
  `global.css`. Fonts are self-hosted (`@fontsource-variable/*`) so no font CSP entry is needed.
- CSP Trusted Sites for `https://external.findock.com` (method logos) and `https://images.findock.com`
  (issuer / brand images) with `img-src` + `connect-src`.

### Metadata checklist (Experience target)

`DonatePortal.uibundle-meta.xml` with `<target>Experience</target>`; `ui-bundle.json` with
`routing.fallback: index.html` and `trailingSlash: never`; `digitalExperiences/site/<Site>1/…/content.json`
with `appContainer: true`, `appSpace: "c__DonatePortal"`, `authenticationType:
AUTHENTICATED_WITH_PUBLIC_ACCESS_ENABLED`; Network with `enableSiteAsContainer: true`; CustomSite;
DigitalExperienceConfig; the CMT type + `Default` record; the permission set; the two CSP entries.
Generate the site files with `sf-skills/generating-ui-bundle-site` when starting from scratch.

### Internal variant (virtual terminal, invoice desk)

Same code, `target` = `CustomApplication`, plus a `CustomApplication` and a permission set for the
staff who use it. The app runs on `https://<org>--c.<instance>.my.salesforce.app/app/c__<Name>/…`, so
`appUrl()` still builds the return URLs from `SFDC_ENV.basePath`. No guest prerequisites; users need
the FinDock permission set (group) that grants the API classes plus the wrapper classes.

---

## Route 4 — "Chat about it": discussion guide

Ask, then recommend one route and say why:

1. **Who pays?** Anonymous public donors → any of 1, 2, 3 (all run as the site Guest User; same
   ProcessingHub prerequisites). Logged-in customers/partners → any route. Staff → Route 3 internal.
2. **Who maintains the payment step?** Admins in Flow Builder → Routes 1 or 2 (managed Pay Button).
   Developers → Route 3.
3. **Does a Flow / LWC payment experience already exist?** Yes → Route 1 or 2c reuse it as-is.
4. **How much React is needed?** A widget or two on an existing donation page → 2a. A whole branded
   SPA around an admin-owned pay step → 1 (or 2c for lowest risk). Everything → 3.
5. **PSP / method mix?** Many methods with parameters and enums → Route 3 with a dynamic selector, or
   the managed Payment Method Selector via Routes 1/2.
6. **Risk appetite?** GA everywhere: 1, 2a, 2c, 3 (FinDock managed components remain pilot). Preview: 2b.
7. **Budget for two sites?** Route 1 needs the React site **and** an LWR site plus LO2 admin work.

Default recommendations: existing Flow + React marketing shell → **1** (or **2c** if the team wants
no LO2 admin work); new build with full design control → **3**; existing EC donation page that needs
a React component → **2a**.

---

## Local development, build, deploy

```bash
sf template generate ui-bundle -n findockPayment --template reactbasic   # or: sf template generate project (reactexternalapp)
cd force-app/main/default/uiBundles/findockPayment && npm install
npm run dev                    # http://localhost:5173 — @salesforce/vite-plugin-ui-bundle proxies data calls to your org
npm run build                  # tsc -b && vite build → dist/
sf project deploy start        # UIBundle + CustomApplication or site metadata + Apex + CSP
```

Deploy order matters (see `sf-skills/deploying-ui-bundle` and the example's `AGENTS.md`): backend
(CMT + Apex + tests + permission set + CSP, together, `-l RunSpecifiedTests`) → built bundle → site
metadata → assign `Donation_Public_Access` + the **FinDock Payer** permission set group to the site Guest User
(`Site.GuestUserId`) → anonymous smoke test (config 200, invalid POST 400, redirect to the PSP).

---

## Key differences vs the other React paths

| | Anywhere (standalone React) | Multi-Framework Route 3 | Multi-Framework Route 1 |
|---|---|---|---|
| Auth to FinDock | Server proxy + OAuth token | Platform SDK session (`sdk.fetch`) | None from React — the managed Pay Button pays inside the iframe |
| Hosting | Any web host | Salesforce (UIBundle) | Salesforce (UIBundle + LWR site) |
| CORS / proxy | Required | Not needed | Not needed for payment; LO2 allow-lists instead |
| Production | Yes | Yes (GA, Hyperforce) | Yes (guests via linked LWR site) |
| SuccessURL target | Your domain | React route on the site / app domain | React route on the React site |

## Resources

- Multi-Framework guide: https://developer.salesforce.com/docs/platform/multiframework/guide/reactdev-overview.html
- GA announcement (July 2026): https://developer.salesforce.com/blogs/2026/07/build-with-react-on-salesforce-multi-framework-is-now-ga
- **FinDock Labs example (Route 3, public donation page): https://github.com/FinDockLabs/findock-multi-framework-react**
- Recipes (React, Apex REST, micro-frontends): https://github.com/trailheadapps/multiframework-recipes
- Lightning Out 2.0 (LWC guide): https://developer.salesforce.com/docs/platform/lwc/guide/lightning-out-intro.html
- Lightning Out 2.0 (Help: prepare / auth / build): https://help.salesforce.com/s/articleView?id=platform.lightning_out_intro.htm&type=5
- Third-party JS in LWC (React-in-LWC): https://developer.salesforce.com/docs/platform/lwc/guide/js-third-party-library.html
- FinDock: Payment Experiences, Pay Button in LWC, Integrating with Experience Cloud — via the docs MCP
