# Pattern 1 — Minimal One-Time Payment (plain HTML + vanilla JS)

This is a minimal, annotated example of a FinDock-powered payment form.
It uses a server-side proxy (at `/api/payment-intent`) to keep credentials out of the browser.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>One-Time Payment</title>
</head>
<body>
  <h1>Make a Payment</h1>
  <form id="payment-form">
    <label>First Name <input id="firstName" type="text" required></label>
    <label>Last Name  <input id="lastName"  type="text" required></label>
    <label>Email      <input id="email"     type="email" required></label>
    <label>Amount (€) <input id="amount"    type="number" min="1" step="0.01" required></label>
    <button type="submit">Pay Now</button>
  </form>
  <div id="status"></div>

  <script>
    document.getElementById('payment-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      document.getElementById('status').textContent = 'Processing…';

      // FinDock: build the PaymentIntent payload
      const payload = {
        // FinDock: URLs the PSP will redirect the payer to after payment
        SuccessURL: `${window.location.origin}/thank-you.html`,
        FailureURL: `${window.location.origin}/payment-failed.html`,

        // FinDock: payer details — must match org deduplication rules
        Payer: {
          Contact: {
            SalesforceFields: {
              FirstName: document.getElementById('firstName').value,
              LastName:  document.getElementById('lastName').value,
              Email:     document.getElementById('email').value,
            }
          }
        },

        // FinDock: OneTime block for a single payment
        OneTime: {
          Amount: parseFloat(document.getElementById('amount').value),
          PaymentMethod: 'CreditCard',
          // FinDock: Target omitted — FinDock uses the org's default processor for
          // this method. Add Target: 'Stripe1' only to override the default.
        }
      };

      try {
        // FinDock: POST to your server proxy, which adds the Bearer token and
        // calls https://{instance}.my.salesforce.com/services/apexrest/cpm/v2/PaymentIntent
        const response = await fetch('/api/payment-intent', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          const err = await response.json();
          // FinDock: error responses include an Errors array with error_code and error_message
          const msg = err.Errors?.map(e => e.error_message).join(', ') || 'Payment failed';
          document.getElementById('status').textContent = `Error: ${msg}`;
          return;
        }

        const result = await response.json();

        // FinDock: the response includes a RedirectURL — redirect the payer to the PSP
        if (result.RedirectURL) {
          window.location.href = result.RedirectURL;
        } else {
          // Some processors (e.g. direct debit) may not redirect
          document.getElementById('status').textContent = 'Payment initiated.';
        }

      } catch (err) {
        document.getElementById('status').textContent = `Unexpected error: ${err.message}`;
      }
    });
  </script>
</body>
</html>
```

## Minimal server proxy (Node.js / Express)

```javascript
// server.js — keeps Salesforce credentials server-side
const express = require('express');
const app = express();
app.use(express.json());

const SF_INSTANCE   = process.env.SF_INSTANCE;    // e.g. 'yourorg.my.salesforce.com'
const SF_TOKEN      = process.env.SF_ACCESS_TOKEN; // acquired via OAuth2

app.post('/api/payment-intent', async (req, res) => {
  const response = await fetch(
    `https://${SF_INSTANCE}/services/apexrest/cpm/v2/PaymentIntent`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // FinDock: Bearer token required — obtained via Salesforce OAuth2
        'Authorization': `Bearer ${SF_TOKEN}`,
      },
      body: JSON.stringify(req.body),
    }
  );
  const data = await response.json();
  res.status(response.status).json(data);
});

app.listen(3000, () => console.log('Proxy running on :3000'));
```

## Notes
- Replace `'CreditCard'` with the method name from `GET /PaymentMethods`; `Target` is optional (org default used when omitted)
- `Email` in `SalesforceFields` is the standard Salesforce `Contact.Email` field name
- Add more `SalesforceFields` (address, phone, etc.) as required by the org's dedup rules
- For sandbox, the Salesforce base URL is `https://{instance}.sandbox.my.salesforce.com`
