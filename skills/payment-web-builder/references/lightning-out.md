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
   Each one must be allow-listed in four places (see the checklist).
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

> ⚠️ **Republish habit.** Many of the steps below change the Experience Cloud site. Some changes
> only take effect after **Publish** in Experience Builder, and it is not always obvious which.
> Republish after every change to the site, its settings, or its security configuration.

---

## Setup checklist

Work through these in order. Steps 1–2 are admin configuration; step 3 is the only code.

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
6. **Publish** the site again.

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

### 3. Expose the components

1. **Create the LWC to expose.** LO2 renders **LWCs only**. If the payment experience is a Flow,
   wrap it:

   ```html
   <!-- force-app/main/default/lwc/donationFlowEmbed/donationFlowEmbed.html -->
   <template>
       <lightning-flow flow-api-name="Donation_Flow"
                       onstatuschange={handleStatusChange}>
       </lightning-flow>
   </template>
   ```

   ```javascript
   // donationFlowEmbed.js
   import { LightningElement } from 'lwc';

   export default class DonationFlowEmbed extends LightningElement {
       handleStatusChange(event) {
           // FinDock: the Pay Button inside the Flow performs the PSP redirect itself;
           // this hook is only for FINISHED handling (e.g. analytics) if you add screens after payment.
           if (event.detail.status === 'FINISHED') { /* optional */ }
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
   Deploy with the host's Salesforce tooling (`sf project deploy start …`).

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

Pass properties to the exposed component as plain HTML attributes (kebab-case), e.g.
`<c-payment-form amount="25.00" default-currency="EUR"></c-payment-form>`.

---

## Success / failure URLs and the PSP round-trip

- The managed **Pay Button redirects the whole top-level page** to the PSP's hosted payment
  page (not just the iframe), to avoid PSP pages refusing to load framed.
- Therefore **SuccessURL / FailureURL must point at pages on the external website**, not at
  Experience Cloud pages. In a Flow, set the Pay Button's `successUrl` / `failureUrl` inputs to
  e.g. `https://www.example.com/donate/thank-you` and `https://www.example.com/donate/failed`.
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
  must additionally give the iframe enough height and avoid nested scroll containers.

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

---

## Division of labour

This is an **on-platform** target. Supply the FinDock contract (which components to expose, the
guest prerequisites, the redirect URLs, the allow-list entries) and defer the Salesforce plumbing
— creating the LWR site, the LWC bundle scaffolding and deployment, Setup configuration — to the
org-aware host when one is available. The authentication reference and credentials tooling
(Step 6) do **not** apply: the host page holds no token and never calls the REST API.
