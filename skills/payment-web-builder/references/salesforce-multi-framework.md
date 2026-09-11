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

  const successUrl = `${window.location.origin}${import.meta.env.BASE_URL}thank-you`;
  const failureUrl = `${window.location.origin}${import.meta.env.BASE_URL}payment-failed`;

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

React renders the whole form (personal details → method selector → method parameters → pay) and
calls FinDock through the platform SDK. No proxy, no token, no CORS: the SDK adds the session.

### How to call FinDock from a UI bundle

React UI bundles **cannot call `@AuraEnabled` Apex**. Two supported shapes, both `sdk.fetch` to
`/services/apexrest/…`:

| | 3a — FinDock's Apex REST resource directly | 3b — Your own `@RestResource` wrapper |
|---|---|---|
| Endpoint | `GET /services/apexrest/cpm/v2/PaymentMethods`, `POST /services/apexrest/cpm/v2/PaymentIntent` (same contract as the public REST docs) | `POST /services/apexrest/findock/payment` → Apex calls `cpm.API_PaymentIntent_V2.postPaymentIntent()` in-transaction |
| When | Default. The form is the whole integration. | You need pre/post logic (dedupe/find-or-create Contact, campaign or invoice lookup, server-side amount validation, logging) or want to hide the FinDock payload shape from the browser |
| Guest access | Guest user needs access to the `cpm.API_PaymentIntent_V2` / `cpm.API_PaymentMethod_V2` classes — assign the **FinDock Experience Cloud** permission set (part of the **FinDock Payer** group) | Same, plus access to your wrapper class |

> Guest payers require the **public-site prerequisites** from `experience-cloud.md` (ProcessingHub
> installed **and connected**, its integration user in the **FinDock Integration User** permission set
> group, FinDock Experience Cloud permission set on the site Guest User). FinDock's docs describe
> guest access for the Apex entry points; calling the Apex REST resource through a React external
> site's `/services/apexrest` path is the same class with a different transport — **verify in a
> sandbox with a guest session** before going live, and ask FinDock Support if it is refused.

Because the request goes through the site, the browser never holds credentials. The
`authentication.md` / `credentials-setup.md` material and the standalone Step 6 do **not** apply.

### Apex REST wrapper (3b)

```apex
// FinDockPaymentResource.cls — FinDock: thin REST façade over the managed Apex entry points.
@RestResource(urlMapping='/findock/payment')
global with sharing class FinDockPaymentResource {

    @HttpGet
    global static void getPaymentMethods() {
        // FinDock: same payload as GET /PaymentMethods (methods, processors, parameters, enums+images)
        RestContext.response.addHeader('Content-Type', 'application/json');
        RestContext.response.responseBody = Blob.valueOf(cpm.API_PaymentMethod_V2.getPaymentMethods());
    }

    @HttpPost
    global static void createPaymentIntent() {
        String payloadJson = RestContext.request.requestBody.toString();
        // FinDock: server-side rules go here (find-or-create Contact, amount floor, campaign mapping).
        // FinDock: in-transaction call — NOT an HTTP callout back into the org (that causes a callout loop).
        String responseJson = cpm.API_PaymentIntent_V2.postPaymentIntent(payloadJson);
        RestContext.response.addHeader('Content-Type', 'application/json');
        RestContext.response.responseBody = Blob.valueOf(responseJson);
    }
}
```

Verify the exact parameter/return types of both managed methods against the docs MCP and the
FinDockLabs example repo before finalizing (they are demonstrated there; do not invent signatures).

### React (GA SDK) — API layer

```ts
// src/api/findock.ts
import { createDataSDK } from '@salesforce/platform-sdk';

// FinDock: switch between 3a (FinDock resource) and 3b (your wrapper) here.
const METHODS_URL = '/services/apexrest/cpm/v2/PaymentMethods';   // 3b: '/services/apexrest/findock/payment'
const INTENT_URL  = '/services/apexrest/cpm/v2/PaymentIntent';    // 3b: '/services/apexrest/findock/payment'

export type Processor = { Name: string; IsDefault?: boolean; SupportsRecurring?: boolean;
  image?: { svg?: string }; Parameters?: Parameter[]; Targets?: string[] };
export type Parameter = { Name: string; Required?: boolean; Type?: string;
  Enum?: { value: string; label: string; image?: { svg?: string } }[] };
export type PaymentMethod = { Name: string; Processors: Processor[] };

export async function getPaymentMethods(): Promise<PaymentMethod[]> {
  const sdk = await createDataSDK();
  const res = await sdk.fetch?.(METHODS_URL);                    // FinDock: session + CSRF added by the SDK
  if (!res?.ok) throw new Error(`PaymentMethods failed: ${res?.status}`);
  const body = await res.json();
  return body.PaymentMethods ?? [];
}

export async function createPaymentIntent(payload: unknown) {
  const sdk = await createDataSDK();
  const res = await sdk.fetch?.(INTENT_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const body = await res?.json();                                 // FinDock: error bodies are JSON too
  return { ok: !!res?.ok, status: res?.status ?? 0, body };
}
```

### React — the form (essentials; apply every rule from the skill)

```tsx
// src/components/PaymentForm.tsx
import { useEffect, useMemo, useState } from 'react';
import { createPaymentIntent, getPaymentMethods, type PaymentMethod, type Processor } from '../api/findock';

const RECOVERABLE = new Set([201, 202, 203, 204, 205]);           // FinDock: only these are payer-fixable

export function PaymentForm({ currency = 'EUR' }: { currency?: string }) {
  const [methods, setMethods] = useState<PaymentMethod[]>([]);
  const [form, setForm] = useState({ firstName: '', lastName: '', email: '', amount: '25', method: '', params: {} as Record<string, string> });
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [status, setStatus] = useState<'idle' | 'loading' | 'submitting' | 'error'>('loading');

  useEffect(() => {
    // FinDock: canonical step 1 — discover methods at load; never hardcode the list.
    getPaymentMethods()
      .then(m => { setMethods(m); setForm(f => ({ ...f, method: m[0]?.Name ?? '' })); setStatus('idle'); })
      .catch(() => setStatus('error'));
  }, []);

  const selected = methods.find(m => m.Name === form.method);
  const processor: Processor | undefined = selected?.Processors.find(p => p.IsDefault) ?? selected?.Processors[0];
  const requiredParams = useMemo(() => processor?.Parameters?.filter(p => p.Required) ?? [], [processor]);

  function validate() {
    const e: Record<string, string> = {};
    if (!form.firstName.trim()) e.firstName = 'Enter your first name.';
    if (!form.lastName.trim())  e.lastName  = 'Enter your last name.';
    if (!/^\S+@\S+\.\S+$/.test(form.email)) e.email = 'Enter a valid email address.';
    if (!(parseFloat(form.amount) > 0)) e.amount = 'Enter an amount greater than 0.';
    if (!form.method) e.method = 'Choose a payment method.';
    for (const p of requiredParams) if (!form.params[p.Name]) e[`param.${p.Name}`] = `${p.Name} is required.`;
    setFieldErrors(e); return Object.keys(e).length === 0;
  }

  async function submit(ev: React.FormEvent) {
    ev.preventDefault();
    if (!validate()) return;
    setStatus('submitting');
    // FinDock: PaymentIntent — same shape as the REST docs. Processor/Target omitted → org default.
    const base = `${window.location.origin}${import.meta.env.BASE_URL}`;
    const payload = {
      SuccessURL: `${base}thank-you`,
      FailureURL: `${base}payment-failed`,
      Payer: { Contact: { SalesforceFields: { FirstName: form.firstName.trim(), LastName: form.lastName.trim(), Email: form.email.trim() } } },
      OneTime: { Amount: parseFloat(form.amount), CurrencyISOCode: currency },
      PaymentMethod: { Name: form.method, ...(Object.keys(form.params).length ? { Parameters: form.params } : {}) },
    };
    const { ok, body } = await createPaymentIntent(payload);
    const errors: { error_code?: number | string; error_message?: string }[] = body?.Errors ?? [];
    if (!ok || errors.length) {
      const recoverable = errors.filter(e => RECOVERABLE.has(Number(e.error_code)));
      if (recoverable.length) {                                   // FinDock: 201–205 → field-level guidance, let them retry
        setFieldErrors(f => ({ ...f, params: recoverable.map(e => e.error_message).join(' ') })); setStatus('idle'); return;
      }
      console.error('FinDock PaymentIntent failed', body);        // FinDock: everything else → log + ONE generic message
      setStatus('error'); return;
    }
    if (body.RedirectURL) { window.location.assign(body.RedirectURL); return }   // FinDock: PSP hosted page
    window.location.assign(`${base}thank-you?pi=${body.Id ?? ''}`);             // FinDock: non-redirect success
  }

  if (status === 'loading') return <p role="status">Loading payment options…</p>;
  if (status === 'error')   return <p role="alert">We couldn't start your payment. Please try again later or contact support.</p>;

  return (
    <form onSubmit={submit} noValidate>
      {/* 1. Personal details first — never below the method selector */}
      {/* …lightning-free inputs with aria-invalid / aria-describedby wired to fieldErrors… */}
      {/* 2. Method selector: radio → icon → label, icon from processor.image.svg (never method.image) */}
      <fieldset>
        <legend>Payment method</legend>
        {methods.map(m => {
          const p = m.Processors.find(x => x.IsDefault) ?? m.Processors[0];
          return (
            <label key={m.Name} className="method-row">
              <input type="radio" name="method" value={m.Name} checked={form.method === m.Name}
                     onChange={() => setForm(f => ({ ...f, method: m.Name, params: {} }))} />
              {p?.image?.svg && <img src={p.image.svg} alt="" height={24} />}
              <span>{m.Name}</span>
            </label>
          );
        })}
      </fieldset>
      {/* 3. Method-specific parameters from the response; Enum → show label + image.svg, send value */}
      {/* 4. Submit with the exact amount in the label */}
      <button type="submit" disabled={status === 'submitting'}>
        {status === 'submitting' ? 'Processing…' : `Pay ${currency} ${Number(form.amount || 0).toFixed(2)}`}
      </button>
    </form>
  );
}
```

Add `/thank-you` and `/payment-failed` routes, a `CspTrustedSite` for `https://external.findock.com`
(and `https://images.findock.com` for issuer/brand images) with `img-src` + `connect-src`, or bundle
the SVGs as static assets per the SKILL icon rules. Recurring: swap `OneTime` for `Recurring` with
`Frequency` and `StartDate` (see `recurring-payment.md`). Everything in `parameters-and-enums.md`,
`required-fields-and-errors.md`, `accessibility.md`, `page-quality.md`, `donation-page-structure.md`
applies unchanged to the React markup.

### Internal variant (virtual terminal, invoice desk)

Same code, `target` = `CustomApplication`, plus a `CustomApplication` and a permission set for the
staff who use it. The app runs on `https://<org>--c.<instance>.my.salesforce.app/app/c__<Name>/…`, so
build `SuccessURL`/`FailureURL` from `window.location` as above rather than hardcoding a domain. No
guest prerequisites; users need the FinDock permission set (group) that grants the API classes.

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

Deploy order matters (see `sf-skills/deploying-ui-bundle`): build → deploy metadata → assign
permission sets (staff **and** the site Guest User) → publish/activate the site → smoke-test a payment
with a guest session if the site is public.

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
- Recipes (React, Apex REST, micro-frontends): https://github.com/trailheadapps/multiframework-recipes
- Lightning Out 2.0 (LWC guide): https://developer.salesforce.com/docs/platform/lwc/guide/lightning-out-intro.html
- Lightning Out 2.0 (Help: prepare / auth / build): https://help.salesforce.com/s/articleView?id=platform.lightning_out_intro.htm&type=5
- Third-party JS in LWC (React-in-LWC): https://developer.salesforce.com/docs/platform/lwc/guide/js-third-party-library.html
- FinDock: Payment Experiences, Pay Button in LWC, Integrating with Experience Cloud — via the docs MCP
