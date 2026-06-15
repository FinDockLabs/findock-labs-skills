# FinDock Supported Payment Methods & Processors Catalogue

Source: https://docs.findock.com/docs/payment-processors/payment-methods/payment-methods-overview

Use this catalogue during intake **Question 5** to show the user which payment methods and
processors FinDock supports — grouped by category. This is the full FinDock product catalogue,
NOT what's active in a specific org (that's what `GET /PaymentMethods` returns at runtime).

> **Note**: this list reflects the docs at time of writing. If the user asks about a method not
> listed here, or you want to confirm current support, check the FinDock docs MCP or the source
> page above — FinDock adds processors and methods regularly.

---

## Cards
| Payment Method | Processors |
|---|---|
| Card (credit/debit) | Adyen, Authorize.net, Axerve, Buckaroo, Checkout.com, Mollie, Paya, Redsys, Saferpay, Stripe, Worldpay BG350, Worldpay Corporate Gateway |

## Direct Debit
| Payment Method | Processors |
|---|---|
| SEPA Direct Debit | Buckaroo, FinDock (native), GoCardless, Mollie, Stripe |
| Bacs Direct Debit (UK) | Access PaySuite (SmartDebit), FinDock (native), GoCardless, Stripe |
| ACH Direct Debit (US) | Authorize.net, GoCardless, Paya, Stripe |
| Autogiro (Sweden) | FinDock (native), GoCardless |
| AvtaleGiro (Norway) | FinDock (native) |
| CH-DD Direct Debit (Switzerland) | FinDock (native) |
| LSV Direct Debit (Switzerland) | FinDock (native) |
| Pre-authorized Debit / PAD (Canada) | GoCardless, Stripe |

## Online Banking
| Payment Method | Processors |
|---|---|
| iDEAL - Wero (Netherlands) | Adyen, Buckaroo, Checkout.com, Mollie, Stripe |
| iDEAL QR - Wero | Buckaroo |
| Bancontact (Belgium) | Adyen, Buckaroo, Checkout.com, Mollie, Stripe |
| Sofort (DACH) | Adyen, Buckaroo, Mollie |
| BLIK (Poland) | Stripe |
| Przelewy24 (Poland) | Stripe |
| Bizum (Spain) | Redsys |
| TWINT (Switzerland) | Saferpay |
| PostFinance Pay (Switzerland) | Saferpay |
| Instant Bank Pay | GoCardless |

## Wallets
| Payment Method | Processors |
|---|---|
| Apple Pay | Adyen, Saferpay, Stripe, Worldpay Corporate Gateway |
| Google Pay | Adyen, Saferpay, Stripe, Worldpay Corporate Gateway |
| PayPal | Buckaroo, Mollie, PayPal (direct) |
| Swish (Sweden) | Swish (direct) |
| Vipps (Norway) | Vipps MobilePay |
| MobilePay (Denmark/Finland) | Vipps MobilePay |
| Satispay (Italy) | Stripe |

## Bank Transfer
| Payment Method | Processors |
|---|---|
| SEPA Bank Transfer | FinDock (native) |
| Giro | FinDock (native) |
| Standing Order | FinDock (native) |

## Payment Request (reference-based: invoices, payment slips)
| Payment Method | Processors |
|---|---|
| Acceptgiro (Netherlands) | FinDock (native) |
| Bollettino Postale (Italy) | FinDock (native) |
| ESR / QR-bill (Switzerland) | FinDock (native) |
| Giro KID / OCR (Norway) | FinDock (native) |
| OGM (Belgium) | FinDock (native) |
| iDEAL QR | Buckaroo |
| Tikkie (Netherlands) | Tikkie (direct) |

## Credit Transfer (outgoing / payable installments)
| Payment Method | Processors |
|---|---|
| SEPA Credit Transfer | FinDock (native) |

---

## How to present this during intake

Don't dump the whole catalogue. Ask about the donor/customer audience first
(country/region matters most), then offer the relevant subset. For example:

- **Netherlands**: iDEAL, Card, SEPA Direct Debit, PayPal, Tikkie
- **UK**: Card, Bacs Direct Debit, Apple Pay / Google Pay
- **US**: Card, ACH Direct Debit, Apple Pay / Google Pay, PayPal
- **Sweden**: Swish, Card, Autogiro
- **Norway**: Vipps, Card, AvtaleGiro
- **Switzerland**: TWINT, Card, QR-bill, CH-DD/LSV
- **Belgium**: Bancontact, Card, SEPA Direct Debit
- **Poland**: BLIK, Przelewy24, Card
- **International/mixed**: Card, PayPal, Apple Pay / Google Pay + region-specific extras

Recurring support varies by method-processor combination. Always check the specific
method page on docs.findock.com (or the docs MCP) when recurring is in scope — for
example, most online banking methods (iDEAL, Bancontact, Sofort) handle recurring via
a first payment that establishes a SEPA mandate.

## Important distinction for the build

- **This catalogue** = what FinDock *can* support → use during intake to ask the user what
  they want
- **`GET /PaymentMethods`** = what's *activated in the org right now* → use at runtime in
  dynamic forms

If the user picks methods from this catalogue that aren't yet activated in their org, note
that they (or their admin) need to install/activate the relevant payment extension in
FinDock Setup → Processors & Methods before the form will work end-to-end.
