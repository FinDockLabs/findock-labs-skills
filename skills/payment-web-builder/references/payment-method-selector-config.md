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

### Option A — FinDockLabs `c-payment-selector` wrapper (recommended for custom LWC forms)

The FinDockLabs [`experience-cloud-lwc`](https://github.com/FinDockLabs/experience-cloud-lwc) repo
ships a `paymentSelector` component (`<c-payment-selector>`) that wraps `cpm-payment-method-selector`
and accepts a **simplified flat config** — fewer fields, no manual `key` generation, string or
array input. Use this when building your own LWC form.

```html
<c-payment-selector
    config={paymentMethodConfig}
    frequency={frequency}
    onpaymentmethodchanged={handlePaymentMethodChanged}>
</c-payment-selector>
```

- **`config`** — the simplified flat array (or its JSON string). See
  [Simplified config schema](#simplified-config-schema-c-payment-selector) below.
- **`frequency`** — `'onetime'` or `'recurring'` (case-insensitive). Controls which methods
  are shown based on `enabledOneTime` / `enabledRecurring`. Default: `'onetime'`.
- **`paymentIntentResponse`** — optional; pass the response from `cpm-pay-button` back to the
  selector (for post-payment state).
- **Event `paymentmethodchanged`** — bubbles and is composed, so it propagates through shadow
  DOM. `event.detail` is the enriched entry (`name`, `processor`, `target`, `parameters`, …),
  ready to slot into the `PaymentMethod` block of a `paymentIntent`.

Pair it with `<cpm-pay-button payment-intent={paymentIntent} disabled={...}>`: build the
`paymentIntent` object from the selection and other form fields, then pass it to the Pay Button.
The Pay Button calls `cpm.API_PaymentIntent_V2.postPaymentIntent()` and handles the PSP redirect —
no custom Apex needed. See `on-platform-apex-lwc-flow.md` for the `c-payment-form` worked example.

### Option B — `cpm-payment-method-selector` directly (managed component, full config schema)

Use the managed component directly when you need full control over the config shape, or when
using the selector outside the FinDockLabs component stack:

```html
<cpm-payment-method-selector
    payment-method-config={paymentMethodConfig}
    onpaymentmethodchanged={handlePaymentMethodChanged}>
</cpm-payment-method-selector>
```

- **Property `payment-method-config`** — the full-schema array (see
  [Config input](#config-input-example-confirmed-against-findocklabs-templates) below).
- **Event `paymentmethodchanged`** — `event.detail` is the chosen entry.

---

## Simplified config schema (`c-payment-selector`)

The `c-payment-selector` wrapper accepts a **flat array** with different field names from the
full `cpm-payment-method-selector` schema. The wrapper enriches it internally (generates `key`,
maps `paymentMethod` → `name`, `paymentProcessor` → `processor`, etc.) before passing it down.

### Flat config example

```javascript
// paymentMethodConfiguration.js — define once, import where needed
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
        displayLabel: 'Credit Card',
        parameters: [
            {
                name: 'description',
                value: '',
                visibleToCustomer: true,
                displayLabel: "Description for the payer's bank",
                required: false,
                data_type: 'String',
                description: "Description of the payment for the payer's bank."
            }
        ]
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

### Flat config field reference

| Field | Meaning |
|---|---|
| `paymentMethod` | FinDock payment method name (maps to `name` / `PaymentMethod.Name`). Source: `PaymentMethods[].Name` from `GET /PaymentMethods`. Example: `CreditCard` |
| `paymentProcessor` | Processor key (maps to `processor` / `PaymentMethod.Processor`). Source: `PaymentMethods[].Processors[].Name`. Example: `PaymentHub-Stripe` |
| `target` | Merchant account (maps to `PaymentMethod.Target`). Native processors: returned in `Targets[]` from `GET /PaymentMethods`. PSPs (e.g. PaymentHub-Stripe): FinDock Setup → Processors & Methods → processor → Accounts tab → Merchant Account Name. |
| `enabledOneTime` | Offer this method for one-time payments |
| `enabledRecurring` | Offer this method for recurring payments. Must be `false` if `supportsRecurring` is `false` |
| `isDefaultOneTime` | Pre-select for one-time. Exactly one entry should be `true` |
| `isDefaultRecurring` | Pre-select for recurring. Exactly one `enabledRecurring: true` entry should be `true` |
| `supportsRecurring` | Whether the processor supports recurring for this method. Source: `SupportsRecurring` from `GET /PaymentMethods`. Defaults to `enabledRecurring` when omitted |
| `displayLabel` | Payer-facing label. Defaults to `paymentMethod` when omitted |
| `redirectInstruction` | Shown before PSP redirect (e.g. iDEAL). Omit when no redirect |
| `parameters` | Method-specific parameters. `null` / omit when none. See parameter fields below |

### Flat parameter fields

| Field | Meaning |
|---|---|
| `name` | Parameter key (maps to `PaymentMethod.Parameters[name]`). Source: `Parameters[].Name` from `GET /PaymentMethods` |
| `value` | Value sent to the processor. Leave empty for payer-filled fields |
| `visibleToCustomer` | `true` → render as an input for the payer; `false` → send silently (default) |
| `displayLabel` | Label shown to the payer when `visibleToCustomer` is `true`. Defaults to `name` |
| `required` | Whether the processor requires this parameter |
| `data_type` | `String`, `Enum`, `Boolean`, or `Number` |
| `description` | Human-readable explanation of the parameter |

> **Enum parameters** (`data_type: 'Enum'`) are not supported in the simplified flat schema — use
> the full `cpm-payment-method-selector` schema (Option B) for enum bank-picker parameters (e.g.
> iDEAL issuer). See `parameters-and-enums.md`.

### Apex script — populate config from the org

Run in Developer Console → Execute Anonymous to generate a ready-to-paste JS config:

```apex
class ParameterEntry {
    String name; String value; Boolean visibleToCustomer;
    String displayLabel; Boolean required; String dataType; String description;
}
class MethodEntry {
    String paymentMethod; String paymentProcessor; String target;
    Boolean enabledOneTime; Boolean enabledRecurring;
    Boolean isDefaultOneTime; Boolean isDefaultRecurring;
    Boolean supportsRecurring; String displayLabel;
    List<ParameterEntry> parameters;
}
RestRequest req = new RestRequest();
RestResponse res = new RestResponse();
RestContext.request = req; RestContext.response = res;
req.requestURI = '/services/apexrest/cpm/v2/PaymentMethods';
req.httpMethod = 'GET';
req.headers.put('verbose', 'true');
cpm.API_PaymentMethod_V2.getPaymentMethods();
Map<String, Object> apiResponse = (Map<String, Object>) JSON.deserializeUntyped(res.responseBody.toString());
List<Object> paymentMethods = (List<Object>) apiResponse.get('PaymentMethods');
List<MethodEntry> config = new List<MethodEntry>();
Boolean isFirst = true;
for (Object m : paymentMethods) {
    Map<String, Object> method = (Map<String, Object>) m;
    for (Object p : (List<Object>) method.get('Processors')) {
        Map<String, Object> proc = (Map<String, Object>) p;
        Boolean supportsRecurring = (Boolean) proc.get('SupportsRecurring');
        List<ParameterEntry> parameters = new List<ParameterEntry>();
        List<Object> rawParams = (List<Object>) proc.get('Parameters');
        if (rawParams != null) {
            for (Object raw : rawParams) {
                Map<String, Object> rp = (Map<String, Object>) raw;
                ParameterEntry pe = new ParameterEntry();
                pe.name = (String) rp.get('Name'); pe.value = '';
                pe.visibleToCustomer = false; pe.displayLabel = (String) rp.get('Name');
                pe.required = (Boolean) rp.get('Required'); pe.dataType = (String) rp.get('DataType');
                pe.description = (String) rp.get('Description');
                parameters.add(pe);
            }
        }
        MethodEntry entry = new MethodEntry();
        entry.paymentMethod = (String) method.get('Name');
        entry.paymentProcessor = (String) proc.get('Name');
        entry.target = 'TODO — check FinDock Setup or Flow CPE UI';
        entry.enabledOneTime = true; entry.enabledRecurring = supportsRecurring;
        entry.isDefaultOneTime = isFirst; entry.isDefaultRecurring = isFirst && supportsRecurring;
        entry.supportsRecurring = supportsRecurring;
        entry.displayLabel = (String) method.get('Name');
        entry.parameters = parameters.isEmpty() ? null : parameters;
        config.add(entry); isFirst = false;
    }
}
// ... print as JS (see paymentMethodConfiguration.js in the FinDockLabs repo for the full print loop)
System.debug(JSON.serialize(config));
```

After running: fill in the `target` field for each entry (not returned by the API — find it in
FinDock Setup → Processors & Methods → processor → Accounts tab, or in the Flow CPE UI).

---

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

- In a **custom LWC using `c-payment-form`** (preferred, no Apex): drop in the FinDockLabs
  `paymentForm` component — it includes `c-payment-selector` and `cpm-pay-button` and needs no
  custom Apex. Configure payment methods in `paymentMethodConfiguration.js` using the flat schema
  above. See `on-platform-apex-lwc-flow.md` for the full component reference.
- In a **custom LWC using `c-payment-selector` directly**: import the flat config array, pass it
  as `config` to `<c-payment-selector>`, handle `paymentmethodchanged` to build the PaymentIntent,
  pass it to `<cpm-pay-button>`. No custom Apex needed.
- In a **custom LWC using `cpm-payment-method-selector` directly** (full schema): use Option B
  above when you need enum parameters or full schema control.
- In a **Flow**: configure `cpm:paymentMethodSelector` with the full-schema array, wire its output
  to `cpm:payButton`. No custom code. Consider `c-payment-form` instead if the use case fits.

## When finalizing

Keep the example, field table, and runtime interface in sync with the published pilot schema and
the FinDockLabs templates; reconcile any renamed fields and drop the pilot banner once GA. Keep
the parameter object schema aligned with `parameters-and-enums.md`.
