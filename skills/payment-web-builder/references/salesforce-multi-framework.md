# Pattern 5 — FinDock Payment Form on Salesforce Multi-Framework (Beta)

Runs a React-based FinDock payment form **natively inside Salesforce** as a UIBundle app.
No separate web server or OAuth proxy needed — authentication is handled by the platform.

> ⚠️ **Beta**: Available in sandbox and scratch orgs only (English default language).
> Multi-Framework **cannot be disabled** once enabled in an org.
> Not deployable to production orgs during beta.

---

## Prerequisites

- Salesforce CLI (latest)
- Node.js v18+
- Sandbox or scratch org with Multi-Framework enabled:
  Setup → search "Salesforce Multi-Framework" → React Development with Salesforce Multi-Framework (Beta) → **Enable Beta**
- For external (public-facing) apps: Digital Experiences must be enabled in the org

---

## Scaffold the app

```bash
# Generate a new UIBundle React app
sf template generate ui-bundle --name findockPayment

# Project lands in:
# force-app/main/default/uiBundles/findockPayment/
```

The template comes pre-configured with:
- `@salesforce/sdk-data` — Salesforce data access (GraphQL, Apex invocations)
- Vite (bundler) + Vitest (tests)
- shadcn/ui + Tailwind CSS

---

## Two approaches for calling the FinDock Payment API

### Option A — Apex proxy (recommended for production)

Write a thin Apex class that calls the FinDock REST API server-side. Invoke it from React
using `sdk.fetch()`. No CORS setup needed and no credentials to manage — the Apex methods run
in-transaction on-platform (no REST callout back into the org).

**Step 1 — Apex class**

```apex
// FinDockPaymentService.cls
public with sharing class FinDockPaymentService {

    // FinDock: Multi-Framework runs ON-PLATFORM, so call the managed Apex methods directly.
    // Do NOT make an HTTP callout back to the org's own REST endpoint — no Named Credential,
    // no callout:FinDockAPI. The static methods run in-transaction.
    @AuraEnabled
    public static String createPaymentIntent(String payloadJson) {
        // cpm.API_PaymentIntent_V2.postPaymentIntent — returns serialized response (incl. RedirectURL)
        return cpm.API_PaymentIntent_V2.postPaymentIntent(payloadJson);
    }

    @AuraEnabled(cacheable=true)
    public static String getPaymentMethods() {
        // cpm.API_PaymentMethod_V2.getPaymentMethods — same payload as GET /PaymentMethods
        return cpm.API_PaymentMethod_V2.getPaymentMethods();
    }
}
```

**Step 2 — React component calling the Apex method**

```tsx
// src/components/PaymentForm.tsx
import { useState, useEffect } from 'react';
import { createDataSDK } from '@salesforce/sdk-data';

// FinDock: createDataSDK handles Salesforce session auth automatically
// No token management needed in React code
const sdk = createDataSDK();

interface PaymentMethod {
  PaymentMethod: string;
  Target: string;
  IsDefault?: boolean;
  SupportsRecurring?: boolean;
}

export function PaymentForm() {
  const [methods, setMethods]         = useState<PaymentMethod[]>([]);
  const [selected, setSelected]       = useState<PaymentMethod | null>(null);
  const [amount, setAmount]           = useState('25');
  const [firstName, setFirstName]     = useState('');
  const [lastName, setLastName]       = useState('');
  const [email, setEmail]             = useState('');
  const [status, setStatus]           = useState('');
  const [submitting, setSubmitting]   = useState(false);

  // FinDock: load payment methods via Apex on mount
  useEffect(() => {
    sdk.fetch('/apex/FinDockPaymentService/getPaymentMethods', { method: 'GET' })
      .then(r => r.json())
      .then(data => {
        const available: PaymentMethod[] = data.PaymentMethods ?? [];
        setMethods(available);
        const def = available.find(m => m.IsDefault) ?? available[0];
        if (def) setSelected(def);
      })
      .catch(err => setStatus(`Could not load payment methods: ${err.message}`));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected) return;
    setSubmitting(true);
    setStatus('');

    // FinDock: construct the PaymentIntent payload
    const payload = {
      // FinDock: SuccessURL / FailureURL — the PSP redirects the payer here after payment
      // For internal Salesforce apps, point to a page in your org or App Launcher URL
      SuccessURL: `${window.location.origin}/lightning/n/Payment_Success`,
      FailureURL: `${window.location.origin}/lightning/n/Payment_Failed`,

      Payer: {
        Contact: {
          SalesforceFields: {
            FirstName: firstName.trim(),
            LastName:  lastName.trim(),
            Email:     email.trim(),
          },
        },
      },

      OneTime: {
        Amount:        parseFloat(amount),
        // FinDock: use values loaded from /PaymentMethods
        PaymentMethod: selected.PaymentMethod,
        Target:        selected.Target,
      },
    };

    try {
      // FinDock: call Apex which proxies to the FinDock Payment API
      const response = await sdk.fetch('/apex/FinDockPaymentService/createPaymentIntent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ payloadJson: JSON.stringify(payload) }),
      });

      const result = await response.json();

      if (result.Errors?.length) {
        // FinDock: Errors array with error_code and error_message
        setStatus(`Error: ${result.Errors.map((e: any) => e.error_message).join(', ')}`);
        return;
      }

      // FinDock: redirect the payer to the PSP payment page
      if (result.RedirectURL) {
        window.location.href = result.RedirectURL;
      } else {
        setStatus('Payment initiated successfully.');
      }
    } catch (err: any) {
      setStatus(`Unexpected error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto p-6">
      <h2 className="text-xl font-semibold mb-4">Make a Payment</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* FinDock: payment method picker from /PaymentMethods */}
        {methods.length > 0 && (
          <fieldset className="border rounded p-3">
            <legend className="text-sm font-medium px-1">Payment method</legend>
            {methods.map(m => (
              <label key={`${m.PaymentMethod}-${m.Target}`} className="flex items-center gap-2 mb-1">
                <input
                  type="radio"
                  name="method"
                  checked={selected?.Target === m.Target && selected?.PaymentMethod === m.PaymentMethod}
                  onChange={() => setSelected(m)}
                />
                {m.PaymentMethod}
                {m.IsDefault && <span className="text-xs text-gray-400">(default)</span>}
              </label>
            ))}
          </fieldset>
        )}

        <div>
          <label className="block text-sm font-medium mb-1">Amount (€)</label>
          <input
            type="number" min="1" step="0.01" value={amount}
            onChange={e => setAmount(e.target.value)} required
            className="w-full border rounded px-3 py-2"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium mb-1">First name</label>
            <input value={firstName} onChange={e => setFirstName(e.target.value)} required
              className="w-full border rounded px-3 py-2" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Last name</label>
            <input value={lastName} onChange={e => setLastName(e.target.value)} required
              className="w-full border rounded px-3 py-2" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Email</label>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)} required
            className="w-full border rounded px-3 py-2" />
        </div>

        {status && <p className="text-sm text-red-600">{status}</p>}

        <button
          type="submit" disabled={submitting || !selected}
          className="w-full bg-blue-600 text-white py-2 rounded font-medium disabled:opacity-50"
        >
          {submitting ? 'Processing…' : 'Pay now'}
        </button>
      </form>
    </div>
  );
}
```

---

### Option B — Direct REST call (NOT recommended on-platform)

Avoid this for Multi-Framework. Because the app runs inside Salesforce, the correct path is the
Apex static methods in Option A (`cpm.API_PaymentIntent_V2.postPaymentIntent` /
`cpm.API_PaymentMethod_V2.getPaymentMethods`). The REST endpoint is for external clients only;
calling it from on-platform code adds needless auth/CORS complexity and breaks the on-platform
model. This section is retained only to make the distinction explicit — prefer Option A.

**CORS setup (one-time):**
Setup → Security → CORS → Add `https://<your-org-domain>.lightning.force.com`

```tsx
import { createDataSDK } from '@salesforce/sdk-data';

const sdk = createDataSDK();

// FinDock: get the session context to extract the instance URL and access token
const context = await sdk.getContext();
const SF_INSTANCE = context.instanceUrl;  // e.g. https://yourorg.my.salesforce.com
const token       = context.accessToken;  // Salesforce session token

const response = await fetch(
  `${SF_INSTANCE}/services/apexrest/cpm/v2/PaymentIntent`,
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // FinDock: use the platform-managed session token directly
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  }
);
```

> Note: `sdk.getContext()` API shape — verify against the latest `@salesforce/sdk-data`
> docs as this is a beta SDK. The exact method names may change before GA.

---

## UIBundle metadata file

```xml
<!-- findockPayment.uiBundle-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<UIBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>FinDock Payment</label>
    <description>FinDock payment form powered by Salesforce Multi-Framework</description>
    <isExposed>true</isExposed>
</UIBundle>
```

---

## Build and deploy

```bash
# Build the React app
cd force-app/main/default/uiBundles/findockPayment
npm run build

# Push to the org
sf project deploy start

# Find in App Launcher as "FinDock Payment"
```

---

## Local development

```bash
npm run dev
# Preview at http://localhost:5173
# Note: Salesforce SDK calls won't work locally without a mock — use stub data for UI work
```

---

## Key differences vs standalone React

| | Standalone React | Multi-Framework |
|---|---|---|
| Auth | Server proxy with Bearer token | `@salesforce/sdk-data` handles it |
| Deployment | Any web host | Salesforce org (sandbox/scratch only in beta) |
| CORS | Required in Salesforce | Not needed with Apex approach |
| Salesforce data access | REST/GraphQL with token | GraphQL + `@wire`-style hooks natively |
| Production ready | Yes | No (beta) |
| SuccessURL target | Your own domain | Lightning page or App Launcher URL |

---

## Resources

- [Salesforce Multi-Framework blog post](https://developer.salesforce.com/blogs/2026/04/build-with-react-run-on-salesforce-introducing-salesforce-multi-framework)
- [Beta documentation](https://developer.salesforce.com/docs/platform/einstein-for-devs/guide/reactdev-overview.html)
- [Multi-Framework Recipes (20+ examples)](https://github.com/trailheadapps/multiframework-recipes)
- [Setup guide](https://developer.salesforce.com/docs/platform/code-builder/guide/reactdev-setup.html)
