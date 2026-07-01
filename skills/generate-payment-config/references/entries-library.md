# Known Entries Library (static — Modes B and C only)

These are illustrative examples, not org-verified data. Mode D (live org) pulls real parameters.
Copy entries verbatim; adjust `target` and `isDefault*` before writing.

## File header (include at top of generated file)

```javascript
/**
 * Payment method configuration for the paymentForm component.
 * Edit to match the payment methods and processors activated in your org.
 *
 * Auto-generate from a configured org:
 *   npm run generate:config -- --org <orgAlias>
 *   Then fill in `target` per entry (not returned by the API).
 *
 * TARGET FIELD: FinDock Setup → Processors & Methods → [processor] → Accounts tab.
 */
```

## Regional presets

| Region | Methods to include |
|---|---|
| Netherlands | iDEAL, CreditCard, SEPA Direct Debit, PayPal |
| Belgium | Bancontact, CreditCard, SEPA Direct Debit |
| UK | CreditCard, Bacs Direct Debit |
| US | CreditCard, ACH Direct Debit |
| Sweden | CreditCard, Autogiro |
| Poland | BLIK, Przelewy24, CreditCard |
| Canada | CreditCard, PAD |
| Italy | CreditCard, Satispay, SEPA Direct Debit |
| International/mixed | CreditCard, SEPA Direct Debit, iDEAL, PayPal |

---

## PaymentHub-Stripe

```javascript
{
    paymentMethod: 'CreditCard',
    paymentProcessor: 'PaymentHub-Stripe',
    target: '',
    enabledOneTime: true,
    enabledRecurring: true,
    isDefaultOneTime: false,
    isDefaultRecurring: false,
    supportsRecurring: true,
    displayLabel: 'Credit Card',
    parameters: [
        {
            name: 'locale',
            value: '',
            visibleToCustomer: false,
            displayLabel: 'Locale',
            required: false,
            data_type: 'String',
            description: 'BCP 47 language tag for the Stripe checkout page. Examples: nl-NL, en-US.'
        }
    ]
}

{
    paymentMethod: 'Ideal',
    paymentProcessor: 'PaymentHub-Stripe',
    target: '',
    enabledOneTime: true,
    enabledRecurring: false,
    isDefaultOneTime: false,
    isDefaultRecurring: false,
    supportsRecurring: false,
    displayLabel: 'iDEAL',
    redirectInstruction: 'You will be redirected to your bank to complete the payment.',
    parameters: null
}

{
    paymentMethod: 'SEPA Direct Debit',
    paymentProcessor: 'PaymentHub-Stripe',
    target: '',
    enabledOneTime: true,
    enabledRecurring: true,
    isDefaultOneTime: false,
    isDefaultRecurring: false,
    supportsRecurring: true,
    displayLabel: 'SEPA Direct Debit',
    parameters: null
}

{
    paymentMethod: 'Bancontact',
    paymentProcessor: 'PaymentHub-Stripe',
    target: '',
    enabledOneTime: true,
    enabledRecurring: false,
    isDefaultOneTime: false,
    isDefaultRecurring: false,
    supportsRecurring: false,
    displayLabel: 'Bancontact',
    redirectInstruction: 'You will be redirected to your bank to complete the payment.',
    parameters: null
}

{
    paymentMethod: 'BLIK',
    paymentProcessor: 'PaymentHub-Stripe',
    target: '',
    enabledOneTime: true,
    enabledRecurring: false,
    isDefaultOneTime: false,
    isDefaultRecurring: false,
    supportsRecurring: false,
    displayLabel: 'BLIK',
    parameters: null
}

{
    paymentMethod: 'Przelewy24',
    paymentProcessor: 'PaymentHub-Stripe',
    target: '',
    enabledOneTime: true,
    enabledRecurring: false,
    isDefaultOneTime: false,
    isDefaultRecurring: false,
    supportsRecurring: false,
    displayLabel: 'Przelewy24',
    redirectInstruction: 'You will be redirected to complete the payment.',
    parameters: null
}

{
    paymentMethod: 'Satispay',
    paymentProcessor: 'PaymentHub-Stripe',
    target: '',
    enabledOneTime: true,
    enabledRecurring: false,
    isDefaultOneTime: false,
    isDefaultRecurring: false,
    supportsRecurring: false,
    displayLabel: 'Satispay',
    parameters: null
}

{
    paymentMethod: 'ACH Direct Debit',
    paymentProcessor: 'PaymentHub-Stripe',
    target: '',
    enabledOneTime: true,
    enabledRecurring: true,
    isDefaultOneTime: false,
    isDefaultRecurring: false,
    supportsRecurring: true,
    displayLabel: 'ACH Direct Debit',
    parameters: null
}

{
    paymentMethod: 'PAD',
    paymentProcessor: 'PaymentHub-Stripe',
    target: '',
    enabledOneTime: true,
    enabledRecurring: true,
    isDefaultOneTime: false,
    isDefaultRecurring: false,
    supportsRecurring: true,
    displayLabel: 'Pre-authorized Debit',
    parameters: null
}
```

## GoCardless

```javascript
{
    paymentMethod: 'SEPA Direct Debit',
    paymentProcessor: 'GoCardless',
    target: '',
    enabledOneTime: true,
    enabledRecurring: true,
    isDefaultOneTime: false,
    isDefaultRecurring: false,
    supportsRecurring: true,
    displayLabel: 'SEPA Direct Debit',
    parameters: null
}

{
    paymentMethod: 'BACS Direct Debit',
    paymentProcessor: 'GoCardless',
    target: '',
    enabledOneTime: true,
    enabledRecurring: true,
    isDefaultOneTime: false,
    isDefaultRecurring: false,
    supportsRecurring: true,
    displayLabel: 'Bacs Direct Debit',
    parameters: null
}

{
    paymentMethod: 'ACH Direct Debit',
    paymentProcessor: 'GoCardless',
    target: '',
    enabledOneTime: true,
    enabledRecurring: true,
    isDefaultOneTime: false,
    isDefaultRecurring: false,
    supportsRecurring: true,
    displayLabel: 'ACH Direct Debit',
    parameters: null
}

{
    paymentMethod: 'PAD',
    paymentProcessor: 'GoCardless',
    target: '',
    enabledOneTime: true,
    enabledRecurring: true,
    isDefaultOneTime: false,
    isDefaultRecurring: false,
    supportsRecurring: true,
    displayLabel: 'Pre-authorized Debit',
    parameters: null
}

{
    paymentMethod: 'Autogiro',
    paymentProcessor: 'GoCardless',
    target: '',
    enabledOneTime: false,
    enabledRecurring: true,
    isDefaultOneTime: false,
    isDefaultRecurring: false,
    supportsRecurring: true,
    displayLabel: 'Autogiro',
    parameters: null
}
```

## PaymentHub-Mollie

```javascript
{
    paymentMethod: 'CreditCard',
    paymentProcessor: 'PaymentHub-Mollie',
    target: '',
    enabledOneTime: true,
    enabledRecurring: true,
    isDefaultOneTime: false,
    isDefaultRecurring: false,
    supportsRecurring: true,
    displayLabel: 'Credit Card',
    parameters: null
}

{
    paymentMethod: 'Ideal',
    paymentProcessor: 'PaymentHub-Mollie',
    target: '',
    enabledOneTime: true,
    enabledRecurring: false,
    isDefaultOneTime: false,
    isDefaultRecurring: false,
    supportsRecurring: false,
    displayLabel: 'iDEAL',
    redirectInstruction: 'You will be redirected to your bank to complete the payment.',
    parameters: null
}

{
    paymentMethod: 'SEPA Direct Debit',
    paymentProcessor: 'PaymentHub-Mollie',
    target: '',
    enabledOneTime: true,
    enabledRecurring: true,
    isDefaultOneTime: false,
    isDefaultRecurring: false,
    supportsRecurring: true,
    displayLabel: 'SEPA Direct Debit',
    parameters: null
}

{
    paymentMethod: 'PayPal',
    paymentProcessor: 'PaymentHub-Mollie',
    target: '',
    enabledOneTime: true,
    enabledRecurring: false,
    isDefaultOneTime: false,
    isDefaultRecurring: false,
    supportsRecurring: false,
    displayLabel: 'PayPal',
    redirectInstruction: 'You will be redirected to PayPal to complete the payment.',
    parameters: null
}

{
    paymentMethod: 'Bancontact',
    paymentProcessor: 'PaymentHub-Mollie',
    target: '',
    enabledOneTime: true,
    enabledRecurring: false,
    isDefaultOneTime: false,
    isDefaultRecurring: false,
    supportsRecurring: false,
    displayLabel: 'Bancontact',
    redirectInstruction: 'You will be redirected to your bank to complete the payment.',
    parameters: null
}
```
