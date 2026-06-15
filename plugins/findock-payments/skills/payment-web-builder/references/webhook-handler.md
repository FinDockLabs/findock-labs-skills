# Pattern 4 — Webhook Handler (Node.js / Express)

FinDock sends webhook events to your `WebhookURL` after payment processing.
Include `WebhookURL` in the PaymentIntent body; also add it to Salesforce Remote Site Settings.

## Event types

| Event | When it fires |
|-------|--------------|
| `paymentIntent.processed` | PaymentIntent processed (not necessarily collected) |
| `paymentIntent.in_review` | Processing stalled, manual SF intervention needed |
| `paymentIntent.failed` | PaymentIntent processing failed in Salesforce |
| `installment.created` | Installment record created |
| `installment.status_change` | Installment status changed (e.g. Pending → Collected) |

## Handler example

```javascript
// webhook.js — server-side webhook receiver
const express = require('express');
const router  = express.Router();

router.post('/api/webhook', express.json(), (req, res) => {
  const event = req.body;

  // FinDock: always acknowledge quickly (200) before doing any slow work
  res.sendStatus(200);

  // FinDock: route by event type
  switch (event.type) {

    case 'paymentIntent.processed':
      console.log('PaymentIntent processed:', event.data.Id);
      // event.data contains: Id, Status, Payer, OneTime/Recurring, etc.
      // Status 'Matched' = fully reconciled; 'Pending' = awaiting PSP callback
      handlePaymentIntentProcessed(event.data);
      break;

    case 'paymentIntent.failed':
      console.error('PaymentIntent failed:', event.data.Id);
      // Alert your team or log for manual review in Salesforce
      handlePaymentIntentFailed(event.data);
      break;

    case 'installment.status_change':
      // FinDock: fired whenever an installment status changes
      // event.data.Status values: Pending, Collected, Failed, Cancelled, etc.
      console.log(`Installment ${event.data.Id} → ${event.data.Status}`);
      handleInstallmentStatusChange(event.data);
      break;

    case 'installment.created':
      console.log('Installment created:', event.data.Id);
      break;

    default:
      console.log('Unknown event type:', event.type);
  }
});

function handlePaymentIntentProcessed(data) {
  // Access Salesforce record IDs for downstream processing:
  // data.Payer.Contact.Id  → Contact record
  // data.OneTime.Id        → Installment record
  // data.Recurring.Id      → Recurring record (if applicable)
}

function handleInstallmentStatusChange(data) {
  if (data.Status === 'Collected') {
    // Payment succeeded — send receipt email, update your DB, etc.
    // data.Payments is an array of Payment records (cash movements)
  } else if (data.Status === 'Failed') {
    // Payment failed — trigger retry logic or notify payer
  }
}

function handlePaymentIntentFailed(data) {
  // Log and alert — this means Salesforce-side processing failed
  // The payer's PSP journey may still be ongoing
}

module.exports = router;
```

## PaymentIntent webhook body structure

```json
{
  "type": "paymentIntent.processed",
  "data": {
    "Id": "pi_6cazikr7625yqt9mf",
    "Status": "Matched",
    "Payer": {
      "Contact": { "Id": "0033X00003H9uZPQAZ", "Name": "Jane Doe" },
      "Account": { "Id": "0013X00002bZPGIQA4", "Name": "Doe Family" }
    },
    "OneTime": {
      "Id": "a083X00001mFTBAQA4",
      "Type": "cpm__Installment__c",
      "Status": "Pending"
    }
  }
}
```

## Installment status_change webhook body

```json
{
  "type": "installment.status_change",
  "data": {
    "Id": "a083X00001kJynLQAS",
    "Status": "Collected",
    "Amount": 25.00,
    "AmountOpen": 0,
    "PaymentMethod": "CreditCard",
    "PaymentProcessor": "Stripe1",
    "PaymentIntentId": "pi_5jthokq7z8som0w6o",
    "Payments": [
      {
        "Id": "a0R3X00000V1sutUAB",
        "Amount": 25.00,
        "CollectionDate": "2025-03-15",
        "PaymentMethod": "CreditCard",
        "PaymentProcessor": "Stripe1"
      }
    ]
  }
}
```

## Alternative: polling instead of webhooks

If you can't receive inbound webhooks, poll `GET /PaymentIntent/{ID}` after redirect:

```javascript
// Poll for status after the payer returns from the PSP
async function pollPaymentStatus(paymentIntentId, maxAttempts = 10) {
  for (let i = 0; i < maxAttempts; i++) {
    const res  = await fetch(`/api/payment-status/${paymentIntentId}`);
    const data = await res.json();
    // FinDock: InboundReport.Status tells you the processing state
    if (['Matched', 'Failed'].includes(data.Status)) return data;
    await new Promise(r => setTimeout(r, 2000)); // wait 2s between polls
  }
  return null;
}
```

## Salesforce Remote Site Settings

For webhooks to work, add your webhook URL to Salesforce:
1. Setup → Security → Remote Site Settings
2. Add your webhook domain (e.g. `https://yoursite.com`)
