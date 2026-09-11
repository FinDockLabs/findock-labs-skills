# Pattern 6 — Experience Cloud (FinDock Payment Experiences)

Use this when the deployment target from intake Question 1 is **Salesforce Experience Cloud**.

> **Status**: FinDock Payment Experiences is in a **closed pilot** at time of writing. Tell the
> user to contact FinDock Support to participate. Always verify current component names,
> permission sets, and availability against the docs MCP (`https://docs.findock.com/mcp`) and
> the FinDockLabs templates repo before finalizing — pilot details change.

FinDock Payment Experiences lets you build payment pages natively in Salesforce with full
control of the UX, using managed building blocks instead of hand-rolling the whole flow. There
are two implementation routes (this maps to the intake sub-questions):

## Route A — FinDock out-of-the-box LWC components

FinDock provides **managed Lightning Web Components** that work both as Flow screen components
**and** as custom-element tags you embed directly in your own LWC:

- **FinDock Payment Method Selector** (managed LWC, tag `cpm-payment-method-selector`): visual
  configuration of payment methods, processors, target merchant accounts, and parameters. When
  shown to the payer it renders the enabled methods (and any configured parameters) for
  selection. Familiar to anyone who has used Giving Pages payment method configuration.
  In a custom LWC it takes a `payment-method-config` property (the method array) and emits a
  `paymentmethodchanged` event whose `detail` is the payer's selection (`name`, `processor`,
  `target`, parameters). Config shape, props, and events are documented in
  `references/payment-method-selector-config.md`.
- **FinDock Pay Button** (managed LWC, tag `cpm-pay-button`): builds/sends the PaymentIntent and
  initiates payment on click, redirecting to the PSP when confirmation is required. In a Flow it
  uses a visual editor mapping Flow variables -> PaymentIntent; in a custom LWC you pass the
  assembled PaymentIntent object via the `payment-intent` property and gate it with `disabled`.
  If using the Payment Method Selector, feed its selection into the PaymentIntent you hand to the
  Pay Button (or, in Flow, link its output to the Pay Button's Payment Method variable).
- **Amount & Frequency selector** (UNMANAGED component, tag `c-amount-and-frequency`): provided
  as part of the starter templates for one-time and recurring donations. Because it's unmanaged,
  you can use and extend it in any environment. It dispatches both a `FlowAttributeChangeEvent`
  (for Flow) **and** an `amountfrequencychanged` `CustomEvent` (for custom LWC) carrying
  `amountOneTime`, `amountRecurring`, and `frequency`.

Within Route A there are **two ways to assemble the form** (intake sub-question):

1. **Flow as the form builder** — drop the managed components (`cpm:paymentMethodSelector`,
   `cpm:payButton`) into a Screen Flow; **no custom Apex needed**. Best for low-code,
   admin-maintained journeys; supports single-step and multi-step forms, conditional logic, and
   validation. FinDock provides Flow templates (single-step and multi-step screen flows)
   deployable from FinDock Labs (https://github.com/FinDockLabs/payment-experiences-templates). Drop
   the Flow into an Experience Cloud page and it adopts the site theme. See the **Flow worked
   example** below for the screen order, the selector's `frequency` input, the Contact subflow,
   amount-routing formulas, and status-based decision routing.
2. **Build the whole form in LWC** — embed the managed components directly inside your own
   custom LWC. Best when you need UX the Flow screen can't express, while still avoiding
   hand-rolled PaymentIntent logic. The Payment Method Selector, Pay Button, and Amount &
   Frequency component are all embeddable as custom-element tags today (see worked example
   below).

> **The Payment Method Selector is now LWC-enabled.** Earlier pilot builds exposed the selector
> only to the Flow builder; it can now be embedded directly in a custom LWC as
> `<cpm-payment-method-selector>`, alongside `<cpm-pay-button>` and the unmanaged
> `<c-amount-and-frequency>`. So "build the whole form in LWC" no longer requires hand-rolling
> method selection from `cpm.API_PaymentMethod_V2.getPaymentMethods()` — use the managed
> selector and only drop to custom rendering if you need UX it can't express. The reference
> implementation is the `lwc-procode` package (`sfdx-source/packages/lwc-procode/lwc/paymentForm`) in the FinDockLabs templates repo
> (https://github.com/FinDockLabs/payment-experiences-templates). Re-check the docs MCP for the
> current pilot component names before finalizing.

### Worked example — Flow assembling the managed components

Mirrors the FinDockLabs `One_Screen_Donation_Flow` / `Multi_Screen_Donation_Flow` templates.
**No custom Apex** — the managed screen components do the work. A Screen Flow collects input and
the **Pay Button screen component** (`cpm:payButton`) submits the PaymentIntent and handles the
PSP redirect. In Flow the components use the colon form (`cpm:payButton`,
`cpm:paymentMethodSelector`, `c:amountAndFrequency`).

**Screen field order (single-screen template):**
1. `c:amountAndFrequency` (unmanaged) — outputs `frequency` + `amountOneTime` (store output automatically).
2. First Name / Last Name — two-column section, required text inputs.
3. `flowruntime:email` — the standard email screen component (built-in format validation), not a plain text input.
4. `cpm:paymentMethodSelector` — **input** `frequency` (wired from `amountAndFrequency.frequency`, so it only offers methods valid for the chosen frequency); **output** `context` (the selection, stored automatically).
5. `cpm:payButton` — submits and redirects.

**Pay Button inputs (wire these):**
- `contact` ← a Contact record (see Contact subflow below).
- payment method ← `paymentMethodSelector.context`.
- one-time amount ← formula `One_Time_Amount` = `IF({!amountAndFrequency.frequency}="oneTime", {!amountAndFrequency.amountOneTime}, 0)`.
- recurring amount ← formula `Recurring_Amount` = `IF({!amountAndFrequency.frequency}="recurring", {!amountAndFrequency.amountOneTime}, 0)`.
- `successUrl` / `failureUrl` ← pages within your Experience Cloud site (the template appends `?status=success` / `?status=failure`).
- currency + frequency.

**Resolve the Contact in a subflow, not inline.** The template calls a `Contact_Assignment_Flow`
subflow that takes firstName/lastName/email and returns a `contact` SObject, fed to the Pay
Button as `Contact_Assignment.Results.contact`. The shipped subflow only assembles an in-memory
Contact — **customize it for your org**: add find-or-create / duplicate-matching logic (Get
Records by email → Create if none) so you don't create duplicate Contacts on every donation.

**Handle the return trip with a Decision.** Declare a `status` input variable; the PSP redirect
returns to your SuccessURL/FailureURL carrying `?status=...`. A `Status_Decision` routes:
`success` → Success screen, `failure` → Failure screen, default → back to the payment screen.

**Multi-screen variant:** split amount, personal info, and payment onto separate screens and add
the unmanaged `c:experienceProgressStages` component at the top of each for a progress indicator.
Same component wiring; only the screen layout differs.

**Setup checklist (from the templates README):**
1. Deploy the flow templates + LWCs to the org.
2. Grant the site **Guest User** access to the flows (plus the FinDock permissions — see the public-site prerequisite above).
3. On the payment screen, open the **Payment Method Selector** and configure the methods/processors/targets to offer.
4. Set **SuccessURL/FailureURL** on the Pay Button to pages within your site.
5. Verify the variable mappings match your fields.
6. **Activate** the flow.
7. Enable API access (Experience Builder → Administration → Preferences) so guest users can call the Payment API.
8. Drop the flow onto an Experience Cloud page (it adopts the site theme).

Templates: `sfdx-source/packages/donation-fundraising/flows/` in
https://github.com/FinDockLabs/payment-experiences-templates (`Donation_Flow` multi-screen,
`One_Screen_Donation_Flow`, `Contact_Assignment`), with NPSP and UK Gift Aid variants in the
sibling `donation-npsp` and `donation-fundraising-uk` packages and a `Checkout_Flow` in `checkout`.

### Worked example — custom LWC assembling the managed components

Mirrors the FinDockLabs `customPayment` example. The custom LWC owns layout, validation, and
step navigation; the managed components own method selection and payment submission. A
`screenMode` design property switches between a single page (`OneScreen`) and a multi-step
wizard (`MultiScreen`).

```html
<!-- customPayment.html -->
<template>
  <!-- Step 1: Amount & Frequency (unmanaged component) -->
  <c-amount-and-frequency onamountfrequencychanged={handleAmountFrequencyChanged}>
  </c-amount-and-frequency>

  <!-- Step 2: Personal details (your own fields) -->
  <lightning-input type="text"  label="First Name" data-field="firstName" required
                   value={firstName} onchange={handleFieldChange}></lightning-input>
  <lightning-input type="text"  label="Last Name"  data-field="lastName"  required
                   value={lastName}  onchange={handleFieldChange}></lightning-input>
  <lightning-input type="email" label="Email"      data-field="email"     required
                   value={email}     onchange={handleFieldChange}></lightning-input>

  <!-- Step 3: Managed selector + managed pay button -->
  <cpm-payment-method-selector payment-method-config={paymentMethodConfig}
                               onpaymentmethodchanged={handlePaymentMethodChanged}>
  </cpm-payment-method-selector>
  <cpm-pay-button payment-intent={paymentIntent} disabled={isPayButtonDisabled}></cpm-pay-button>
</template>
```

```javascript
// customPayment.js (essentials)
import { api, LightningElement, track } from "lwc";
import { PAYMENT_METHOD_CONFIG } from "./customPaymentMethodConfiguration";

export default class CustomPayment extends LightningElement {
  @api screenMode = "OneScreen";        // design property: OneScreen | MultiScreen
  paymentMethodConfig = PAYMENT_METHOD_CONFIG;
  @track paymentIntent = {};
  // ...field + amount + selectedPaymentMethod state...

  handleAmountFrequencyChanged(e) { /* read e.detail.amountOneTime/amountRecurring/frequency */ this._rebuild(); }
  handleFieldChange(e)           { this[e.target.dataset.field] = e.detail.value; this._rebuild(); }
  handlePaymentMethodChanged(e)  { this.selectedPaymentMethod = e.detail; this._rebuild(); }

  _rebuild() {
    const isRecurring = this.frequency === "recurring";
    this.paymentIntent = {
      SuccessURL: ".../success", FailureURL: ".../failure",
      Payer: { Contact: { SalesforceFields: {
        FirstName: this.firstName, LastName: this.lastName, Email: this.email } } },
      ...(isRecurring
        ? { Recurring: { Amount: this.amountRecurring, CurrencyISOCode: "EUR" } }
        : { OneTime:   { Amount: this.amountOneTime,   CurrencyISOCode: "EUR" } }),
      PaymentMethod: {
        Name:      this.selectedPaymentMethod?.name,
        Processor: this.selectedPaymentMethod?.processor,   // omit to use org default
        Target:    this.selectedPaymentMethod?.target,      // omit to use org default
      },
    };
  }
}
```

Key points carried over from the example:
- You assemble the PaymentIntent yourself (reactively, on every input/selection change) and
  pass the **whole object** to `<cpm-pay-button>` via `payment-intent`; the button performs the
  on-platform `cpm.API_PaymentIntent_V2` call and PSP redirect — you do **not** call Apex.
- The selector's `paymentmethodchanged` `detail` (`name`, `processor`, `target`, parameters)
  slots straight into the PaymentIntent `PaymentMethod` block. `Processor`/`Target` are optional
  — omit to use the org default for that method.
- Gate the Pay Button with a `disabled` getter that checks required fields, a positive amount, a
  selected method, and `lightning-input` validity (`checkValidity()`), so the payer can't submit
  an incomplete intent.
- Expose the OneScreen/MultiScreen choice as a `screenMode` design property in the
  `.js-meta.xml` (`datasource="OneScreen, MultiScreen"`) so admins pick the layout per page.
- Standard FinDock UI rules still apply (selector row layout, enums with label+image, WCAG 2.2
  AA, responsive, field order) — the managed selector handles these for method/enum rows; you
  own them for your custom fields.

> **Note on Amount & Frequency.** The FinDockLabs example uses the **unmanaged**
> `c-amount-and-frequency` component. Because it's unmanaged (and therefore unsupported), prefer
> a managed alternative or your own simple amount/frequency inputs for production builds — the
> integration contract is just the three values (`amountOneTime`, `amountRecurring`,
> `frequency`) the `amountfrequencychanged` event carries, so any source that produces those
> works identically with the rest of this pattern.

## Route B — Custom LWC + Apex

Full custom build: your LWC renders the form and calls an `@AuraEnabled` Apex method that
invokes `cpm.API_PaymentIntent_V2.postPaymentIntent()` in-transaction. Use this when neither
the managed components nor Flow give you enough control. See `on-platform-apex-lwc-flow.md`
for the full Apex/LWC pattern. All FinDock UI rules (selector layout, enums with label+image,
WCAG 2.2 AA, responsive, field order) still apply.

---

## Calling FinDock — use Apex methods, never the REST endpoint

From Experience Cloud (and all on-platform code) you MUST call FinDock's managed Apex methods
directly, never the public REST endpoint (`/services/apexrest/cpm/v2/...`):
- `cpm.API_PaymentIntent_V2.postPaymentIntent()` — create/pay/update a payment
- `cpm.API_PaymentMethod_V2.getPaymentMethods()` — list active methods/processors

Both are **no-argument** static methods that read the JSON body from `RestContext.request` and write
to `RestContext.response` (`postPaymentIntent(String)` does not compile). The request/response shapes
match the REST API exactly; only the transport differs. The managed Pay Button handles this for you;
for custom LWC/Apex use the `FinDockGateway` RestContext-swap pattern in `on-platform-apex-lwc-flow.md`.

---

## Templates

FinDock provides Experience Cloud templates for donation and checkout pages, plus Flow
templates (single-step and multi-step), deployable from FinDock Labs:
https://github.com/FinDockLabs/payment-experiences-templates

---

---

## REQUIRED for public sites — ProcessingHub connected + guest user permission set

For any **public** (guest-user) Experience Cloud page, these prerequisites MUST be in place or the
payment will fail at runtime for unauthenticated payers:

1. **The FinDock | ProcessingHub must be installed AND connected.** Install it from **FinDock
   Setup**, then complete the connection step — installing alone is not enough. Connecting the
   ProcessingHub designates an **integration user** that the hub runs as. When a Site Guest User
   makes the Payment Intent call, FinDock hands the asynchronous part of processing to this
   ProcessingHub integration user (via a callout/callback) so processing is allowed to continue.
   Without ProcessingHub connected, guest-user payments cannot complete.
2. **The ProcessingHub integration user must have the FinDock Integration User permission set
   group assigned.** This is the user the ProcessingHub connects with; without this permission set
   group, the handed-off async processing is rejected and guest payments fail. (Setup → Users →
   [the integration user] → Permission Set Group Assignments → add **FinDock Integration User**.)
3. **The FinDock Payer permission set group must be assigned to the site's Guest User.** FinDock
   ships persona-based permission set **groups**; the Payer group bundles the two sets the payment
   experience needs — **FinDock Core Experience Cloud Run** and **FinDock Experience Cloud**
   (API name `proh__FinDock_Experience_Cloud`, from the ProcessingHub package), which grant access
   to `cpm.API_PaymentIntent_V2`. Assign the group, not the individual sets. (History: since the
   FinDock July '22 release the single FinDock Experience Cloud set was sufficient; the group is the
   current framework and stays correct as FinDock adds sets to it.)

   FinDock's *Getting started with Payment Experiences* also lists three Salesforce settings for
   guest access: **Flow access** (Setup → Flows → [flow] → Edit Access → override and enable the
   guest profile / permission set), **site access** (Experience Builder → Settings → General →
   guests can see and interact without logging in; Guest User Profile → Enabled Flow Access), and
   **API access** (Experience Builder → Administration → Preferences → *Allow guest users to
   access public APIs*).

**Always throw a warning when generating a public Experience Cloud / guest-user payment page**,
e.g.:

> ⚠️ Public site prerequisite: This page is for unauthenticated (guest) payers. For it to work,
> the **FinDock | ProcessingHub** must be installed *and connected* (from FinDock Setup), the
> **FinDock Integration User** permission set group must be assigned to the integration user the
> ProcessingHub is connected with, and the **FinDock Payer** permission set group must be assigned to
> the site's Guest User. Without all three, guest-user payments
> will fail. Private/authenticated pages do not require ProcessingHub for this reason, but still
> need the appropriate FinDock permissions.

This applies to both the managed Pay Button route and the custom LWC + Apex route whenever the
page is public.

---

## Security & permissions

- Payment Experiences runs entirely within Salesforce's enterprise security model and uses
  FinDock's existing permissions/compliance framework.
- The solution ships **dedicated permission sets** that must be assigned to user profiles for
  access to the managed LWCs. For a public site, assign the relevant set to the **Guest User**
  (standard Salesforce practice) so the Pay Button works for unauthenticated payers.
- PII captured through Payment Experiences is **not stored** by FinDock in any component,
  template, or external system.
- Experience Cloud specifics: needs Digital Experiences enabled and a site created; check user
  licenses (Customer Community (Plus) for B2C, Partner Community for B2B); SuccessURL/FailureURL
  should point to pages within the Experience Cloud site.

---

## Choosing a route (guidance for the intake)

- Low-code, admin will maintain it, standard donation/checkout -> **Route A + Flow builder**
  (use templates).
- Need custom UX but want managed payment plumbing -> **Route A + build in LWC** (embed
  `<cpm-payment-method-selector>` + `<cpm-pay-button>`; see the worked example above).
- Full control / complex interleaved logic -> **Route B (custom LWC + Apex)**.
