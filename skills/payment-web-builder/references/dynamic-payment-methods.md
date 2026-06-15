# Pattern 2 — Dynamic Payment Method Selector (React)

Loads available payment methods from `GET /PaymentMethods` at runtime, lets the payer
choose, and submits a PaymentIntent with the selected method and processor.

```jsx
// PaymentForm.jsx
import { useState, useEffect } from 'react';

export default function PaymentForm() {
  const [methods, setMethods]         = useState([]);
  const [selectedMethod, setSelected] = useState(null);
  const [amount, setAmount]           = useState('');
  const [firstName, setFirstName]     = useState('');
  const [lastName, setLastName]       = useState('');
  const [email, setEmail]             = useState('');
  const [status, setStatus]           = useState('');
  const [loading, setLoading]         = useState(true);

  // FinDock: load available payment methods on mount
  useEffect(() => {
    fetch('/api/payment-methods')
      .then(r => r.json())
      .then(data => {
        // FinDock: response is an array of { PaymentMethod, Target, IsDefault, ... }
        setMethods(data.PaymentMethods ?? []);
        const def = data.PaymentMethods?.find(m => m.IsDefault) ?? data.PaymentMethods?.[0];
        if (def) setSelected(def);
      })
      .finally(() => setLoading(false));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedMethod) return;
    setStatus('Processing…');

    // FinDock: build PaymentIntent using the payer-selected method + its default processor
    const payload = {
      SuccessURL: `${window.location.origin}/thank-you`,
      FailureURL: `${window.location.origin}/payment-failed`,
      Payer: {
        Contact: {
          SalesforceFields: { FirstName: firstName, LastName: lastName, Email: email }
        }
      },
      OneTime: {
        Amount: parseFloat(amount),
        // FinDock: PaymentMethod and Target populated from /PaymentMethods response
        PaymentMethod: selectedMethod.PaymentMethod,
        Target:        selectedMethod.Target,
      }
    };

    const response = await fetch('/api/payment-intent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const result = await response.json();

    if (!response.ok) {
      const msg = result.Errors?.map(e => e.error_message).join(', ') || 'Error';
      setStatus(`Error: ${msg}`);
      return;
    }

    // FinDock: redirect to PSP
    if (result.RedirectURL) {
      window.location.href = result.RedirectURL;
    } else {
      setStatus('Payment initiated.');
    }
  };

  if (loading) return <p>Loading payment options…</p>;

  return (
    <form onSubmit={handleSubmit}>
      <h2>Pay</h2>

      {/* FinDock: render a radio row per method — REQUIRED order: radio, then logo, then label.
          The logo URL is on the PROCESSOR: m.Processors[].image.svg (NOT m.image.svg). */}
      <fieldset>
        <legend>Payment method</legend>
        {methods.map(m => {
          const proc = m.Processors?.find(p => p.IsDefault) ?? m.Processors?.[0];
          const imgUrl = proc?.image?.svg;   // ← correct path
          return (
            <label key={m.Name}>
              <input
                type="radio"
                name="paymentMethod"
                checked={selectedMethod?.Name === m.Name}
                onChange={() => setSelected(m)}
              />
              {imgUrl && (
                <img src={imgUrl} alt={m.Name} height={24}
                     onError={(e) => { e.currentTarget.style.display = 'none'; }} />
              )}
              <span>{m.Name}</span>
              {m.IsDefault && ' ✓ default'}
            </label>
          );
        })}
      </fieldset>

      <label>First name <input value={firstName} onChange={e => setFirstName(e.target.value)} required /></label>
      <label>Last name  <input value={lastName}  onChange={e => setLastName(e.target.value)}  required /></label>
      <label>Email      <input type="email" value={email} onChange={e => setEmail(e.target.value)} required /></label>
      <label>Amount (€) <input type="number" min="1" step="0.01" value={amount} onChange={e => setAmount(e.target.value)} required /></label>

      <button type="submit" disabled={!selectedMethod}>Pay Now</button>
      {status && <p>{status}</p>}
    </form>
  );
}
```

## Server proxy additions (for `/api/payment-methods`)

```javascript
// FinDock: proxy the GET /PaymentMethods call to avoid CORS and keep the token server-side
app.get('/api/payment-methods', async (req, res) => {
  const response = await fetch(
    `https://${SF_INSTANCE}/services/apexrest/cpm/v2/PaymentMethods`,
    { headers: { 'Authorization': `Bearer ${SF_TOKEN}` } }
  );
  res.status(response.status).json(await response.json());
});
```

## Notes
- `PaymentMethods` response shape: always verify with `GET /PaymentMethods` via the docs MCP
  before assuming field names — the schema can vary slightly with processor updates
- `IsDefault` tells you which processor is the org's default for a given payment method
- If the org has only one processor, you can skip the selector and hardcode; but dynamic is
  safer for long-lived integrations
- Payment method–specific fields (e.g. IBAN for SEPA, phone number for Swish) need to be
  added to the `OneTime` or payment method block — always check the docs MCP for the PSP
- For rendering the `Parameters` array — especially Enum parameters like iDEAL `issuer`
  and `cardBrand` which include `label` + `image.svg` per option — see
  `parameters-and-enums.md` in this references folder

## Enum parameters: render with label and image

Some payment method parameters are **enums** — most notably `issuer` for iDEAL (the payer's
bank). For enum parameters, the `GET /PaymentMethods` response includes the list of allowed
values, and each value can carry a **label** (display name) and **image** (logo URL on
`external.findock.com`).

**Always render enum parameters as a visual picker using the label and image from the
response** — never as a free-text input, and never with hardcoded bank lists.

```javascript
// FinDock: render an enum parameter (e.g. iDEAL issuer) as a visual picker
// using the labels and images supplied in the /PaymentMethods response
function renderEnumParameter(param, container) {
  // Defensive: the enum value list may be under param.Values / param.AllowedValues —
  // verify the exact field name against the /PaymentMethods response of the org
  // or the FinDock docs MCP before relying on it.
  const values = param.Values ?? param.AllowedValues ?? [];

  const list = document.createElement('div');
  list.className = 'enum-picker';

  values.forEach(v => {
    // Each enum value can include: value (API value), label (display name),
    // image (logo URL, e.g. bank logos for iDEAL issuers)
    const apiValue = v.value ?? v.Value ?? v;
    const label    = v.label ?? v.Label ?? apiValue;
    const imgUrl   = v.image?.svg ?? v.image ?? null;

    const option = document.createElement('label');
    option.className = 'enum-option';
    option.innerHTML = `
      <input type="radio" name="param_${param.Name}" value="${apiValue}">
      ${imgUrl ? `<img src="${imgUrl}" alt="${label}" height="24"
                       onerror="this.style.display='none'">` : ''}
      <span>${label}</span>
    `;
    list.appendChild(option);
  });

  container.appendChild(list);
}

// Detect enum vs free-text when rendering Parameters:
processor.Parameters?.forEach(param => {
  const isEnum = Array.isArray(param.Values ?? param.AllowedValues);
  if (isEnum) {
    renderEnumParameter(param, extraFieldsContainer);
  } else {
    renderTextInput(param, extraFieldsContainer);  // e.g. IBAN
  }
});
```

The selected enum value is submitted in the PaymentIntent like any other parameter, e.g.
`{ "OneTime": { ..., "issuer": "<selected-value>" } }` — check the parameter docs via the
docs MCP for where exactly the parameter belongs in the payload for the given processor.
