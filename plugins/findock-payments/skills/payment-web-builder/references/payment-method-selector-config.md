# Payment Method Selector — Component Config (DRAFT schema)

> ⚠️ **DRAFT / PROVISIONAL — to be finalized later.** This documents the *expected* shape of the
> FinDock Payment Method Selector component's configuration, based on an early example. The final
> field names and semantics may change. Always verify against the docs MCP
> (`https://docs.findock.com/mcp`) and the FinDockLabs templates before relying on it. When the
> final version is published, replace the example and field table below.

The Payment Method Selector component is configured with an array of payment-method entries (one
per method+processor the org wants to offer). At runtime the component renders these for the
payer to choose from, and its **output** is the selected payment method, processor, and target,
plus any parameters — ready to feed into the **Pay Button** (linked to its Payment Method
variable) or into a **PaymentIntent** sent to the Payment API directly.

## Config input (provisional example)

```json
[
  {
    "key": "PaymentHub-Stripe-CreditCard",
    "name": "CreditCard",
    "processor": "PaymentHub-Stripe",
    "processorPrettyName": "Stripe",
    "processorFriendlyName": "Stripe",
    "active": true,
    "supportsRecurring": true,
    "displayLabel": "Credit Card",
    "enabledOneTime": true,
    "isDefaultOneTime": true,
    "enabledRecurring": true,
    "isDefaultRecurring": true,
    "merchantAccount": "stripe_merchant_account",
    "merchantAccountGroup": "static",
    "redirectInstruction": "",
    "parameters": null
  },
  {
    "key": "PaymentHub-Stripe-iDEAL",
    "name": "iDEAL",
    "processor": "PaymentHub-Stripe",
    "processorPrettyName": "Stripe",
    "processorFriendlyName": "Stripe",
    "active": true,
    "supportsRecurring": false,
    "displayLabel": "iDEAL",
    "enabledOneTime": true,
    "isDefaultOneTime": false,
    "enabledRecurring": false,
    "isDefaultRecurring": false,
    "merchantAccount": "stripe_merchant_account",
    "merchantAccountGroup": "static",
    "redirectInstruction": "You will be redirected to your bank to complete the payment.",
    "parameters": null
  }
]
```

## Field reference (provisional)

| Field | Meaning |
|---|---|
| `key` | Unique identifier for the entry, conventionally `{processor}-{name}` (e.g. `PaymentHub-Stripe-CreditCard`) |
| `name` | FinDock payment method name (the API value, e.g. `CreditCard`, `iDEAL`) |
| `processor` | Processor/source-connector key (e.g. `PaymentHub-Stripe`) |
| `processorPrettyName` / `processorFriendlyName` | Human-readable processor names for display |
| `active` | Whether this method+processor is available at all |
| `supportsRecurring` | Whether the method can be used for recurring payments |
| `displayLabel` | The label shown to the payer in the selector (e.g. "Credit Card") |
| `enabledOneTime` | Offer this method for one-time payments |
| `isDefaultOneTime` | Pre-select this method for one-time payments |
| `enabledRecurring` | Offer this method for recurring payments |
| `isDefaultRecurring` | Pre-select this method for recurring payments |
| `merchantAccount` | The target merchant account to route through |
| `merchantAccountGroup` | How the merchant account is resolved (e.g. `static`) |
| `redirectInstruction` | Optional payer-facing copy shown when the method redirects (e.g. iDEAL → bank). Empty when no redirect |
| `parameters` | Method-specific parameters/enums (e.g. issuer); `null` when none |

## Output → Pay Button / Payment API

The component's output identifies the payer's choice and is used as input downstream:

- **payment method** (`name`), **processor**, and **target** (`merchantAccount` / merchant account group), plus any **parameters**
- Feed it into the **Pay Button** by linking the selector's output to the Pay Button's Payment
  Method variable, OR
- Map it into a **PaymentIntent** `PaymentMethod` block when calling
  `cpm.API_PaymentIntent_V2.postPaymentIntent()` (on-platform) or `POST /PaymentIntent`
  (external). The method name, processor/target, and parameters slot directly into the
  PaymentIntent contract (see `parameters-and-enums.md` and `one-time-payment.md`).

## How to use this today (mind the LWC gap)

- In a **Flow** (the currently supported builder for the selector): configure the component with
  this array, wire its output to the Pay Button. No custom code.
- In a **custom LWC** (selector not yet LWC-enabled — see `experience-cloud.md`): you currently
  build method selection yourself from `cpm.API_PaymentMethod_V2.getPaymentMethods()`. When the
  selector becomes LWC-enabled, this config schema is the expected interface — design your custom
  selector's data shape to be close to it so migration is easy.

## When finalizing

Replace the provisional example and field table with the published version, drop the DRAFT
banner, and reconcile any renamed fields. Keep the output→Pay Button / PaymentIntent mapping
section in sync with the parameters reference.
