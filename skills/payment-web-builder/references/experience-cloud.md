# Pattern 6 — Experience Cloud (FinDock Payment Experiences)

Use this when the deployment target from intake Question 2 is **Salesforce Experience Cloud**.

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

1. **Flow as the form builder** — drop the managed components into a Screen Flow. Best for
   low-code, admin-maintained journeys; supports single-step and multi-step forms, conditional
   logic, and validation. FinDock provides Flow templates (single-step and multi-step screen
   flows) deployable from FinDock Labs (https://github.com/FinDockLabs/experience-cloud-templates).
   Drop the Flow into an Experience Cloud page and it adopts the site theme.
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
> implementation is the `custom-lwc-implementation` path in the FinDockLabs templates repo
> (https://github.com/FinDockLabs/experience-cloud-templates). Re-check the docs MCP for the
> current pilot component names before finalizing.

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
- `cpm.API_PaymentIntent_V2.postPaymentIntent(request)` — create/pay/update a payment
- `cpm.API_PaymentMethod_V2.getPaymentMethods()` — list active methods/processors

The request/response shapes match the REST API exactly; only the transport differs. The managed
Pay Button handles this for you; for custom LWC/Apex you call it yourself.

---

## Templates

FinDock provides Experience Cloud templates for donation and checkout pages, plus Flow
templates (single-step and multi-step), deployable from FinDock Labs:
https://github.com/FinDockLabs/experience-cloud-templates

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
3. **The FinDock Experience Cloud permission set (included in the ProcessingHub package) must be
   assigned to the site's Guest User.** This grants the guest user access to
   `cpm.API_PaymentIntent_V2`. (Since the FinDock July '22 release, assigning this single
   permission set is all that's required for the guest user itself.)

**Always throw a warning when generating a public Experience Cloud / guest-user payment page**,
e.g.:

> ⚠️ Public site prerequisite: This page is for unauthenticated (guest) payers. For it to work,
> the **FinDock | ProcessingHub** must be installed *and connected* (from FinDock Setup), the
> **FinDock Integration User** permission set group must be assigned to the integration user the
> ProcessingHub is connected with, and the **FinDock Experience Cloud** permission set (included in
> that package) must be assigned to the site's Guest User. Without all three, guest-user payments
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
