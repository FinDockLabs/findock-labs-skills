# Pattern 3 — Recurring Payment Setup

Recurring payments replace (or supplement) the `OneTime` block with a `Recurring` block.
Some PSPs require an initial one-time authorisation payment alongside the recurring setup —
use `GET /PaymentMethods` to check `RequiresInitialPayment` for each method.

> **Note**: `Target` is optional in all examples below. When omitted, FinDock uses the
> org's default processor for the payment method. The examples include it for clarity.

## Recurring-only (no initial payment)

```json
{
  "SuccessURL": "https://yoursite.com/thank-you",
  "FailureURL": "https://yoursite.com/failed",
  "Payer": {
    "Contact": {
      "SalesforceFields": {
        "FirstName": "Jane",
        "LastName": "Doe",
        "Email": "jane@example.com"
      }
    }
  },
  "Recurring": {
    "Amount": 10.00,
    "Frequency": "Monthly",
    "PaymentMethod": "DirectDebit",
    "Target": "GoCardless1"
  }
}
```

## Recurring + initial authorisation payment (e.g. card mandates)

Some processors (Stripe, Adyen) require an initial £0 or real-amount payment
to collect the card mandate. Check `GET /PaymentMethods` response for the processor.

```json
{
  "SuccessURL": "https://yoursite.com/thank-you",
  "FailureURL":  "https://yoursite.com/failed",
  "Payer": {
    "Contact": {
      "SalesforceFields": { "FirstName": "Jane", "LastName": "Doe", "Email": "jane@example.com" }
    }
  },
  "OneTime": {
    "Amount": 0,
    "PaymentMethod": "CreditCard",
    "Target": "Stripe1"
  },
  "Recurring": {
    "Amount": 15.00,
    "Frequency": "Monthly",
    "PaymentMethod": "CreditCard",
    "Target": "Stripe1"
  }
}
```

## Updating an existing recurring payment

To change the payment method/processor on an existing recurring payment,
omit `Payer` and add the recurring record's `Id` (GUID or Salesforce record Id):

```json
{
  "Recurring": {
    "Id": "a0V3X00000S7b5YUAR",
    "PaymentMethod": "SEPA",
    "Target": "Buckaroo1",
    "IBAN": "NL00BANK0000000000"
  }
}
```

## Source connector differences

The `Recurring` block maps to different Salesforce objects depending on the source connector:

| Source connector | Salesforce object |
|-----------------|-------------------|
| FinDock standard | `cpm__Recurring_Payment__c` |
| NPSP | `npe03__Recurring_Donation__c` |
| NPC / Fundraising | `Gift_Commitment__c` (split: GiftCommitment + GiftCommitmentSchedule) |

For NPC/Fundraising, prefix fields targeting the parent object with `GiftCommitment.`:
```json
"SalesforceFields": {
  "GiftCommitment.GiftVehicle": "Cash",
  "StartDate": "2025-01-01"
}
```

## Frequency values

Always verify accepted `Frequency` values with `GET /PaymentMethods` or the docs MCP,
as available frequencies depend on the processor and FinDock configuration. Common values:
`Weekly`, `Monthly`, `Quarterly`, `Yearly`.

## Notes
- `GET /Recurring/{ID}` retrieves current details of a recurring payment record
- Recurring updates do not require `Payer` — only `Id` + changed fields in `Recurring`
- For webhook events on recurring, only `paymentIntent.processed` fires (not per-installment
  events); use `installment.status_change` on subsequent collected installments
