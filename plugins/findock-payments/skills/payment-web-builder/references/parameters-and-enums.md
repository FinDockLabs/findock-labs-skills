# Payment Method Parameters — Enums, Labels, Images & Tokenization Fields

The `GET /PaymentMethods` response includes a `Parameters` array per processor-method
combination. This reference covers how to render those parameters correctly in a form —
especially **enum parameters**, which ship with FinDock-hosted labels and images.

---

## Enum parameters: always use the label and image from the response

When a parameter has `DataType: "Enum"` (e.g. `issuer` for iDEAL, `cardBrand` for cards),
the `Enum` array contains **objects** — not bare strings — each with:

| Field | Use for |
|---|---|
| `value` | What you send in the PaymentIntent `Parameters` object |
| `label` | What you show the payer (human-readable name) |
| `image.svg` | The logo/icon URL to render next to the label |

Example from the response (iDEAL issuer):

```json
{
  "Required": false,
  "Name": "issuer",
  "DataType": "Enum",
  "Description": "The issuing bank. Use this parameter to skip the bank selection screen of the PSP and send the user directly to their bank's authorization environment.",
  "Enum": [
    {
      "value": "abnamro",
      "label": "ABN AMRO",
      "image": { "svg": "https://images.findock.com/issuers/abnamro/issuer.svg" }
    },
    {
      "value": "asnbank",
      "label": "ASN Bank",
      "image": { "svg": "https://images.findock.com/issuers/asnbank/issuer.svg" }
    }
  ]
}
```

### Rules

1. **Never hardcode enum options** (issuer lists, card brands). Render them from the
   response. When a PSP or FinDock adds an issuer or brand, the form picks it up
   automatically — no code change.
2. **Show `label`, send `value`.** The payer sees "ABN AMRO"; the PaymentIntent gets
   `"issuer": "abnamro"`.
3. **Use `image.svg` verbatim.** Image URLs come from FinDock-managed domains
   (`images.findock.com`, `external.findock.com`) — use whatever URL the response gives,
   don't construct your own paths for enum values. See "Enum icon URLs" below for the
   pattern and the per-method sub-folder convention when you must construct a URL.
4. Selecting an issuer up-front lets the payer **skip the PSP's bank selection screen** —
   a meaningful UX improvement for iDEAL, so prefer showing the issuer selector when the
   enum is present.

### Enum icon URLs (issuers & card brands)

Unlike top-level **payment-method** icons (which sit directly under
`https://external.findock.com/icon/payment-methods/<methodname>.svg` — see the SKILL.md
"Payment method, issuer, and card brand images" section), **enum** icons for issuers and
card brands live in a **per-method sub-folder**:

```
https://external.findock.com/icon/payment-methods/<methodname>/<value>.svg
```

- `<methodname>` = the parent method Name, lowercased with all non-alphanumeric characters
  removed (`CreditCard` → `creditcard`, `iDEAL` → `ideal`).
- `<value>` = the enum option's `value`.

Examples:
- iDEAL issuer ING → `https://external.findock.com/icon/payment-methods/ideal/ing.svg`
- Credit-card brand Visa → `https://external.findock.com/icon/payment-methods/creditcard/visa.svg`

**Always prefer the `image.svg` URL from the response verbatim** — it is authoritative and
may point at `external.findock.com` or `images.findock.com` (e.g.
`https://images.findock.com/issuers/abnamro/issuer.svg`). Only fall back to constructing the
sub-folder URL above when you have no live response. As with method icons: never hand-draw,
approximate, or substitute a generic icon — if the data source lacks an image URL, fix the
source or apply the pattern, don't fake it.

**Delivery** is the same choice as for method icons: hotlink (requires `external.findock.com`
and `images.findock.com` as CSP Trusted Sites) or bundle the SVGs as a static resource
(no CSP Trusted Site; preferred for Experience Cloud / guest-user sites).

### Rendering pattern (vanilla JS)

Row layout order: visible radio first, then the option image, then the label.

```javascript
// FinDock: render an enum parameter (e.g. iDEAL issuer) with label + image
function renderEnumParam(param, container) {
  const wrap = document.createElement('div');
  wrap.className = 'enum-grid';

  param.Enum.forEach(option => {
    const el = document.createElement('label');
    el.className = 'enum-option';
    el.innerHTML = `
      <input type="radio" name="param_${param.Name}" value="${option.value}">
      <img src="${option.image?.svg ?? ''}" alt="" height="24"
           onerror="this.style.display='none'">
      <span>${option.label}</span>
    `;
    wrap.appendChild(el);
  });

  container.appendChild(wrap);
}

// FinDock: when building the PaymentIntent, send the value (not the label)
const issuer = document.querySelector('input[name="param_issuer"]:checked')?.value;
// → goes into the PaymentMethod Parameters: { "issuer": "abnamro" }
```

### Where parameter values go in the PaymentIntent

Parameter values are sent in the `PaymentMethod` object of the PaymentIntent request:

```json
{
  "PaymentMethod": {
    "Name": "Ideal",
    "Parameters": {
      "issuer": "abnamro"
    }
  }
}
```

---

## Tokenization form parameters (card / bankAccount form types)

For processors that support direct tokenization, the parameters define the fields of the
card or bank account form. The inventory below per processor-method combination
(source: FinDock internal parameter sheet; verify against `GET /PaymentMethods` at runtime
since processor support evolves):

### Card form type (`formType: card`)

| Parameter | Type | Notes |
|---|---|---|
| `cardNumber` | String | Required everywhere |
| `expirationMonth` | Integer | Required everywhere |
| `expirationYear` | Integer | Required everywhere |
| `cvc` | String | Conditionally required (processor/flow dependent) |
| `cardBrand` | String | Optional everywhere — **enum with label + image**, render as selector |
| `holderName` | String | Required for PaymentHub-MT940 and PaymentHub-WorldPay; not used by Stripe/Paya/Authorize.net card forms |

Processors with a card form: PaymentHub-Stripe, FinDock-for-Paya, AuthorizeNet-for-FinDock,
PaymentHub-MT940, PaymentHub-WorldPay.

### Bank account form type (`formType: bankAccount`)

| Processor / Method | Required | Optional | Length constraints |
|---|---|---|---|
| PaymentHub-Stripe / ACH DD | email, holderName, accountNumber, routingNumber, accountHolderType | — | holderName max 22, accountNumber min 4 |
| FinDock-for-Paya / ACH DD | holderName, accountNumber, routingNumber, accountType | — | holderName max 35, accountNumber min 6 |
| AuthorizeNet-for-FinDock / ACH DD | holderName, accountNumber, routingNumber, accountType | email | holderName max 22, accountNumber min 4 |
| PaymentHub-MT940 / Giropayments | holderName, accountNumber, routingNumber, accountType | email | holderName max 35, accountNumber min 4 |

Notes:
- **`accountHolderType` vs `accountType`**: Stripe ACH uses `accountHolderType`; Paya,
  Authorize.net and MT940 use `accountType`. Both are typically enums (e.g.
  individual/company, checking/savings) — render from the response's Enum array when present.
- **Length validation**: apply `minLength`/`maxLength` from the response as HTML
  `minlength`/`maxlength` attributes and in client-side validation. The values differ per
  processor (e.g. holderName max 22 for Stripe vs 35 for Paya), so derive them from the
  response rather than hardcoding.

---

## General parameter rendering algorithm

For each parameter in the `Parameters` array of the selected processor-method:

1. `DataType === "Enum"` → render a selector (radio/dropdown) from the `Enum` array,
   showing `label` + `image.svg`, submitting `value`
2. `DataType === "Integer"` → `<input type="number">`
3. `DataType === "String"` → `<input type="text">` with `minlength`/`maxlength` from the
   response
4. `Required === true` → mark the field required; `false` → optional (label it as such);
   missing/empty → conditionally required, check the processor docs via the docs MCP
5. Use `Description` from the response as the field's help text or placeholder
