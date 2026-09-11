# Pattern 7 — On-Platform: Apex, LWC & Flow

Use this when the integration runs **inside Salesforce** rather than as an external website
calling the REST API. Covers three surfaces that share one integration model: Apex (the
server-side core), LWC (UI on top of Apex), and Flow (admin-friendly, via an invocable Apex
action). Applies to Experience Cloud sites and internal Lightning pages alike.

> **Always verify against the docs MCP first.** Before writing Apex, query
> `https://docs.findock.com/mcp` and check the FinDockLabs example repo
> (https://github.com/FinDockLabs/findock-experience-cloud-examples) for the current class
> method signatures and object shapes. The class name and overall pattern below are confirmed
> from FinDock docs, but exact method names/signatures are demonstrated in the repo and can
> evolve — do not invent signatures.

---

## The core difference vs. the REST patterns

| | REST (Patterns 1–6) | On-platform (this pattern) |
|---|---|---|
| Transport | HTTPS to `/services/apexrest/cpm/v2/PaymentIntent` | Direct Apex call, same transaction |
| Auth | OAuth2 Bearer token + proxy | None — runs as the Salesforce/guest user |
| CORS | Required for browser calls | Not applicable |
| Credentials tooling | `setup.mjs` / `doctor` (Step 6) | Not needed — skip Step 6 |
| Entry point | REST resource | Apex class `cpm.API_PaymentIntent_V2` |

Because there's no token or proxy, **the entire authentication reference and credentials
setup do not apply** to on-platform builds. The trade-off: the code only runs inside
Salesforce (LWC, Aura, Flow, Visualforce, triggers, batch).

Everything *else* the skill encodes still applies to the UI layer: the canonical flow,
payment-methods catalogue, enum/parameter rendering (label + image), accessibility (WCAG 2.2
AA), responsive/mobile rules, field order, and the radio-first selector layout.

---

## Apex — the server-side core

The Apex entry points are **static methods** on FinDock's managed global classes. You build
the same request you would send over REST and pass it to the Apex method in-transaction; the
response mirrors the REST response (including `RedirectURL`).

| Purpose | REST endpoint (external only) | Apex method (on-platform) |
|---|---|---|
| Create/pay/update a payment | `POST /PaymentIntent` | `cpm.API_PaymentIntent_V2.postPaymentIntent()` — no arguments, reads/writes `RestContext` |
| List active methods/processors | `GET /PaymentMethods` | `cpm.API_PaymentMethod_V2.getPaymentMethods()` — no arguments, reads/writes `RestContext` |

> **Critical (Experience Cloud and all on-platform code): do NOT call the public REST
> endpoint.** From within Salesforce — Experience Cloud LWC, internal Lightning, Flow, Apex —
> you cannot use `/services/apexrest/cpm/v2/...` (it would require an outbound authenticated
> callout back into the same org, which is blocked / nonsensical and breaks for guest users).
> Call the underlying Apex methods directly instead: `cpm.API_PaymentIntent_V2.postPaymentIntent()`
> and `cpm.API_PaymentMethod_V2.getPaymentMethods()`. The REST API is only for **external**
> (non-Salesforce) clients.

> **Signature — verified in an org (FinDockLabs `findock-multi-framework-react` and
> `findock-experience-cloud-examples`).** Both managed entry points are **no-argument** static methods
> on `@RestResource` classes: they read the JSON body from `RestContext.request` and write the
> response to `RestContext.response`. `postPaymentIntent(String)` does **not compile**. From any Apex
> (an `@AuraEnabled` controller, an invocable action, or your own `@RestResource`) you therefore
> swap in a fresh `RestRequest` / `RestResponse`, call the method, read the response, and restore the
> original context in `finally`. Wrap that once in a gateway class and reuse it everywhere.

```apex
// FinDockGateway.cls — FinDock: single place that talks to the managed classes, in-transaction.
public with sharing class FinDockGateway {

    public class Result {
        public Integer statusCode; public String body;
        public Boolean isSuccess() { return statusCode != null && statusCode >= 200 && statusCode < 300; }
    }

    // FinDock: equivalent of POST /PaymentIntent — body is the PaymentIntent JSON from the REST docs
    public static Result postPaymentIntent(String paymentIntentJson) {
        RestRequest req = new RestRequest();
        req.requestURI = URL.getOrgDomainUrl().toExternalForm() + '/services/apexrest/cpm/v2/PaymentIntent';
        req.httpMethod = 'POST';
        req.addHeader('Content-Type', 'application/json');
        req.requestBody = Blob.valueOf(paymentIntentJson);
        return invoke(req, true);
    }

    // FinDock: equivalent of GET /PaymentMethods — same payload (methods, processors, parameters, enums+images)
    public static Result getPaymentMethods() {
        RestRequest req = new RestRequest();
        req.requestURI = URL.getOrgDomainUrl().toExternalForm() + '/services/apexrest/cpm/v2/PaymentMethods';
        req.httpMethod = 'GET';
        return invoke(req, false);
    }

    private static Result invoke(RestRequest req, Boolean isPost) {
        RestRequest originalRequest = RestContext.request;     // may be null outside a REST call — that is fine
        RestResponse originalResponse = RestContext.response;
        RestResponse res = new RestResponse();
        try {
            RestContext.request = req;
            RestContext.response = res;
            if (isPost) { cpm.API_PaymentIntent_V2.postPaymentIntent(); }   // FinDock: no arguments
            else        { cpm.API_PaymentMethod_V2.getPaymentMethods(); }   // FinDock: no arguments
        } finally {
            RestContext.request = originalRequest;
            RestContext.response = originalResponse;
        }
        Result r = new Result();
        r.statusCode = res.statusCode == null ? 200 : res.statusCode;
        r.body = res.responseBody == null ? '' : res.responseBody.toString();
        return r;
    }
}
```

The LWC-facing controller then stays thin:

```apex
public with sharing class FinDockPaymentController {

    // FinDock: @AuraEnabled so LWC/Aura can call it directly (NOT reachable from React UI bundles —
    // those need an @RestResource; see salesforce-multi-framework.md)
    @AuraEnabled
    public static String submitPayment(String payloadJson) {
        // FinDock: the PaymentIntent JSON built by the front-end matches the REST body exactly.
        FinDockGateway.Result r = FinDockGateway.postPaymentIntent(payloadJson);
        // Return the serialized response (RedirectURL, Id, Errors[]) to the caller; the LWC routes on it.
        return r.body;
    }

    @AuraEnabled(cacheable=true)
    public static String getPaymentMethods() {
        // FinDock: do NOT fetch GET /PaymentMethods over REST from Experience Cloud — call in-transaction.
        return FinDockGateway.getPaymentMethods().body;
    }
}
```

Testing: make the gateway swappable (interface + `@TestVisible` static) so unit tests stub FinDock
and never contact a PSP; cover the real gateway with one test that calls the managed methods with an
empty body and asserts `RestContext` is restored.

Guest-user note (public Experience Cloud pages) — REQUIRED, warn the user: for public pages the
**FinDock | ProcessingHub must be installed AND connected** (from FinDock Setup), the **FinDock
Integration User** permission set group must be assigned to the integration user the ProcessingHub
is connected with, AND the **FinDock Payer** permission set group (bundles FinDock Core Experience
Cloud Run + FinDock Experience Cloud) must be assigned to the site's guest user. When a guest user calls the Payment Intent, FinDock
hands async processing to the ProcessingHub integration user, so without a connected ProcessingHub
whose integration user has the FinDock Integration User permission set group, guest payments fail.
(The Payer group is what grants the guest user's own access to `cpm.API_PaymentIntent_V2`.) See `experience-cloud.md` for the full
warning.

---

## LWC — UI calling the Pay Button (no custom Apex)

### FinDockLabs `c-payment-form` — drop-in replacement for a Screen Flow

The `paymentForm` component from the FinDockLabs
[`experience-cloud-lwc`](https://github.com/FinDockLabs/experience-cloud-lwc) repo is a
complete, configurable payment form that replaces a Screen Flow. It uses `c-payment-selector`
and `cpm-pay-button` internally — **no custom Apex controller needed**; the managed `cpm-pay-button`
calls `cpm.API_PaymentIntent_V2.postPaymentIntent()` on the way to the PSP redirect.

Use `c-payment-form` when:
- You want a fully code-controlled form with more UI flexibility than a Screen Flow.
- You need a drop-in component in Experience Builder or App Builder with no Flow configuration.
- The built-in three-step structure (Amount, Personal Info, Payment Method) fits the use case.

**Do not** use it when you need a non-standard form layout or when you must call a custom Apex
action before or after payment — in those cases build your own LWC + Apex (see below).

#### API properties (configurable in Experience Builder)

| Property | Type | Default | Description |
|---|---|---|---|
| `screenMode` | String | `'OneScreen'` | `'OneScreen'` — all steps on one page; `'MultiScreen'` — three separate steps with Back/Next navigation |
| `currency` | String | `'EUR'` | ISO currency code shown in the amount picker (e.g. `EUR`, `USD`, `GBP`) |
| `hideFrequency` | Boolean | `false` | Hide the one-time / recurring toggle |
| `defaultFrequency` | String | `'oneTime'` | Pre-selected frequency on load: `'oneTime'` or `'recurring'` |
| `recordId` | String | — | Salesforce record ID passed from the page context |

The "recurring" toggle option covers a fixed monthly plan today — there's no separate cadence
picker, so the component always sends `Recurring.Frequency: 'Monthly'`. Add a configurable
frequency property if another cadence needs to be covered later.

#### Targets (exposed in Experience Builder / App Builder)

```xml
<targets>
    <target>lightning__RecordPage</target>
    <target>lightning__HomePage</target>
    <target>lightningCommunity__Page</target>
    <target>lightningCommunity__Default</target>
</targets>
```

#### Form structure

The component renders three sections (always visible in OneScreen, step-by-step in MultiScreen):

1. **Amount & Frequency** — `c-amount-and-frequency` component; fires `amountfrequencychange`
2. **Personal Information** — First Name, Last Name, Email (`lightning-input`, all required)
3. **Payment Method & Pay Button** — `c-payment-selector` + `cpm-pay-button`

In MultiScreen mode a `c-experience-progress-stages` indicator shows the current step, and
`aria-live` announcements are made on step transitions (WCAG 4.1.3).

#### Payment method configuration

Payment methods are defined in a sibling `paymentMethodConfiguration.js` file imported at the JS
level — no Apex call to `GET /PaymentMethods` at runtime. Edit this file to match the payment
methods and processors active in the org. See `payment-method-selector-config.md` for the flat
config schema and the Apex script to generate it from the org.

```javascript
// paymentMethodConfiguration.js
export const PAYMENT_METHOD_CONFIG = [
    {
        paymentMethod: 'CreditCard',
        paymentProcessor: 'PaymentHub-Stripe',
        target: 'Stripe-Main-Account',
        enabledOneTime: true,
        enabledRecurring: true,
        isDefaultOneTime: true,
        isDefaultRecurring: false,
        supportsRecurring: true,
        displayLabel: 'Credit Card'
    },
    {
        paymentMethod: 'Ideal',
        paymentProcessor: 'PaymentHub-Stripe',
        target: 'Stripe-Main-Account',
        enabledOneTime: true,
        enabledRecurring: false,
        isDefaultOneTime: false,
        isDefaultRecurring: false,
        supportsRecurring: false,
        displayLabel: 'iDEAL',
        redirectInstruction: 'You will be redirected to your bank to complete the payment.'
    }
];
```

#### PaymentIntent built by the component

`paymentForm` builds the intent internally from form state and passes it to `cpm-pay-button`:

```javascript
{
    SuccessURL: 'https://example.com/success',
    FailureURL:  'https://example.com/failure',
    Payer: { Contact: { SalesforceFields: { FirstName, LastName, Email } } },
    // one of:
    OneTime:   { Amount: amountOneTime,   CurrencyISOCode: currency },
    Recurring: { Amount: amountRecurring, CurrencyISOCode: currency, Frequency: 'Monthly', StartDate: todayISODate() },
    PaymentMethod: {
        Name:      selectedPaymentMethod.name,
        Processor: selectedPaymentMethod.processor,
        Target:    selectedPaymentMethod.target
    }
}
```

`Recurring.Frequency` and `Recurring.StartDate` (`yyyy-mm-dd`) are both required by the Payment
API for recurring requests (see `recurring-payment.md`) — omitting either returns a 422 `Missing
Frequency value` / `Missing Start Date value` error even when the payer picked "recurring" on the
toggle, since the toggle only chooses one-time vs. recurring, not the cadence or start date. With
no date picker on the form, `StartDate` defaults to today in the payer's local time.

Customize `SuccessURL`/`FailureURL` and add additional `Payer` fields or `Recurring` schedule
fields by forking the component.

The Pay Button is disabled until all required fields are filled and a payment method is selected.

---

## LWC — UI calling Apex (custom controller approach)

Use this approach when `c-payment-form` doesn't fit — for example, when you need pre/post-payment
Apex logic, a non-standard form layout, or fine-grained control over the PaymentIntent shape.

The LWC renders the form (applying all the skill's UI rules) and calls the `@AuraEnabled`
Apex method via an imported method — no `fetch`, no proxy.

```javascript
// paymentForm.js
import { LightningElement, track } from 'lwc';
// FinDock: import the Apex method — Salesforce handles auth via the session automatically
// FinDock: the Apex method wraps cpm.API_PaymentIntent_V2.postPaymentIntent — NOT a REST call
import submitPayment from '@salesforce/apex/FinDockPaymentController.submitPayment';

export default class PaymentForm extends LightningElement {
    @track amount = 25;
    @track method = 'Ideal';

    async handleSubmit() {
        // FinDock: build the same PaymentIntent payload shape as the REST patterns
        const payload = {
            SuccessURL: window.location.origin + '/thank-you',
            FailureURL: window.location.origin + '/payment-failed',
            Payer: { Contact: { SalesforceFields: {
                FirstName: this.firstName, LastName: this.lastName, Email: this.email
            } } },
            OneTime: { Amount: this.amount },
            // FinDock: Processor omitted → org default is used (only set to override)
            PaymentMethod: { Name: this.method }
        };

        try {
            // FinDock: call Apex; result is the serialized API response
            const responseJson = await submitPayment({ payloadJson: JSON.stringify(payload) });
            const result = JSON.parse(responseJson);

            // FinDock: redirect to the PSP (Apex returns the same RedirectURL as REST)
            if (result.RedirectURL) {
                window.location.href = result.RedirectURL;
            }
        } catch (e) {
            // Apex errors surface as e.body.message
            this.error = e.body?.message ?? 'Payment could not be started.';
        }
    }
}
```

`paymentForm.js-meta.xml` — expose to Experience Builder / Lightning App Builder:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
  <apiVersion>63.0</apiVersion>
  <isExposed>true</isExposed>
  <targets>
    <target>lightningCommunity__Page</target>
    <target>lightning__AppPage</target>
    <target>lightning__RecordPage</target>
  </targets>
</LightningComponentBundle>
```

> All UI rules still apply: render payment methods from the response with the radio-first
> layout (radio → icon → label), use enum `label`+`image.svg`, meet WCAG 2.2 AA, be responsive.
> For Experience Cloud specifically, also see `experience-cloud.md` (native LWC components are
> coming soon and may replace hand-rolled components).

---

## Flow — admin-friendly

> **Consider `c-payment-form` first.** The FinDockLabs `paymentForm` LWC is a drop-in
> replacement for a Screen Flow that gives developers full code control without any Flow
> configuration. See the [LWC section above](#lwc--ui-calling-the-pay-button-no-custom-apex).
> Use a Flow when an admin-friendly, no-code configuration is the priority.

There are two ways to call FinDock from Flow. **Prefer the managed screen components** when they
fit:

- **Managed Pay Button + Payment Method Selector (no custom Apex) — preferred for Experience
  Cloud / Payment Experiences.** Drop `cpm:paymentMethodSelector` and `cpm:payButton` into a
  Screen Flow; the Pay Button builds and submits the PaymentIntent and handles the PSP redirect
  for you. This is the FinDockLabs template approach — see the **Flow worked example** in
  `experience-cloud.md` (screen order, the selector's `frequency` input, the Contact subflow,
  amount-routing formulas, status-based decision routing). No invocable Apex required.
- **Invocable Apex action (below) — use when the managed components aren't available or don't
  fit:** internal/non-Experience-Cloud flows, orgs not in the Payment Experiences pilot, or when
  you need full control over how the PaymentIntent is assembled.

### Invocable Apex action

Flow can't build the nested PaymentIntent object directly (Invocable Variables don't support
inner classes or maps), so you wrap the call in an `@InvocableMethod` that accepts flat inputs
and assembles the PaymentIntent in Apex.

```apex
public with sharing class FinDockSubmitPaymentInvocable {

    public class FlowInput {
        @InvocableVariable(required=true) public Decimal amount;
        @InvocableVariable(required=true) public String paymentMethod;
        @InvocableVariable(required=true) public String firstName;
        @InvocableVariable(required=true) public String lastName;
        @InvocableVariable(required=true) public String email;
        @InvocableVariable public String successUrl;
        @InvocableVariable public String failureUrl;
    }

    public class FlowOutput {
        @InvocableVariable public String redirectUrl;
        @InvocableVariable public String responseJson;
    }

    // FinDock: flat Flow inputs → PaymentIntent → API call → flat outputs back to Flow
    @InvocableMethod(label='FinDock Submit Payment'
        description='Creates a payment with FinDock from Flow inputs')
    public static List<FlowOutput> submit(List<FlowInput> inputs) {
        List<FlowOutput> outputs = new List<FlowOutput>();
        for (FlowInput in : inputs) {
            // Build the PaymentIntent JSON (same shape as REST) from the flat inputs
            Map<String, Object> payload = new Map<String, Object>{
                'SuccessURL' => in.successUrl,
                'FailureURL' => in.failureUrl,
                'Payer' => new Map<String, Object>{
                    'Contact' => new Map<String, Object>{
                        'SalesforceFields' => new Map<String, Object>{
                            'FirstName' => in.firstName,
                            'LastName'  => in.lastName,
                            'Email'     => in.email
                        }
                    }
                },
                'OneTime' => new Map<String, Object>{ 'Amount' => in.amount },
                'PaymentMethod' => new Map<String, Object>{ 'Name' => in.paymentMethod }
            };

            // FinDock: submit via the gateway (RestContext swap around the no-arg managed method,
            // see the Apex section above) — never the public REST endpoint
            String responseJson = FinDockGateway.postPaymentIntent(JSON.serialize(payload)).body;

            Map<String, Object> resp =
                (Map<String, Object>) JSON.deserializeUntyped(responseJson);

            FlowOutput out = new FlowOutput();
            out.responseJson = responseJson;
            out.redirectUrl  = (String) resp.get('RedirectURL');
            outputs.add(out);
        }
        return outputs;
    }
}
```

In Flow: collect inputs on a Screen, call this Apex Action, then use the returned
`redirectUrl` (e.g. in a post-Flow navigation or an Aura wrapper for Experience Cloud).
The FinDockLabs repo includes a ready-made Flow + Aura wrapper for exactly this.

---

## Testing

- Apex unit tests: mock the response shape; don't make live PSP calls in tests.
- Use Salesforce Workbench to simulate an authenticated PaymentIntent call quickly while
  debugging configuration (per FinDock's troubleshooting guide).

## Resources (verify current versions via the docs MCP)

- Apex / Experience Cloud integration: https://docs.findock.com/api/integrating-with-experience-cloud
- Example repo (Apex, LWC, Flow, Aura): https://github.com/FinDockLabs/findock-experience-cloud-examples
- Blog part 1 (LWC + Apex) and part 2 (Flow): linked from the integration doc above
