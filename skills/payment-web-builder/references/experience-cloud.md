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

FinDock provides **managed Lightning Web Components** for use in Flows or your own components:

- **FinDock Payment Method Selector** (managed LWC): visual configuration of payment methods,
  processors, target merchant accounts, and parameters. When shown to the payer it displays
  the enabled methods (and any configured parameters) for selection. Familiar to anyone who
  has used Giving Pages payment method configuration.
  Its config shape and output (selected method + processor + target + parameters, used as input
  for the Pay Button or a PaymentIntent) are documented in
  `references/payment-method-selector-config.md` (DRAFT schema — to be finalized).
- **FinDock Pay Button** (managed LWC): a single-button step that builds the PaymentIntent
  (via a visual configuration editor mapping Flow variables -> PaymentIntent, with support for
  dynamic logic, variables, and static values) and initiates payment on click, redirecting to
  the PSP when confirmation is required. If using the Payment Method Selector, link its output
  to the Pay Button's Payment Method variable.
- **Amount & Frequency selector** (UNMANAGED component): provided as part of the starter
  templates for one-time and recurring donations. Because it's unmanaged, you can use and
  extend it in any environment.

Within Route A there are **two ways to assemble the form** (intake sub-question):

1. **Flow as the form builder** — drop the managed components into a Screen Flow. Best for
   low-code, admin-maintained journeys; supports single-step and multi-step forms, conditional
   logic, and validation. FinDock provides Flow templates (single-step and multi-step screen
   flows) deployable from FinDock Labs (https://github.com/FinDockLabs/experience-cloud-templates).
   Drop the Flow into an Experience Cloud page and it adopts the site theme.
2. **Build the whole form in LWC** — embed the managed components directly inside your own
   custom LWC. Best when you need UX the Flow screen can't express, while still avoiding
   hand-rolled PaymentIntent logic.

> **IMPORTANT — Payment Method Selector is not yet LWC-enabled.** At time of writing the
> Payment Method Selector component is only available for the Flow builder; it is NOT yet
> usable as a standalone LWC you can embed in a custom LWC. So if the user chooses
> "build the whole form in LWC" and needs method selection, the method selector currently
> requires **custom development** (render methods from `cpm.API_PaymentMethod_V2.getPaymentMethods()`
> yourself, following the parameters-and-enums reference). The Pay Button and the unmanaged
> Amount & Frequency selector can be used in custom LWC today. Re-check the docs MCP — this
> gap is expected to close.

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

## REQUIRED for public sites — ProcessingHub package + guest user permission set

For any **public** (guest-user) Experience Cloud page, two prerequisites MUST be in place or the
payment will fail at runtime for unauthenticated payers:

1. **The FinDock | ProcessingHub package must be installed.** Install it from **FinDock Setup**.
   When a Site Guest User makes the Payment Intent call, FinDock hands the asynchronous part of
   processing to the ProcessingHub integration user (via a callout/callback) so processing is
   allowed to continue. Without ProcessingHub connected, guest-user payments cannot complete.
2. **The FinDock Experience Cloud permission set (included in the ProcessingHub package) must be
   assigned to the site's Guest User.** This grants the guest user access to
   `cpm.API_PaymentIntent_V2`. (Since the FinDock July '22 release, assigning this single
   permission set is all that's required.)

**Always throw a warning when generating a public Experience Cloud / guest-user payment page**,
e.g.:

> ⚠️ Public site prerequisite: This page is for unauthenticated (guest) payers. For it to work,
> the **FinDock | ProcessingHub** package must be installed (from FinDock Setup) and the
> **FinDock Experience Cloud** permission set (included in that package) must be assigned to the
> site's Guest User. Without both, guest-user payments will fail. Private/authenticated pages do
> not require ProcessingHub for this reason, but still need the appropriate FinDock permissions.

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
- Need custom UX but want managed payment plumbing -> **Route A + build in LWC** (mind the
  Payment Method Selector gap above).
- Full control / complex interleaved logic -> **Route B (custom LWC + Apex)**.
