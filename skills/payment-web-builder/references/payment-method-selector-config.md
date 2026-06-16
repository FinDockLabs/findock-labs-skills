# Payment Method Selector — Component Config (pilot schema)

> ⚠️ **Pilot — verify before relying on it.** This schema is confirmed against the FinDockLabs
> `custom-lwc-implementation` example (https://github.com/FinDockLabs/experience-cloud-templates),
> but FinDock Payment Experiences is still in a closed pilot, so field names and semantics can
> change. Always cross-check the docs MCP (`https://docs.findock.com/mcp`) and the latest
> FinDockLabs templates before finalizing.

The Payment Method Selector component is configured with an array of payment-method entries (one
per method+processor the org wants to offer). At runtime the component renders these for the
payer to choose from, and its **output** is the selected payment method, processor, and target,
plus any parameters — ready to feed into the **Pay Button** or into a **PaymentIntent** sent to
the Payment API directly.

## Runtime interface (embedding in a custom LWC)

The selector is now usable as a custom-element tag inside your own LWC (it is no longer
Flow-only):

```html
<cpm-payment-method-selector
    payment-method-config={paymentMethodConfig}
    onpaymentmethodchanged={handlePaymentMethodChanged}>
</cpm-payment-method-selector>
```

- **Property `payment-method-config`** — the array of entries below (typically imported from a
  sibling config module, e.g. `customPaymentMethodConfiguration.js`).
- **Event `paymentmethodchanged`** — fired when the payer picks a method. `event.detail` is the
  chosen entry (at least `name`, `processor`, `target`, plus any selected parameter values),
  which slots straight into the PaymentIntent `PaymentMethod` block. Omit `Processor`/`Target`
  in the PaymentIntent to fall back to the org default.

Pair it with `<cpm-pay-button payment-intent={paymentIntent} disabled={...}>`: build the
PaymentIntent from the selection (and your other fields) and hand the whole object to the Pay
Button, which performs the on-platform `cpm.API_PaymentIntent_V2` call and PSP redirect. See the
worked example in `experience-cloud.md`.

## Config input (example, confirmed against FinDockLabs templates)

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
    "merchantAccount": "TestMerchant1",
    "merchantAccountGroup": "static",
    "redirectInstruction": "You will be redirected to your bank to complete the payment.",
    "target": "TestMerchant1",
    "parameters": [
      {
        "name": "description",
        "data_type": "String",
        "required": false,
        "description": "Description of the payment for the payer's bank.",
        "visibleToCustomer": false,
        "displayLabel": "Description",
        "value": "This is a description"
      }
    ]
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
    "merchantAccount": "TestMerchant1",
    "merchantAccountGroup": "static",
    "redirectInstruction": "You will be redirected to your bank to complete the payment.",
    "target": "TestMerchant1",
    "parameters": null
  }
]
```

## Parameter object schema (per entry's `parameters` array)

`parameters` is optional per entry: `null` (or omitted) when the method needs no extra inputs,
otherwise an array of parameter objects:

| Field | Meaning |
|---|---|
| `name` | The parameter key the processor expects (e.g. `issuer`, `brand`, `description`) |
| `data_type` | Value type: `String`, `Enum`, `Boolean`, or `Number` |
| `required` | Whether the processor requires the parameter |
| `visibleToCustomer` | `true` → rendered as an input in the form for the payer to supply; `false` → set programmatically before submission |
| `description` | Human-readable explanation of what the parameter controls |
| `displayLabel` | Label shown to the payer when `visibleToCustomer` is true (falls back to `name`) |
| `value` | Optional pre-set/default value (matches `data_type`); useful when `visibleToCustomer` is false |
| `enum` | (Enum only) allowed option objects `{ value, label, image?: { svg } }` — render the row as radio + image + label, submit `value`. See `parameters-and-enums.md` |
| `literals` | (Enum only) flat list of the allowed `value`s, for quick client-side validation |

Example — an Enum parameter (iDEAL bank picker):

```json
"parameters": [
  {
    "name": "issuer",
    "data_type": "Enum",
    "required": false,
    "description": "The issuing bank. Skips the bank-selection screen and redirects straight to the bank.",
    "enum": [
      { "value": "abnamro", "label": "ABN AMRO", "image": { "svg": "https://external.findock.com/icon/payment-methods/ideal/abnamro.svg" } },
      { "value": "ing",     "label": "ING",      "image": { "svg": "https://external.findock.com/icon/payment-methods/ideal/ing.svg" } }
    ],
    "literals": ["abnamro", "ing"]
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
| `merchantAccount` | The merchant account to route through |
| `merchantAccountGroup` | How the merchant account is resolved (e.g. `static`) |
| `target` | The target merchant account submitted in the PaymentIntent `PaymentMethod.Target` (omit in the intent to use the org default) |
| `redirectInstruction` | Optional payer-facing copy shown when the method redirects (e.g. iDEAL → bank). Empty when no redirect |
| `parameters` | Method-specific parameters/enums (e.g. issuer); `null` when none. See the parameter object schema above |

## Output → Pay Button / Payment API

The component's output identifies the payer's choice and is used as input downstream:

- **payment method** (`name`), **processor**, and **target** (`merchantAccount` / merchant account group), plus any **parameters**
- Feed it into the **Pay Button** by linking the selector's output to the Pay Button's Payment
  Method variable, OR
- Map it into a **PaymentIntent** `PaymentMethod` block when calling
  `cpm.API_PaymentIntent_V2.postPaymentIntent()` (on-platform) or `POST /PaymentIntent`
  (external). The method name, processor/target, and parameters slot directly into the
  PaymentIntent contract (see `parameters-and-enums.md` and `one-time-payment.md`).

## How to use this

- In a **Flow**: configure the component with this array, wire its output to the Pay Button. No
  custom code.
- In a **custom LWC**: import the array (e.g. from `customPaymentMethodConfiguration.js`), pass
  it as `payment-method-config` to `<cpm-payment-method-selector>`, and handle
  `paymentmethodchanged` to build the PaymentIntent you hand to `<cpm-pay-button>`. See the
  worked example in `experience-cloud.md`.

## When finalizing

Keep the example, field table, and runtime interface in sync with the published pilot schema and
the FinDockLabs templates; reconcile any renamed fields and drop the pilot banner once GA. Keep
the parameter object schema aligned with `parameters-and-enums.md`.
