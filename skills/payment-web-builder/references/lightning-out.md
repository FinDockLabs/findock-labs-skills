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
> provides the Flows and LWCs you expose, plus a ready-made LO2 wrapper for Flows: the
> `lightningOutFlowContainer` LWC in the `lightning-out-flow` package (*FinDock Experiences -
> Lightning Out Flow*). It runs any screen Flow and auto-sizes the iframe. Step 3 explains when to
> use it and when to write your own wrapper.

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
     `Checkout_Flow`, or the customer's own) → expose it through the FinDockLabs
     `c-lightning-out-flow-container` (or a custom wrapper, see step 3). LO2 can only expose LWCs,
     never a Flow directly.
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
   wrap it. There are two ways:

   | | **A. FinDockLabs Lightning Out Flow container** (default) | **B. Custom wrapper** (`donationFlowEmbed` below) |
   |---|---|---|
   | Source | `lightning-out-flow` package in the templates repo, LWC `lightningOutFlowContainer` (`c-lightning-out-flow-container`) | Written into the customer's project from this file |
   | Which Flow | Any screen Flow, chosen with the `flow-api-name` attribute | Hardcoded in the template |
   | Auto-sizing | Yes, `flow:height` messages | Yes, `findock-embed:resize` messages |
   | Hides the Flow runtime's loading dots behind its own spinner | Extend it (see *A3*) | Yes |
   | Ready message for the website's spinner | Extend it (see *A3*): `flow:ready` | Yes: `findock-embed:ready` |
   | Flow input variables from the host | Clone it and add `@api` props (see *A2*) | Already included (`successUrl`, `failureUrl`) |

   Use **A**; use **B** only when the container can't be used. Don't mix their message types:
   the host listener must match the component that is exposed.

   #### A. FinDockLabs Lightning Out Flow container

   Install *FinDock Experiences - Lightning Out Flow*, or deploy its `lightning-out-flow` package
   directory from the templates repo. It holds only the `lightningOutFlowContainer` LWC; the Flow
   itself comes from a template package or the customer's org. The component exposes one
   property, `flowApiName`, so the same container can run `Donation_Flow`, `Checkout_Flow`, or the
   customer's own Flow.

   **How the auto-sizing works.** The website can't see how tall the iframe's content is, so the
   container measures it and posts it to the website, which sizes the frame:
   - **Where it sends.** Lightning Out adds the website's origin to the iframe URL as
     `loAppOrigin`. The container posts `{ type: 'flow:height', height }` to that origin only. With
     no `loAppOrigin` (the component on a normal Experience Cloud page) it does nothing.
   - **What it measures.** A `ResizeObserver` on `document.body`, so the site's own spacing around
     the Flow is included. A new screen, an error message, or a section opening all trigger it.
   - **Unlocking the page height.** The LWR site makes `html` and `body` exactly as tall as the
     iframe, so the frame could grow but never shrink. The container injects
     `html,body{height:auto!important;min-height:100%!important;}` so the page takes its content's
     height.
   - **No collapse between screens.** While the next screen loads, the Flow shows only its spinner.
     Taller heights are sent at once (no scrollbar ever appears). Shorter heights are sent at once
     after `statuschange` (the new screen has finished rendering), and otherwise only if they last
     2 seconds, which a spinner never does but a closed error message does.

   Host-page markup and listener: step 4 and step 5 (*Option A*). When building with the
   container, extend it with the loading state (*A3*).

   #### A2. Passing values from the website into the Flow

   The container passes nothing to the Flow except its API name. Typical values the Flow needs
   from the website:
   - **Success and failure URLs.** The PSP returns the payer to these, and on an embed they must
     be pages on the website (see *Success / failure URLs and the PSP round-trip*). Passing them
     from the website lets one Flow serve several pages or environments.
   - **A record Id the website already knows**, e.g. a Contact Id, so the Flow can prefill the
     payer's details.

   1. **Add input variables to the Flow** (Text, *Available for input*), e.g. `successUrl`,
      `failureUrl`, `contactId`. Salesforce only applies input values to such variables, and only
      when the interview starts.
      - **For the URLs**, set each Pay Button's Success URL and Failure URL to `{!successUrl}` /
        `{!failureUrl}` instead of the template's `https://www.example.com/...` values. Do it in
        Flow Builder, not in the XML: each Pay Button stores the URLs twice (its `successUrl` /
        `failureUrl` inputs and its property-editor JSON), and `Checkout_Flow` has two Pay
        Buttons.
   2. **Clone the container** into a component of your own (e.g. `donationFlowContainer`). It is
      package-owned, so don't edit it in place (see `adjusting-existing-pages.md` → Step C). Copy
      `lightningOutFlowContainer.js` as it is, add one `@api` property per value and an
      `inputVariables` getter, and bind the getter in the template:

      ```javascript
      // donationFlowContainer.js — a copy of lightningOutFlowContainer.js plus the lines marked "Added"
      import { LightningElement, api } from 'lwc';

      // … constants from lightningOutFlowContainer.js, unchanged …

      export default class DonationFlowContainer extends LightningElement {
          @api flowApiName;
          // Added: host attributes (success-url, failure-url, contact-id) arrive as camelCase props.
          @api successUrl;
          @api failureUrl;
          @api contactId;

          // Added: names and types must match the Flow input variables.
          get inputVariables() {
              const variables = [];
              if (this.successUrl) {
                  variables.push({ name: 'successUrl', type: 'String', value: this.successUrl });
              }
              if (this.failureUrl) {
                  variables.push({ name: 'failureUrl', type: 'String', value: this.failureUrl });
              }
              if (this.contactId) {
                  variables.push({ name: 'contactId', type: 'String', value: this.contactId });
              }
              return variables;
          }

          // … fields and methods from lightningOutFlowContainer.js, unchanged …
      }
      ```

      ```html
      <!-- donationFlowContainer.html -->
      <template>
          <lightning-flow
              flow-api-name={flowApiName}
              flow-input-variables={inputVariables}
              onstatuschange={handleStatusChange}>
          </lightning-flow>
      </template>
      ```

      Copy `lightningOutFlowContainer.js-meta.xml` too, with its own `masterLabel`.
   3. **Set the values on the website** as kebab-case attributes next to `flow-api-name`:
      ```html
      <c-donation-flow-container
          flow-api-name="Donation_Flow"
          success-url="https://www.example.com/donate/thank-you"
          failure-url="https://www.example.com/donate/failed"
          contact-id="003…">
      </c-donation-flow-container>
      ```
      Input values are read once, when the interview starts, so the attributes must be on the
      element before the Flow starts. Changing them afterwards doesn't reach the running Flow.
      The success page must also work on a direct page load, since the PSP returns straight to it.
   4. Put the clone on the Lightning Out app (instead of, or next to, the original), use its tag in
      the host markup and listener, and **republish the site**.

   Check in the browser console that the values arrived: the loader logs the props in its
   `lo.setComponentData` line. To confirm which URLs the PSP got, see *Testing*
   (`cpm__Inbound_Report__c`).

   > ⚠️ Anything passed this way comes from the public website and can be changed by the
   > visitor. The Flow runs as the site's Guest User, so treat the value as untrusted input: don't
   > let it unlock records the guest shouldn't see.

   #### A3. Loading state: hide the Flow runtime's dots, tell the website when ready

   Until the first screen renders, `<lightning-flow>` shows the runtime's own grey dots, and the
   stock container shows them to the payer (about 1.5 seconds in testing). CSS can't restyle or
   remove them, because they sit in the runtime's shadow DOM. When building with the container,
   **extend it with the part of option B that hides them**: keep the Flow at `opacity:0` and show
   your own spinner until `statuschange` reports that the first screen is on show. Then post a
   `flow:ready` message, so the website can also cover the loader's start-up with its own spinner
   (step 5, *Option A*), the same way option B does.

   Do it in the clone from *A2* (or clone the container for this alone). Additions to the clone:

   ```html
   <!-- donationFlowContainer.html -->
   <template>
       <div class={wrapperClass}>
           <!-- FinDock: our spinner, centred in the form's own box. -->
           <template lwc:if={isLoading}>
               <div class="flow-loading" role="status">
                   <span class="flow-loading__ring" aria-hidden="true"></span>
                   <span class="flow-loading__label">Loading secure payment form…</span>
               </div>
           </template>
           <!-- FinDock: the Flow renders (and starts) underneath, invisible, so its runtime dots never show. -->
           <div class={flowClass} aria-hidden={ariaHiddenFlow}>
               <lightning-flow
                   flow-api-name={flowApiName}
                   flow-input-variables={inputVariables}
                   onstatuschange={handleStatusChange}>
               </lightning-flow>
           </div>
       </div>
   </template>
   ```

   Without *A2*, leave out `flow-input-variables`.

   CSS: copy `donationFlowEmbed.css` from option B unchanged. The ring takes the linked site's brand
   colour (`--dxp-g-brand`), so it matches the site's theme. Put the label text in a Custom Label
   if the site is translated.

   ```javascript
   // donationFlowContainer.js — additions to the clone, marked "Added"
   // Added: must match the website's listener (step 5, Option A).
   const READY_MESSAGE_TYPE = 'flow:ready';
   // Added: statuses that mean the first screen has rendered (or the Flow failed to start).
   const LOADED_STATUSES = ['STARTED', 'ERROR', 'FINISHED'];
   // Added: never leave the payer on a spinner if statuschange doesn't arrive.
   const LOADING_FALLBACK_MS = 15000;

   export default class DonationFlowContainer extends LightningElement {
       // … @api properties and fields from the clone …
       isLoading = true;
       loadingFallback;
       readySent = false;

       get wrapperClass() {
           return this.isLoading ? 'flow-wrapper flow-wrapper--loading' : 'flow-wrapper';
       }
       get flowClass() {
           return this.isLoading ? 'flow-body flow-body--hidden' : 'flow-body';
       }
       get ariaHiddenFlow() {
           return this.isLoading ? 'true' : 'false';
       }

       connectedCallback() {
           // Added
           // eslint-disable-next-line @lwc/lwc/no-async-operation
           this.loadingFallback = setTimeout(() => {
               this.isLoading = false;
           }, LOADING_FALLBACK_MS);
           // … the container's connectedCallback code, unchanged …
       }

       disconnectedCallback() {
           clearTimeout(this.shrinkTimeout);
           clearTimeout(this.loadingFallback);   // Added
       }

       handleStatusChange(event) {
           const isLoaded = LOADED_STATUSES.includes(event.detail.status);
           // Added: first screen is on show, so swap our spinner for the Flow.
           if (this.isLoading && isLoaded) {
               this.isLoading = false;
               clearTimeout(this.loadingFallback);
           }
           // Changed: measure after the re-render that removed the spinner and its min-height,
           // so the frame shrinks at once instead of after the 2-second shrink delay.
           // eslint-disable-next-line @lwc/lwc/no-async-operation
           requestAnimationFrame(() => {
               this.reportHeight(true);
               // Added: tell the website once, after the height, so it reveals a correctly sized frame.
               if (PARENT_ORIGIN && isLoaded && !this.readySent) {
                   this.readySent = true;
                   window.parent.postMessage({ type: READY_MESSAGE_TYPE }, PARENT_ORIGIN);
               }
           });
       }

       // … other methods from lightningOutFlowContainer.js, unchanged …
   }
   ```

   The spinner inside the iframe can't cover the time before the iframe exists, while the
   Lightning Out loader starts (about 2 seconds in testing). The website's own spinner covers
   that and comes off on `flow:ready` (step 5, *Option A*).

   #### B. Custom wrapper

   Write your own wrapper only when the container (*A*) can't be used. It does more than host the
   Flow. The stock loader leaves gaps that it
   has to fill (verified on loader 2.2.5):
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
   - **The Flow runtime's loading indicator is not ours.** `<lightning-flow>` shows its own grey
     dots / spinner until the first screen renders. It sits in the runtime's shadow DOM, so CSS can't
     restyle or remove it. The wrapper keeps the Flow at `opacity:0` and shows **its own** spinner
     until `statuschange` reports `STARTED`. Never render the Flow visibly and put a spinner on top
     of it. This applies to every Flow-based form, not only Lightning Out (see `experience-cloud.md`
     → *Loading state for Flow-based forms*).

   Before copying the resize workaround, check whether a newer loader handles `lo.resize` itself.

   ```html
   <!-- force-app/main/default/lwc/donationFlowEmbed/donationFlowEmbed.html -->
   <template>
       <div class={wrapperClass}>
           <!-- FinDock: our spinner, centred in the form's own box (see donationFlowEmbed.css). -->
           <template lwc:if={isLoading}>
               <div class="flow-loading" role="status">
                   <span class="flow-loading__ring" aria-hidden="true"></span>
                   <span class="flow-loading__label">Loading secure payment form…</span>
               </div>
           </template>
           <!-- FinDock: the Flow renders (and starts) underneath, invisible, so its runtime dots never show. -->
           <div class={flowClass} aria-hidden={ariaHiddenFlow}>
               <lightning-flow flow-api-name="Donation_Flow"
                               flow-input-variables={inputVariables}
                               onstatuschange={handleStatusChange}>
               </lightning-flow>
           </div>
       </div>
   </template>
   ```

   ```css
   /* donationFlowEmbed.css */
   /* FinDock: the wrapper is the positioning context, so the spinner centres on the FORM,
      not the page. Never use position:fixed or 100vh for the loading state. */
   .flow-wrapper { position: relative; }
   /* FinDock: reserve roughly the first screen's height while loading so the spinner sits in
      the middle of where the form will appear, and the page doesn't jump. */
   .flow-wrapper--loading { min-height: 480px; }

   .flow-body--hidden { opacity: 0; pointer-events: none; }
   .flow-body { transition: opacity 150ms ease-in; }

   .flow-loading {
       position: absolute;
       inset: 0;
       z-index: 1;
       display: flex;
       flex-direction: column;
       align-items: center;
       justify-content: center;
       gap: 0.75rem;
       text-align: center;
   }
   .flow-loading__ring {
       width: 2.5rem;
       height: 2.5rem;
       border-radius: 50%;
       /* FinDock: follow the LWR site's brand colour; the fallback is SLDS brand blue. */
       border: 3px solid var(--dxp-s-form-element-color-border, #d8dde6);
       border-top-color: var(--dxp-g-brand, #0176d3);
       animation: flow-loading-spin 0.8s linear infinite;
   }
   .flow-loading__label { font-size: 0.875rem; color: var(--dxp-g-root-contrast-2, #444); }
   @keyframes flow-loading-spin { to { transform: rotate(360deg); } }
   @media (prefers-reduced-motion: reduce) {
       .flow-loading__ring { animation-duration: 2.4s; }
   }
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
       isLoading = true;

       get wrapperClass() {
           return this.isLoading ? 'flow-wrapper flow-wrapper--loading' : 'flow-wrapper';
       }
       get flowClass() {
           return this.isLoading ? 'flow-body flow-body--hidden' : 'flow-body';
       }
       get ariaHiddenFlow() {
           return this.isLoading ? 'true' : 'false';
       }

       get inputVariables() {
           const vars = [];
           if (this.successUrl) vars.push({ name: 'successUrl', type: 'String', value: this.successUrl });
           if (this.failureUrl) vars.push({ name: 'failureUrl', type: 'String', value: this.failureUrl });
           return vars;
       }

       connectedCallback() {
           // FinDock: never leave the payer on a spinner if statuschange never arrives.
           this._fallback = setTimeout(() => { this.isLoading = false; }, 15000);
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
           clearTimeout(this._fallback);
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
           if (!['STARTED', 'ERROR', 'FINISHED'].includes(status)) return;
           // FinDock: first screen is rendered, so swap our spinner for the Flow.
           this.isLoading = false;
           clearTimeout(this._fallback);
           if (!this._framed || this._readySent) return;
           this._readySent = true;
           // FinDock: report the height first, so the host reveals a correctly sized frame.
           // The rAF runs after the re-render that removed the spinner and its min-height.
           requestAnimationFrame(() => {
               this._postHeight();
               window.parent.postMessage({ type: MSG_READY, status }, '*');
           });
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

   B's resize message differs from A's, so the host listener is different too (step 5, *Option
   B*).

   If exposing the pro-code form, no wrapper is needed: expose `c-payment-form` directly.
   Deploy with the host's Salesforce tooling (`sf project deploy start …`), then **republish the
   site** (see *Republish habit*). If you also change the Flow, **retrieve it from the org first**.
   Admins edit it in Flow Builder, and deploying a stale local copy silently reverts their changes.

2. **Create the Lightning Out 2.0 app.** **Setup → Lightning Out 2.0 App Manager → New**. Any
   name; **Runtime = CLWR**. **Enable** the app.
3. **Add the components.** Under **App Components** add the LWC(s) the external page will render,
   e.g. `c-lightning-out-flow-container`, `c-donation-flow-embed`, or `c-payment-form`.

   > 🚨 **Also add every LWC that the exposed Flow or LWC renders internally**, with its
   > namespace — for FinDock that means at least `cpm-pay-button` and
   > `cpm-payment-method-selector`, plus the unmanaged shared components the templates use
   > (`c-amount-and-frequency`, `c-currency-picker`, `c-payment-selector`,
   > `c-experience-progress-stages`, …). LO2 only ships components that are declared on the app;
   > an undeclared child renders blank.
   >
   > LWC **Flow actions** go on the app too, even though they aren't rendered. The templates'
   > `Get User Agent Info` action needs `c-get-user-agent-info` on the app; the same goes for
   > any LWC Flow action of the customer's own.

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

With the FinDockLabs container (step 3, option A), the component element names the Flow:

```html
<lightning-out-application
    org-url="https://YOUR-SITE.my.site.com"
    site-prefix="donations"
    app-id="YOUR_APP_ID"
    components="c-lightning-out-flow-container">
</lightning-out-application>

<!-- FinDock: flow-api-name picks the screen Flow the container runs. -->
<c-lightning-out-flow-container flow-api-name="Donation_Flow"></c-lightning-out-flow-container>
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
`flow-input-variables` (with the FinDockLabs container, clone it first: step 3, *A2*).

**Host CSP blocks the loader?** If the host page's `script-src` doesn't allow the org's
`my.salesforce.com` domain and you can't change it (a Multi-Framework React site allows only
`'self'`), **vendor the loader**: download `index.iife.prod.js` (about 26 KB, self-contained),
serve it from the host's own origin, and inject that. The loader only creates iframes and talks
`postMessage` to `org-url`, so nothing else needs allow-listing. The copy won't pick up `latest`
updates, so refresh it periodically. Don't load it from the site domain instead: that path
redirects elsewhere.

### 5. Host-page sizing and loading state

The listener depends on which wrapper is exposed (step 3).

#### Option A — FinDockLabs Lightning Out Flow container

Add this script after the Lightning Out markup. It applies each `flow:height` message to the
component element, and the iframe fills that element:

```html
<script>
    // FinDock: the site origin, read from org-url. Messages from any other origin are ignored.
    const flowOrigin = new URL(document.querySelector('lightning-out-application').getAttribute('org-url')).origin;
    const flowContainer = document.querySelector('c-lightning-out-flow-container');

    window.addEventListener('message', (event) => {
        // FinDock: the type check skips Lightning Out's own messages.
        if (event.origin === flowOrigin && event.data?.type === 'flow:height') {
            flowContainer.style.height = `${event.data.height}px`;
        }
    });
</script>
```

- Don't put **`flex: 1`** or a height **`transition`** on `c-lightning-out-flow-container`.
  `flex: 1` overrides the height the script sets, and a transition makes a scrollbar flash each
  time the Flow grows.
- For a clone (step 3, *A2*), change the selector to the clone's tag.

**With the loading state from step 3, *A3*.** Same wrapper, spinner, and CSS as Option B below
(and the same rules for centring the spinner on the form). Only the component tag and the message
types differ:

```html
<!-- FinDock: wrapper around the component element from step 4. Same width as the form column.
     Styles: copy the <style> block from Option B. -->
<div class="donation-embed">
    <div class="donation-embed__spinner" role="status">
        <span class="donation-embed__ring" aria-hidden="true"></span>
        <span>Loading secure payment form…</span>
    </div>
    <c-donation-flow-container flow-api-name="Donation_Flow"
                               style="display:block; height:720px; opacity:0">
    </c-donation-flow-container>
</div>
<script>
    // FinDock: the site origin, read from org-url. Messages from any other origin are ignored.
    const flowOrigin = new URL(document.querySelector('lightning-out-application').getAttribute('org-url')).origin;
    const flowContainer = document.querySelector('c-donation-flow-container');
    const spinner = document.querySelector('.donation-embed__spinner');
    const reveal = () => {
        flowContainer.style.opacity = '1';
        spinner.hidden = true;
        flowContainer.parentElement.style.minHeight = '0';   // FinDock: the frame height now comes from flow:height
    };
    const showLoadError = () => {
        spinner.textContent = 'The payment form could not be loaded. Please try again later.';
        spinner.setAttribute('role', 'alert');
    };

    window.addEventListener('message', (event) => {
        if (event.origin !== flowOrigin) return;
        if (event.data?.type === 'flow:height') flowContainer.style.height = `${event.data.height}px`;
        if (event.data?.type === 'flow:ready') reveal();
    });
    // FinDock: loader errors. These events don't bubble, so listen in the capture phase.
    document.addEventListener('lo.component.error', showLoadError, true);
    document.addEventListener('lo.application.error', showLoadError, true);
    // FinDock: fallback in case the ready message never arrives.
    setTimeout(reveal, 15000);
</script>
```

#### Option B — custom wrapper

The host listens for the wrapper's messages (see step 3), checks the origin, and sizes the
**component element**. The iframe inside it is `height:100%`. Keep the embed invisible behind a
single host spinner until the wrapper says the Flow has started, so the payer never sees the Flow
runtime's own dots or an empty full-height box.

**Centre the spinner on the form, not the page.** The spinner overlay and the component element
share one wrapper that has `position:relative` and **the form column's width** (the same
`max-width` / grid cell the form will occupy). The overlay fills that wrapper with
`position:absolute; inset:0` and centres with flexbox. Each of these shortcuts puts it in the
wrong place:
- `position:fixed`, `100vh`, or a spinner outside the form's container centres it on the
  viewport.
- A wrapper wider than the form (full-width section, two-column layout) puts it off-centre.
- A `<lightning-spinner>` / `.slds-spinner_container` without a `position:relative` parent
  centres it on the page, because it is absolutely positioned against the nearest positioned
  ancestor.

```html
<!-- FinDock: wrapper around the component element from step 4. Same width as the form column. -->
<div class="donation-embed">
    <div class="donation-embed__spinner" role="status">
        <span class="donation-embed__ring" aria-hidden="true"></span>
        <span>Loading secure payment form…</span>
    </div>
    <c-donation-flow-embed style="display:block; height:720px; opacity:0"></c-donation-flow-embed>
</div>
<style>
    .donation-embed { position: relative; min-height: 720px; width: 100%; max-width: 640px; margin-inline: auto; }
    .donation-embed__spinner {
        position: absolute; inset: 0; z-index: 1;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        gap: .75rem; text-align: center; padding: 1rem;
    }
    /* FinDock: display:flex above beats the [hidden] attribute, so restate it or the spinner never goes away. */
    .donation-embed__spinner[hidden] { display: none; }
    .donation-embed__ring {
        width: 2.5rem; height: 2.5rem; border-radius: 50%;
        border: 3px solid #d8dde6; border-top-color: var(--brand-color, #0176d3);   /* use the site's brand colour */
        animation: donation-embed-spin .8s linear infinite;
    }
    @keyframes donation-embed-spin { to { transform: rotate(360deg); } }
    @media (prefers-reduced-motion: reduce) { .donation-embed__ring { animation-duration: 2.4s; } }
</style>
<script>
    // FinDock: must equal the org-url on <lightning-out-application>.
    const SITE_ORIGIN = 'https://YOUR-SITE.my.site.com';
    const cmp = document.querySelector('c-donation-flow-embed');
    const spinner = document.querySelector('.donation-embed__spinner');
    const reveal = () => {
        cmp.style.opacity = '1';
        spinner.hidden = true;
        cmp.parentElement.style.minHeight = '0';   // FinDock: the frame height now comes from the resize messages
    };

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
  ideally passed from the host through the wrapper's `successUrl` / `failureUrl` props (step 3;
  with the FinDockLabs container, *A2*).
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
| Blank area where the component should be, no error | Component (or one of its children, e.g. `cpm-pay-button`, or an LWC Flow action such as `c-get-user-agent-info`) not declared on the Lightning Out app; or site not republished. |
| Console error about refused framing / `X-Frame-Options` | External origin missing from **Trusted Domains for Inline Framing** (site) or **Trusted Domains for Inline Frames** with type Lightning Out (Setup). |
| CORS error on `my.salesforce.com` or `my.site.com` | Origin missing from **Setup → CORS**, or **Enable CORS for OAuth endpoints** unchecked. |
| Runtime loads but fails to initialise, or "site not found" | `org-url` points at the wrong URL (use the site origin), or `site-prefix` missing/wrong (include it even as `""`). |
| Works logged in, fails for anonymous visitors | Guest access not enabled on the site, or Guest User lacks the **FinDock Payer** group, the FinDockLabs guest set, or run access to the Flow. |
| Payment starts but never completes for guests | ProcessingHub not connected or integration user lacks **FinDock Integration User** — see `experience-cloud.md`. |
| Works in Chrome, fails in Safari/private mode | Third-party cookies blocked, or **Require first-party use of Salesforce cookies** enabled in My Domain. |
| PSP redirect lands on an Experience Cloud page | SuccessURL / FailureURL still point at the site; change them to the external website. |
| Guest **401** on `…/webruntime/component/latest/…/c%2F<component>`, then `LWR3008: Error loading …` | Site not republished after linking the app or deploying the LWC. Republish. `curl` gets 401 on these URLs even for working components, so reproduce in a browser. |
| Loader script blocked by the host's CSP | Vendor the loader onto the host's own origin (step 4). |
| Iframe stuck at about 150px tall | Loader auto-resize doesn't work. Use the wrapper's resize messages (steps 3 and 5). With the FinDockLabs container: the host listener is missing, listens for the wrong type (`flow:height`), or selects the wrong tag. |
| Iframe ignores the height, or a scrollbar flashes each time the Flow grows | `flex: 1` or a height `transition` on the component element (step 5, *Option A*). |
| Values from the website (success/failure URLs, a Contact Id) don't reach the Flow | The stock container passes only `flow-api-name`: clone it and map `@api` props to `flow-input-variables`. The Flow variable must be *Available for input*, and the attribute must be on the element before the Flow starts (step 3, *A2*). |
| Top of the form hidden after a validation error | Custom wrapper (option B): `scrollIntoView` scrolled the frame. Use the wrapper's capture-phase scroll reset (step 3). Not seen with the FinDockLabs container, which makes the page as tall as its content. |
| Site header and footer inside the iframe | Lightning Out page uses the `Inner` layout. Map it to a Blank layout (step 1.6). |
| Flow's grey dots or spinner flash after `lo.component.ready` | `lo.component.ready` fires before the Flow starts. Reveal on the wrapper's ready message (step 5). |
| Flow runtime's own spinner visible next to (or instead of) ours | The `<lightning-flow>` is visible while loading. Keep it at `opacity:0` in the wrapper until `statuschange` = `STARTED` (step 3). Its spinner can't be restyled with CSS. With the FinDockLabs container: the stock container shows them; extend it as in step 3, *A3*. |
| Spinner centred on the page or off to one side, not on the form | The overlay isn't inside a `position:relative` box the width of the form, or it uses `position:fixed` / `100vh` / a bare `<lightning-spinner>` (step 5). |
| Spinner never disappears | A `display:flex` rule overrides the `hidden` attribute. Add `[hidden] { display:none }` (step 5). |
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
