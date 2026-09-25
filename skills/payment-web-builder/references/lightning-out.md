# Pattern 8 — Lightning Out 2.0 (embed the Salesforce payment experience in an existing website)

Use this when the deployment target from intake Question 1 is **Existing website via Lightning
Out 2.0**: the customer already has a website (WordPress, Next.js, Laravel, a static site, …)
and wants the FinDock payment experience that lives in Salesforce — a Screen Flow with the
managed Pay Button / Payment Method Selector, or a custom LWC such as the FinDockLabs
`c-payment-form` — rendered **inside that website**, without sending payers to an Experience
Cloud site and without rebuilding the form against the REST API.

> **How it works.** Lightning Out 2.0 (LO2) loads a small runtime script from the org onto the
> external page. A `<lightning-out-application>` element points at a Lightning Out app defined in
> Setup, which lists the LWCs the page may render. The components run in an iframe backed by an
> **LWR Experience Cloud site**, which supplies the guest-user context, permissions, and theme.
> So an Experience Cloud site is still required — it is the backend for the embed, not the
> customer-facing page.

> **Status / grounding.** LO2 is GA on the Salesforce side, but FinDock Payment Experiences (the
> managed components you embed) is still in a closed pilot — see `experience-cloud.md`. Before
> finalizing, verify component names, permission-set names, and current LO2 behaviour against the
> docs MCP (`https://docs.findock.com/mcp`) and the official Salesforce Lightning Out 2.0 docs.
> The FinDockLabs templates repo (https://github.com/FinDockLabs/payment-experiences-templates)
> provides the Flows and LWCs you expose; at time of writing it does **not** ship LO2-specific
> code, so the wrapper LWC and host-page snippet in this file are what you add.

> **Guest (unauthenticated) payers are supported.** LO2 serves anonymous visitors through the
> **linked LWR Experience Cloud site** (Lightning Out (LWR) template or `force:lightningOutLWRContainer`
> page, *Linked Community Site* on the LO2 app, `org-url` + `site-prefix` on the host page, no
> `frontdoor-url`). The embed then runs as that site's Guest User. Note: the *Lightning Out 2.0
> Limitations* page in Salesforce's LWC developer guide still says unauthenticated access "isn't
> supported yet" — that page lags the linked-site capability; follow the setup below, and use the
> ECA + `frontdoor-url` flow from the Salesforce Help articles only when you need **logged-in**
> Salesforce users instead of guests.

> **Host page is a React Multi-Framework app?** Everything in this file still applies; the
> React-specific host component, TSX typings, CSP check, and same-domain notes are in
> `salesforce-multi-framework.md` → *Route 1*.

---

## When to recommend this target

- The customer has an existing public website and wants the donation/checkout form **on their own
  pages** (their URL, their nav, their SEO), not on a `*.my.site.com` domain.
- The payment experience already exists (or will be built) in Salesforce as a Flow or LWC and
  they want to reuse it rather than maintain a second implementation against the REST API.
- They want the low-code, admin-maintained Flow route from `experience-cloud.md` but with an
  external front door.
- They can accept the LO2 runtime constraints below (iframe, third-party cookies, an LWR site to
  maintain, Salesforce look-and-feel inside the embed).

Do **not** recommend it when the customer wants pixel-perfect control over the form's markup,
needs it to work with third-party cookies blocked, or has no Salesforce admin to maintain the
Experience Cloud site and the Lightning Out app. In those cases use **Anywhere (standalone)**.

---

## Intake follow-ups (ask only after Lightning Out 2.0 is confirmed)

1. **What are you exposing?**
   - A **Screen Flow** (e.g. the FinDockLabs `Donation_Flow`, `One_Screen_Donation_Flow`, or
     `Checkout_Flow`, or the customer's own) → wrap it in a thin LWC (see below). LO2 can only
     expose LWCs, never a Flow directly.
   - The **pro-code `c-payment-form` LWC** from the `lwc-procode` template package → expose it
     directly.
   - A **custom LWC** the customer already has → expose it directly.
2. **Is there an LWR Experience Cloud site already?** Reuse it if so; otherwise create one from
   the **Lightning Out (LWR)** template (has the container page built in) or **Build Your Own
   (LWR)**.
3. **Which external origins host the page?** Collect every origin that will embed the form,
   including dev/tunnel hosts (e.g. `https://www.example.com`, `https://your-app.ngrok-free.dev`).
   Each one must be allow-listed in four places (see the checklist). An origin on the **same
   `*.my.site.com` domain as the LWR site** (e.g. another site in the same org) is same-origin
   and needs none of them; see *Same-origin hosts* under step 2.
4. **Where should the payer land after the PSP?** Success and failure pages on the **external
   website**, so the payer returns to the host site, not to the Experience Cloud site.

---

## Prerequisites (tell the user up front)

**External host / browser**
- The host page must be served over **HTTPS**.
- The host page must allow **iframes** and the browser must allow the necessary **third-party
  cookies** (Salesforce lists these as LO2 requirements).
- The host site's own **Content-Security-Policy** must allow framing and navigation to the
  Salesforce org, the Experience Cloud site, and `https://*.findock.com`.

**Salesforce / FinDock**
- A working Payment Experiences setup (Flow or LWC) — build and test it as a normal guest page on
  the Experience Cloud site **first**, then embed it. Debugging inside the LO2 iframe is harder.
- Everything in the **public-site prerequisite** block of `experience-cloud.md` still applies:
  FinDock | ProcessingHub installed **and connected**, the integration user holding the
  **FinDock Integration User** permission set group, and the **FinDock Payer** permission set
  group assigned to the site's Guest User. Emit that warning here too.
- **Cookie policy**: LO2 needs cross-domain Salesforce cookies. If **Require first-party use of
  Salesforce cookies** is enabled under **Setup → My Domain → Routing and Policies**, it must be
  disabled.

> ⚠️ **Republish habit.** Guests only get components that are in the site's **published**
> manifest, frozen at publish time. Republish the LWR site after:
> - linking or changing the Lightning Out app (including its component list)
> - **every deploy of an exposed LWC.** Until you republish, the site keeps serving the old version.
> - custom label / translation changes, and any change to the site, its theme, or its security settings
>
> A missing republish shows up as a guest **401** on
> `/<prefix>/webruntime/component/latest/…/c%2F<component>` followed by `LWR3008: Error loading …`.
> Scripted: `sf community publish -n "<Site>" -o <org>`, then poll
> `SELECT Status FROM BackgroundOperation WHERE Id='<jobId>'` until `Complete`.

---

## Setup checklist

Work through these in order. Steps 1–2 are admin configuration; steps 3–5 are code.

### 1. Experience Cloud site (the LO2 backend)

1. **Create or reuse an LWR site.**
   - **Lightning Out (LWR)** template → includes the Lightning Out page and container; skip 1b.
   - **Build Your Own (LWR)** → follow 1b.
   - An existing LWR site can be reused. Aura-based sites do **not** work.
2. **Add the Lightning Out container page** (Build Your Own only). In Experience Builder:
   **+ New Page → Standard Page → Lightning Out**, then add the component
   `force:lightningOutLWRContainer` to that page. It is LWR-only; if it is not listed, enable
   **Show All Components**. **Publish.**
3. **Enable guest access.** Experience Builder → **Settings → General** → allow guest users to
   access the site. LO2 guest embedding runs through the linked LWR site (see the note at the top).
4. **Clickjack protection.** Experience Builder → **Settings → Security & Privacy** → set
   **Allow framing of site pages on external domains (Good protection)**. Under **Trusted Domains
   for Inline Framing** add every external origin from the intake **and** the FinDock redirect
   domain:
   ```
   https://www.example.com
   https://*.findock.com
   ```
5. **Guest User permissions.** FinDock ships **persona-based permission set groups** that bundle
   the underlying permission sets; assign the group, not the individual sets. For the Guest User:
   - **FinDock Payer** (permission set group) — the payer persona. It contains the underlying
     **FinDock Core Experience Cloud Run** permission set, which is what actually grants the
     guest access to the managed Pay Button / Payment Method Selector and
     `cpm.API_PaymentIntent_V2`. If a guide names only "Experience Cloud Run", this group is
     where it comes from.
   - **FinDockLabs Payment Guest Access** (permission set) if using the `lwc-procode` template
     components.
   - The Flow's guest permission set if exposing a template Flow (`FinDockLabs Donation Flow
     Guest Access` / `FinDockLabs Checkout Flow Guest Access`), or grant run access to the
     customer's own Flow. Without this the embedded Flow renders an error for guests.
6. **Hide the site chrome inside the embed.** The Lightning Out page (route type
   `lightningOut2`) uses the site's `Inner` theme layout by default, so on a reused site with a
   header and footer those appear inside the iframe. Fix it in the DigitalExperienceBundle:
   copy the site's existing simple theme layout (`sfdc_cms__themeLayout/<name>`, a
   `community_layout:simpleThemeLayout`) to `blankThemeLayout`, add
   `{"layoutId":"blankThemeLayout","layoutType":"Blank"}` to the theme's `layouts`, and set the
   Lightning Out view's `themeLayoutType` to `"Blank"`. Deploy all three, then publish. Two things
   don't work: `themeLayoutType: "ServiceNotAvailable"` (the type must be listed in the theme's
   `layouts`), and mapping a second layout type to an existing `layoutId` (each `layoutId` can only
   be mapped once).
7. **Publish** the site again.

### 2. Org-level allow-lists (Setup)

All three are required; missing any one of them shows up as a blank iframe or a console error.

1. **Trusted Domains for Inline Frames** — **Setup → Session Settings → Trusted Domains for Inline
   Frames**. Add each external origin with **IFrame Type = Lightning Out**. (Same idea as step 1.4,
   but this is the org-level setting; both are needed.)
2. **Trusted URLs** — **Setup → Trusted URLs → New Trusted URL**. Add each external origin with
   **CSP Context = All** and the CSP directives LO2 needs (frame-src, connect-src). Also make sure
   `https://*.findock.com` is present as a Trusted URL (the templates ship
   `https://external.findock.com` for the Communities context; add the wildcard for LO2 if it is
   missing).
3. **CORS** — **Setup → CORS**. Add each external origin to the **Allowed Origins List** and tick
   **Enable CORS for OAuth endpoints**.

> **Same-origin hosts.** If the host page is served from the same `*.my.site.com` domain as the
> LWR site (typically another site in the same org, such as a Multi-Framework React site), host and
> iframe are same-origin. Verified end to end with a guest payment: none of the step 2 entries were
> needed, no Trusted Domains for Inline Framing on the site, and the site's default clickjack
> setting (`SameOriginOnly`) was fine. A custom domain on either site makes it cross-origin again,
> and then everything above applies.

#### Scripting and verifying the allow-lists

Useful when the host agent configures the org from the CLI rather than through Setup:

| Setup item | Metadata / API |
|---|---|
| Trusted Domains for Inline Frames | `IframeWhiteListUrlSettings`, entries with `context=LightningOut` and `<url>host</url>` (no scheme). **Singleton: a deploy replaces the whole list**, so retrieve and merge first (orgs often already have e.g. `*.slack.com` entries). |
| Site clickjack setting | `CustomSite.clickjackProtectionLevel`. "Allow framing of site pages on external domains" = `External` (others: `AllowAllFraming`, `SameOriginOnly`, `NoFraming`). |
| Site-level Trusted Domains for Inline Framing | Not in Network, CustomSite, or DigitalExperienceBundle metadata. Set it in Experience Builder. |
| Enable CORS for OAuth endpoints | `SecuritySettings` → `sessionSettings.enableOauthCorsPolicy` (a Settings deploy only touches the fields you list) |
| Require first-party use of Salesforce cookies | `MyDomainSettings.isFirstPartyCookieUseRequired` |
| CORS / Trusted URLs | `CorsWhitelistOrigin` / `CspTrustedSite` |
| Lightning Out app | **No Metadata API type**: create it in Setup. Verify it via Tooling API: `LightningOutApp` (`ApplicationName`, `IsEnabled`, `Runtime`) and `LightningOutAppComponent` (`ComponentName`, `Props`, `InitialHeight`, …). |

### 3. Expose the components

1. **Create the LWC to expose.** LO2 renders **LWCs only**. If the payment experience is a Flow,
   wrap it:

   The wrapper does more than host the Flow. The stock loader leaves gaps that it has to fill
   (verified on loader 2.2.5):
   - **Auto-resize doesn't work.** The loader receives `lo.resize` but ignores it, so the iframe
     stays about 150px tall. `IsAutoResizeEnabled` on the app component has no effect. The wrapper
     reports its own height to the host.
   - **Scrollbars.** The loader styles the iframe `overflow:auto`, inside a closed shadow root the
     host can't restyle. The wrapper sets `overflow:hidden` on the framed document instead.
   - **Scroll on validation errors.** Flow validation calls `scrollIntoView` on the error, which
     scrolls the frame and hides the top of the form. With `overflow:hidden` on `<html>`, `<body>`
     becomes its own scroll container, so `window.scrollTo(0, 0)` does nothing. Reset the scroll
     target from a **capture-phase** `scroll` listener, because scroll events don't bubble.
   - **Ready fires too early.** `lo.component.ready` fires before the Flow has started, so the Flow
     runtime's own spinner still shows. The wrapper posts its own "ready" once the Flow has started.

   Before copying the resize workaround, check whether a newer loader handles `lo.resize` itself.

   ```html
   <!-- force-app/main/default/lwc/donationFlowEmbed/donationFlowEmbed.html -->
   <template>
       <div class="flow-wrapper">
           <lightning-flow flow-api-name="Donation_Flow"
                           flow-input-variables={inputVariables}
                           onstatuschange={handleStatusChange}>
           </lightning-flow>
       </div>
   </template>
   ```

   ```javascript
   // donationFlowEmbed.js
   import { LightningElement, api } from 'lwc';

   // FinDock: postMessage types the host page listens for.
   const MSG_RESIZE = 'findock-embed:resize';
   const MSG_READY = 'findock-embed:ready';

   export default class DonationFlowEmbed extends LightningElement {
       // FinDock: host attributes (success-url, failure-url) arrive as camelCase @api props.
       // The matching Flow variables must be marked Available for input (isInput=true).
       @api successUrl;
       @api failureUrl;

       _framed = window.parent !== window;
       _observer;
       _readySent = false;

       get inputVariables() {
           const vars = [];
           if (this.successUrl) vars.push({ name: 'successUrl', type: 'String', value: this.successUrl });
           if (this.failureUrl) vars.push({ name: 'failureUrl', type: 'String', value: this.failureUrl });
           return vars;
       }

       connectedCallback() {
           if (!this._framed) return;
           // FinDock: no scrollbars inside the iframe; the host sizes the frame instead.
           document.documentElement.style.overflow = 'hidden';
           document.body.style.overflow = 'hidden';
           this._onScroll = (event) => {
               const targets = event.target === document
                   ? [document.documentElement, document.body]
                   : [event.target];
               targets.forEach((t) => { t.scrollTop = 0; t.scrollLeft = 0; });
               this._postHeight();
           };
           document.addEventListener('scroll', this._onScroll, true);
       }

       renderedCallback() {
           if (!this._framed || this._observer) return;
           this._observer = new ResizeObserver(() => this._postHeight());
           this._observer.observe(this.template.querySelector('.flow-wrapper'));
       }

       disconnectedCallback() {
           this._observer?.disconnect();
           if (this._onScroll) document.removeEventListener('scroll', this._onScroll, true);
       }

       _postHeight() {
           const wrapper = this.template.querySelector('.flow-wrapper');
           if (!wrapper) return;
           // FinDock: measure against the document, not the viewport. The LWR page adds padding
           // above the component, and body is the scroll container (see above).
           const height = Math.ceil(
               wrapper.getBoundingClientRect().bottom
               - document.documentElement.getBoundingClientRect().top
               + document.body.scrollTop
           ) + 16;
           window.parent.postMessage({ type: MSG_RESIZE, height }, '*');
       }

       handleStatusChange(event) {
           // FinDock: the Pay Button inside the Flow performs the PSP redirect itself.
           const { status } = event.detail;
           if (!this._framed || this._readySent) return;
           if (['STARTED', 'ERROR', 'FINISHED'].includes(status)) {
               this._readySent = true;
               // FinDock: report the height first, so the host reveals a correctly sized frame.
               requestAnimationFrame(() => {
                   this._postHeight();
                   window.parent.postMessage({ type: MSG_READY, status }, '*');
               });
           }
       }
   }
   ```

   ```xml
   <!-- donationFlowEmbed.js-meta.xml -->
   <?xml version="1.0" encoding="UTF-8"?>
   <LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
       <apiVersion>62.0</apiVersion>
       <isExposed>true</isExposed>
       <targets>
           <target>lightningCommunity__Page</target>
           <target>lightningCommunity__Default</target>
       </targets>
   </LightningComponentBundle>
   ```

   If exposing the pro-code form, no wrapper is needed: expose `c-payment-form` directly.
   Deploy with the host's Salesforce tooling (`sf project deploy start …`), then **republish the
   site** (see *Republish habit*). If you also change the Flow, **retrieve it from the org first**.
   Admins edit it in Flow Builder, and deploying a stale local copy silently reverts their changes.

2. **Create the Lightning Out 2.0 app.** **Setup → Lightning Out 2.0 App Manager → New**. Any
   name; **Runtime = CLWR**. **Enable** the app.
3. **Add the components.** Under **App Components** add the LWC(s) the external page will render,
   e.g. `c-donation-flow-embed` or `c-payment-form`.

   > 🚨 **Also add every LWC that the exposed Flow or LWC renders internally**, with its
   > namespace — for FinDock that means at least `cpm-pay-button` and
   > `cpm-payment-method-selector`, plus the unmanaged shared components the templates use
   > (`c-amount-and-frequency`, `c-currency-picker`, `c-payment-selector`,
   > `c-experience-progress-stages`, …). LO2 only ships components that are declared on the app;
   > an undeclared child renders blank.

   > ⚠️ **Security.** Every component on the app is publicly reachable under the linked site's
   > Guest User. If the Flow runs in **System Context Without Sharing** / "Access All Data",
   > guests inherit that access. Review the Flow's run mode and the guest user's object
   > permissions before exposing it.
4. **Link the Experience Cloud site.** In the app, set **Linked Community Site** to the LWR site
   from step 1 and **Save**. Saving redirects you into the Experience Cloud site to confirm; if
   step 1 is complete there is nothing to change there.
5. **Copy the generated embed code** from the app's main page and paste it into the external
   page. Then **add two attributes the generator omits** (step 4 below).

### 4. Host-page snippet — including `org-url` and `site-prefix`

The generated markup looks like the first three lines below. You **must** add `org-url` and
`site-prefix` yourself — they are not generated, they are poorly documented, and without them
LO2 initialises against the wrong site context and fails even when everything else is right.

```html
<!-- FinDock: Lightning Out 2.0 runtime, served by the org. Keep async. -->
<script type="text/javascript" async
        src="https://YOUR-ORG.my.salesforce.com/lightning/lightning.out.latest/index.iife.prod.js">
</script>

<!-- FinDock: one application element per page. org-url = the LWR SITE ORIGIN (not the
     /lightning-out page). site-prefix = the site's URL prefix, or "" if it has none. -->
<lightning-out-application
    org-url="https://YOUR-SITE.my.site.com"
    site-prefix="donations"
    app-id="YOUR_APP_ID"
    components="c-donation-flow-embed">
</lightning-out-application>

<!-- FinDock: the exposed component, placed wherever the form should render. -->
<c-donation-flow-embed></c-donation-flow-embed>
```

Rules for the two extra attributes:
- `org-url` is the **site origin**: `https://YOUR-SITE.my.site.com`. Never the Lightning Out page
  URL (`…/lightning-out`) and never the `my.salesforce.com` org URL.
- `site-prefix` is the path prefix configured on the Experience Cloud site (e.g. `donations` for
  `https://YOUR-SITE.my.site.com/donations`). **If the site has no prefix, still include the
  attribute as `site-prefix=""`** — omitting it breaks initialisation.
- `components` is a comma-separated list; you can render several exposed components on one page
  from a single application element.

- Put the `lightning-out-application` element **before** the component element (or create it
  first when building the DOM from script).

Pass properties to the exposed component as plain HTML attributes (kebab-case), e.g.
`<c-payment-form amount="25.00" default-currency="EUR"></c-payment-form>`. The loader delivers them
through `lo.setComponentData` as camelCase `@api` props. For a Flow, the wrapper maps them onto
`flow-input-variables`. Build the success and failure URLs on the host from its own location.

**Host CSP blocks the loader?** If the host page's `script-src` doesn't allow the org's
`my.salesforce.com` domain and you can't change it (a Multi-Framework React site allows only
`'self'`), **vendor the loader**: download `index.iife.prod.js` (about 26 KB, self-contained),
serve it from the host's own origin, and inject that. The loader only creates iframes and talks
`postMessage` to `org-url`, so nothing else needs allow-listing. The copy won't pick up `latest`
updates, so refresh it periodically. Don't load it from the site domain instead: that path
redirects elsewhere.

### 5. Host-page sizing and loading state

The host listens for the wrapper's messages (see step 3), checks the origin, and sizes the
**component element**. The iframe inside it is `height:100%`. Keep the embed invisible behind a
single host spinner until the wrapper says the Flow has started, so the payer never sees the Flow
runtime's own dots or an empty full-height box.

```html
<!-- FinDock: wrapper around the component element from step 4. -->
<div class="donation-embed" style="position:relative; min-height:720px">
    <div class="donation-embed__spinner" role="status">Loading secure payment form…</div>
    <c-donation-flow-embed style="display:block; height:720px; opacity:0"></c-donation-flow-embed>
</div>
<script>
    // FinDock: must equal the org-url on <lightning-out-application>.
    const SITE_ORIGIN = 'https://YOUR-SITE.my.site.com';
    const cmp = document.querySelector('c-donation-flow-embed');
    const spinner = document.querySelector('.donation-embed__spinner');
    const reveal = () => { cmp.style.opacity = '1'; spinner.hidden = true; };

    window.addEventListener('message', (event) => {
        if (event.origin !== SITE_ORIGIN || !event.data) return;
        if (event.data.type === 'findock-embed:resize') cmp.style.height = `${event.data.height}px`;
        if (event.data.type === 'findock-embed:ready') reveal();
    });
    // FinDock: loader errors. These events don't bubble, so listen in the capture phase.
    document.addEventListener('lo.component.error', () => {
        spinner.textContent = 'The payment form could not be loaded. Please try again later.';
        spinner.setAttribute('role', 'alert');
    }, true);
    document.addEventListener('lo.application.error', () => {
        spinner.textContent = 'The payment form could not be loaded. Please try again later.';
        spinner.setAttribute('role', 'alert');
    }, true);
    // FinDock: fallback in case the ready message never arrives.
    setTimeout(reveal, 15000);
</script>
```

Loader events: `lo.iframe.load`, `lo.component.ready`, `lo.component.error`, and
`lo.application.error`, dispatched on the component or application element. They **don't
bubble**: listen on the element itself, or with `capture: true` on an ancestor.

---

## Success / failure URLs and the PSP round-trip

- The managed **Pay Button redirects the whole top-level page** to the PSP's hosted payment
  page (not just the iframe), to avoid PSP pages refusing to load framed.
- Therefore **SuccessURL / FailureURL must point at pages on the external website**, not at
  Experience Cloud pages. In a Flow, set the Pay Button's `successUrl` / `failureUrl` inputs to
  e.g. `https://www.example.com/donate/thank-you` and `https://www.example.com/donate/failed`,
  ideally passed from the host through the wrapper's `successUrl` / `failureUrl` props (step 3).
  The host success route must also work on a direct page load, since the PSP returns straight to it.
  In `c-payment-form`, update the hardcoded URLs in `_updatePaymentIntentContext`.
- The templates' status-routing (`?status=success|failure` back into the Flow) does not apply
  when the return page is external; the external page owns the thank-you / retry UX. If the
  customer needs the final payment status there, use webhooks or polling from their own backend
  (`webhook-handler.md`) — never call the REST API from the host page's browser code.

---

## Styling and UX notes

- The embed adopts the **linked site's theme** (branding set, styling hooks). Theme changes on
  the site change the embed; republish after changing them.
- SLDS styling hooks set on the host page reach **some** elements inside the embed (standard
  `lightning-*` inputs, titles) but not everything (e.g. the amount/frequency controls). For
  consistent branding, style in the Experience Cloud theme rather than from the host page.
- All standard FinDock UI and accessibility rules (`accessibility.md`, `page-quality.md`,
  `donation-page-structure.md`) apply to whatever you build inside the LWC/Flow. The host page
  must additionally size the embed and avoid nested scroll containers (step 5).
- Template components sized for full-width pages can overflow a narrow embed. The templates'
  `c-experience-progress-stages` needs about 368px, more than the iframe of a 32rem card, and
  `overflow:hidden` then clips it. Below 480px, make its connectors
  `minmax(var(--slds-g-spacing-4), 1fr)` and give the stages `min-width: var(--slds-g-sizing-10)`.
- The Pay screen's redirect text ("After pressing pay, you will be redirected…") is stored **in
  the Flow**, in the Payment Method Selector's `paymentMethodConfig` JSON (`redirectInstruction`).
  The property editor copies it from the label `cpm.ec_placeholder_redirect_message` when the
  selector is configured, so a label override only affects selectors configured afterwards. To
  change an existing Flow, edit the JSON.

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Blank area where the component should be, no error | Component (or one of its children, e.g. `cpm-pay-button`) not declared on the Lightning Out app; or site not republished. |
| Console error about refused framing / `X-Frame-Options` | External origin missing from **Trusted Domains for Inline Framing** (site) or **Trusted Domains for Inline Frames** with type Lightning Out (Setup). |
| CORS error on `my.salesforce.com` or `my.site.com` | Origin missing from **Setup → CORS**, or **Enable CORS for OAuth endpoints** unchecked. |
| Runtime loads but fails to initialise, or "site not found" | `org-url` points at the wrong URL (use the site origin), or `site-prefix` missing/wrong (include it even as `""`). |
| Works logged in, fails for anonymous visitors | Guest access not enabled on the site, or Guest User lacks the **FinDock Payer** group, the FinDockLabs guest set, or run access to the Flow. |
| Payment starts but never completes for guests | ProcessingHub not connected or integration user lacks **FinDock Integration User** — see `experience-cloud.md`. |
| Works in Chrome, fails in Safari/private mode | Third-party cookies blocked, or **Require first-party use of Salesforce cookies** enabled in My Domain. |
| PSP redirect lands on an Experience Cloud page | SuccessURL / FailureURL still point at the site; change them to the external website. |
| Guest **401** on `…/webruntime/component/latest/…/c%2F<component>`, then `LWR3008: Error loading …` | Site not republished after linking the app or deploying the LWC. Republish. `curl` gets 401 on these URLs even for working components, so reproduce in a browser. |
| Loader script blocked by the host's CSP | Vendor the loader onto the host's own origin (step 4). |
| Iframe stuck at about 150px tall | Loader auto-resize doesn't work. Use the wrapper's resize messages (steps 3 and 5). |
| Top of the form hidden after a validation error | `scrollIntoView` scrolled the frame. Use the wrapper's capture-phase scroll reset (step 3). |
| Site header and footer inside the iframe | Lightning Out page uses the `Inner` layout. Map it to a Blank layout (step 1.6). |
| Flow's grey dots or spinner flash after `lo.component.ready` | `lo.component.ready` fires before the Flow starts. Reveal on the wrapper's ready message (step 5). |
| Unclear which props reached the component | The loader logs verbosely (`LO2:LightningOutComponent …`). The `lo.setComponentData` log line shows the props. |
| Password manager inline menu / shortcut doesn't fill fields in the embed | Password managers behave this way in iframes. Filling from the extension's toolbar menu works. The iframe `sandbox` is not the cause, so don't patch the loader. |

---

## Testing

- **Test as a guest in a private window.** A browser logged into Salesforce or Experience Builder
  also has a session on the `my.site.com` domain, so the embed can run as that user instead of the
  Guest User. That hides missing guest permissions and can cause access errors that don't happen
  for real payers.
- **Playwright works headlessly.** `page.frames()` includes the Lightning Out iframe even though it
  sits in a closed shadow root, and `frame.frameElement()` reaches the iframe element.
  `frame.getByLabel()` / `getByRole()` pierce the LWC shadow DOM, so you can drive the whole Flow,
  including a PSP test payment.
- **Check what the PSP was told.** `cpm__Inbound_Report__c.cpm__RAW_Message__c` holds the
  PaymentIntent (`SuccessURL` / `FailureURL`) and the PSP webhook payloads. That's the quickest way
  to confirm the return URLs.

---

## Division of labour

This is an **on-platform** target. Supply the FinDock contract (which components to expose, the
guest prerequisites, the redirect URLs, the allow-list entries) and defer the Salesforce plumbing
— creating the LWR site, the LWC bundle scaffolding and deployment, Setup configuration — to the
org-aware host when one is available. The authentication reference and credentials tooling
(Step 6) do **not** apply: the host page holds no token and never calls the REST API.
