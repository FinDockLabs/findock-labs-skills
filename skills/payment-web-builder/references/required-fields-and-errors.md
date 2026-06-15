# Required Fields & Response / Error Handling

Two things every FinDock form must get right: collect the data the payment actually requires,
and handle the response by routing the payer to success or a correctly-categorized error.

---

## 1. Required fields — validate before submitting

A PaymentIntent will fail server-side if mandatory data is missing. Validate on the client so
the payer fixes it before the call, not after. Required fields come from three layers:

### Core (always required)
- **Payer identity sufficient for the org's deduplication rules.** For a **Contact**, that is
  at minimum **FirstName + LastName** (LastName is the hard Salesforce requirement; collect
  both). For an **Account/Person Account**, **Name** (or FirstName + LastName for Person
  Account). Email is effectively required for receipts and usually for dedup — treat it as
  required unless the user says otherwise.
- **Amount** > 0 (error code 200 rejects 0/negative).
- **A payment method** selected.

### Payment-method / processor parameters
Each method-processor combination declares its own required parameters in the
`/PaymentMethods` (or `getPaymentMethods()`) response — e.g. IBAN for SEPA, account/routing
number for ACH, issuer where required. Render every parameter marked `Required: true` and
validate it client-side, applying the `minLength`/`maxLength` from the response. See
`parameters-and-enums.md`.

### Source-connector parameters
Some source connectors require additional fields (error code 012 flags these). When in doubt,
check `/SourceConnector` and the docs MCP.

### Implementation rule
Mark required inputs with `required` + `aria-required="true"`, validate inline (real-time or
on blur per `page-quality.md`), block submit until valid, and show field-level messages that
say how to fix the problem. Never rely on the server to be the first line of validation.

---

## 2. Response handling — always route to success or failure

Every form MUST resolve the PaymentIntent response into one of three outcomes. Never leave the
payer on a spinning button.

```
PaymentIntent response
├─ RedirectURL present  → send payer to the PSP (window.location = RedirectURL)
│                          (PSP then returns to your SuccessURL / FailureURL)
├─ Errors present        → categorize (see below): recoverable → inline; else → generic failure
└─ Success, no redirect  → show success (direct-debit methods often don't redirect)
```

- The success/failure destination can be **built into the form** (swap to a success/error
  panel in place) **or a standalone page** (`SuccessURL` / `FailureURL`, or your own
  `/thank-you` / `/payment-failed`). Either is fine — but one must always be reached.
- For redirect-based methods (cards, iDEAL, etc.) the PSP uses the `SuccessURL` / `FailureURL`
  you supplied in the PaymentIntent. Provide both.
- For non-redirect methods (e.g. SEPA/Bacs Direct Debit) handle success inline from the
  response, since there's no PSP round-trip.

---

## 3. Error categorization — recoverable vs generic

FinDock errors return as `{ "Errors": [{ "error_code": "...", "error_message": "..." }] }`.

**Only error codes 201–205 are payer-recoverable** — they mean the payer entered something
fixable (bad IBAN, missing BIC/address for non-EEA SEPA, invalid sort code). For these, show
the problem **next to the relevant field** and let the payer correct and retry.

| Code | Meaning | Recovery shown to payer |
|---|---|---|
| 201 | Sort code or bank account invalid (Bacs DD) | Re-enter sort code / account number |
| 202 | IBAN is not valid | Re-enter IBAN |
| 203 | IBAN not in SEPA geographical zone | Use a SEPA-zone account |
| 204 | BIC required (SEPA DD from non-EEA bank) | Provide BIC |
| 205 | Address required (SEPA DD from non-EEA bank) | Provide street, number, zip, city |

**Every other code is NOT payer-recoverable → show one generic error message.** This includes
010/011/012 (malformed request — a build bug, not the payer's fault), 200 (invalid data),
206 (Sweden clearing/account), 998 (missing object/default — org config), 999 (uncategorized),
and any HTTP 4xx/5xx or network failure. Do not surface raw `error_message` text or codes to
the payer for these — log them for the developer, show the payer something like:

> "Something went wrong processing your payment. Please try again, or contact us if the problem
> continues." (plus a support link)

### Reference implementation

```javascript
// FinDock: error codes 201–205 are the ONLY payer-recoverable ones
const RECOVERABLE = {
  '201': 'Please check your sort code and account number.',
  '202': 'That IBAN doesn’t look valid — please check and try again.',
  '203': 'That account isn’t in the SEPA zone. Please use a SEPA-area account.',
  '204': 'Please provide the BIC for this bank account.',
  '205': 'Please provide your street, house number, postcode and city.',
};

function handleErrors(errors) {
  // If ANY error is non-recoverable, show the generic failure (don't half-recover)
  const allRecoverable = errors.every(e => RECOVERABLE[e.error_code]);
  if (allRecoverable) {
    // Recoverable: show field-level guidance inline, keep the payer on the form
    errors.forEach(e => showFieldError(mapCodeToField(e.error_code), RECOVERABLE[e.error_code]));
    return 'recoverable';
  }
  // Not recoverable: log details for devs, show ONE generic message / go to failure page
  console.error('FinDock payment error', errors);
  showGenericFailure();   // or: window.location = FailureURL
  return 'failed';
}
```

```javascript
// Wiring it into the submit flow
const result = await submitPaymentIntent(payload); // REST proxy OR Apex method
if (result.Errors?.length) {
  handleErrors(result.Errors);
} else if (result.RedirectURL) {
  window.location.href = result.RedirectURL;          // PSP → SuccessURL/FailureURL
} else {
  showSuccess();                                       // non-redirect success
}
```

### Rules of thumb
- Categorize by `error_code`, never by parsing `error_message` strings.
- Mixed batch (some recoverable, some not) → treat the whole submission as failed and show the
  generic error; don't ask the payer to fix one field when another problem will still block it.
- Recoverable errors stay on the form with field-level messaging; generic errors go to the
  failure panel/page.
- Always log the full `Errors` array for developers regardless of category.
