# Field catalogue

Deployed API names carry the `cpm__` prefix. Two source objects can host a Guided Matching Setup;
`Guided_Matching_Setup__c.Object__c` is either `Transaction` or `Inbound_Report`, and that choice
changes both the available fields and the implicit dependencies of the DML rule types.

---

## Which object am I on?

| | `Transaction__c` | `Inbound_Report__c` |
|---|---|---|
| Comes from | bank statement / return files (camt.053, camt.054, MT940, CODA, N43, BACS ARUDD/ADDACS, Autogiro, BGMax…) | PSP notifications, webhooks, Payment API PaymentIntents, and a few file formats (Bollettino, OCR) |
| Parent | `Transaction_Set__c` (master-detail, one per imported file) | `Message__c` |
| Raw payload field | `cpm__Raw_XML_entry__c`, `cpm__Additional_Entry_Information__c` | `cpm__RAW_Message__c` |
| Routed by | `Target__c` or file type | `Report_Type__c` + `Report_SubType__c` |
| Debit/credit field | `cpm__Type__c` (`Credit` / `Debit`) | `cpm__Debit_Credit_Type__c` (picklist) |
| IBAN field | `cpm__IBAN__c` | `cpm__Account_Number__c` |
| Scratch fields | `cpm__Custom_1__c` … `cpm__Custom_5__c` | none — but it has ~70 fields |
| Typical terminal rule | `processInstallment` | `processInstallment`, `processPaymentIntent`, `processRefund`, `handleNotification` |

Note the field-name divergence: **IBAN lives in `cpm__IBAN__c` on Transaction and
`cpm__Account_Number__c` on Inbound Report**, and the amount date is `cpm__Date__c` on both but
`cpm__Value_Date__c` exists only on Transaction. Always confirm which object before writing rules.

---

## `Transaction__c` — 66 fields

**Raw / source**
`Raw_XML_entry__c` (long text) · `Additional_Entry_Information__c` (long text) ·
`File_Reference__c` · `Batch_Id__c` · `Entry_Type__c` (picklist `Entry`, `Entry Detail`) ·
`Entry_Reference__c` · `Custom_1__c`…`Custom_5__c` (text 255, free scratch space) ·
`Transaction_set__c` (master-detail) · `Job_Group_Identifier__c`

**Amount and dates**
`Amount__c` (currency) · `Actual_Amount__c` (formula, negated for Debit) ·
`Open_Amount__c` (currency) · `Date__c` (datetime) · `Value_Date__c` (datetime)

**References**
`Payment_Reference__c` · `Account_Servicer_Reference__c` (bank's own reference) ·
`End_To_End_ID__c` · `Mandate_Reference__c` (text, not a lookup) · `Payment_Info_Id__c` ·
`Reason_Code__c` · `Remittance_Information__c` (255) ·
`Remittance_Information_Long__c` (131072 — the usual regex/fixed-width input)

**Counterparty**
`IBAN__c` (label "Bank Account Number") · `BIC_Code__c` · `Account_Holder_Name__c` ·
`Address_Line_1__c` · `Street__c` · `Building_Number__c` · `City__c` · `PostalCode__c` · `Country__c`

**Payment method / entry type**
`Reported_Payment_Method__c` (text) · `Reported_Payment_Method_Code__c` (text) ·
`Type__c` (picklist `Credit`, `Debit`) · `Reversal_Indicator__c` (checkbox)

**Record references** (the fields matching rules usually write)
`Installment__c` → Installment · `Payment_Profile__c` → Payment Profile · `Contact__c` → Contact ·
`Account__c` → Account · `Campaign__c` → Campaign · `Campaign_Member_Id__c` (text 18, soft ref) ·
`Multiple_Installment_Ids__c` / `Other_Installment_Ids__c` / `Processed_Installment_Ids__c`
(comma-separated id text)

There is **no** `Payment__c`, `Refund__c` or `Mandate__c` lookup on Transaction.

**Status / control**
`Status__c` (picklist: New, Processing, Pending, Matched, Partially Matched, Manual Matched, Manual,
No Match, Duplicate, Ignored, Processed, Guided Review, Failed, Batch Failed) ·
`Status_Reason__c` (restricted picklist, 17 diagnostic values) ·
`Failure_Status__c` (restricted picklist, 11 values) · `Guided_Matching_Error__c` ·
`Guided_Matching_Installment_Processed__c` · `Guided_Matching_Job_Id__c` ·
`Guided_Matching_Log__c` · `Guided_Matching_Nr_Of_Retries__c` ·
`Guided_Matching_Nr_Of_Rules_Processed__c` · `Has_Been_In_Guided_Review__c` ·
`Matched_By_ProcessingHub__c` · `Primary__c` · `ProcessingHub_Id__c` · `Processor__c` ·
`Start_Guided_Matching__c` · `Target__c` (routing key) · `Use_Open_Amount__c` ·
`Last_Worked_On_Date__c`

---

## `Inbound_Report__c` — ~68 fields

**Raw / source**: `RAW_Message__c` (long text — the full PSP payload) · `Event_Parameters__c` ·
`Message__c` → Message · `Origin__c` · `Source__c` · `Target__c` · `External_Id__c` ·
`Unique_Identifier__c` · `Checksum__c` · `File_Reference__c` · `WebhookURL__c` ·
`Guided_Matching_Setup__c` → Guided Matching Setup

**Routing**: `Report_Type__c` (picklist) · `Report_SubType__c` (picklist) · `Report_Status__c` ·
`Report_Status_Reason_Information__c` · `Transaction_Code__c` · `Document_Type__c` ·
`Sequence_Number__c` · `Post_Office__c`

**Amount and dates**: `Amount__c` · `Open_Amount__c` · `Date__c` (date) · `Report_Date__c` (date) ·
`Event_Date__c` (datetime) · `Event_DateTime_ISO8601__c` (text)

**References**: `Payment_Reference__c` · `Payment_Intent_Id__c` · `Recurring_Id__c` ·
`Record_Id__c` (a Salesforce id extracted from the payload) · `Mandate_Reference__c` ·
`Original_Mandate_Reference__c` · `Reason_Code__c` · `Reasoncode_Explanation__c`

**Counterparty**: `Account_Number__c` (the IBAN) · `Account_Number_Additional__c` (BIC) ·
`Account_Holder_Name__c` · `Payment_Method__c` (text) · `Payment_Processor__c` (text) ·
`Debit_Credit_Type__c` (picklist)

**Record references**: `Installment__c` · `Payment_Profile__c` · `Contact__c` · `Account__c` ·
`Campaign__c` · `Campaign_Member_Id__c` (text) · `Mandate__c` · `Refund__c` ·
`Multiple_Installment_Ids__c` / `Other_Installment_Ids__c` / `Processed_Installment_Ids__c`

**Control**: `Status__c` (picklist) · `Status_Reason__c` · `Accepted__c` ·
`Existing_Installment_Expected__c` (checkbox — the standard "should we match or create?" switch) ·
`Use_Open_Amount__c` · `Matched_By_ProcessingHub__c` · `Has_Been_In_Guided_Review__c` ·
`Start_Guided_Matching__c` · `Guided_Matching_Error__c` / `_Job_Id__c` / `_Log__c` /
`_Nr_of_Retries__c` / `_Nr_of_Rules_Processed__c` / `_Installment_Processed__c` ·
`Job_Group_Identifier__c` · `ProcessingHub_Id__c`

---

## Match targets on `Installment__c`

The installment is the thing being paid. Reference fields, in the order you would normally try them:

| Field | Notes |
|---|---|
| `cpm__Final_Payment_Reference__c` | **Formula**: `Custom_Payment_Reference__c` → else `Recurring_Payment_Reference__c` → else `Generated_Payment_Reference__c`. One query instead of three; not indexed, so watch volume. |
| `cpm__Custom_Payment_Reference__c` | External id. The customer's own reference. |
| `cpm__Recurring_Payment_Reference__c` | External id. Stable across a recurring schedule. |
| `cpm__Generated_Payment_Reference__c` | External id. FinDock-generated. |
| `cpm__Payment_Transaction_Id__c` | Where `End_To_End_Id__c` is stored on create. |
| `cpm__External_ID__c`, `cpm__ProcessingHub_Id__c`, `cpm__Payment_Intent_Id__c` | Other external ids. |
| `cpm__Payment_Profile__c`, `cpm__Contact__c`, `cpm__Account__c` | Relationship-based fallback. |
| `cpm__IBAN__c` | **Formula** off the payment profile / mandate. |
| `cpm__Amount__c`, `cpm__Amount_Open__c`, `cpm__Due_Date__c`, `cpm__Original_Due_Date__c` | Narrowing criteria and sort keys. |
| `cpm__Originating_Campaign__c`, `cpm__Mandate__c`, `cpm__Recurring_Payment__c`, `cpm__Payment_Schedule__c` | Enrichment sources. |

`cpm__Status__c` values: `New`, `Outstanding` (default), `Pending`, `Pending Processing`,
`Pending recollection`, `Partially paid`, `Paid`, `Collected`, `Failed`, `Rejected`, `Cancelled`,
`Reversed`, `Refunded`.
The `INSTALLMENT_CLOSED_STATUS` sentinel covers `Collected`, `Reversed`, `Refunded`, `Rejected`,
`Cancelled`, `Failed`, `Paid` — so `Status__c notEquals INSTALLMENT_CLOSED_STATUS` means
"New, Outstanding, Pending, Pending Processing, Pending recollection or Partially paid".

`Payment_Method__c`, `Payment_Processor__c`, `Source__c` and `Target__c` are picklists whose values
are injected per connector at install time — the base package ships them empty. Never assume a value
exists; ask the user what their org uses.

Record types: `Receivable` (money in) and `Payable` (money out). `createInstallment` picks `Payable`
for a Debit transaction, `Receivable` otherwise.

## Match targets on `Payment_Profile__c`

`cpm__IBAN__c` · `cpm__Bank_Account__c` (pre-SEPA account number) · `cpm__BIC_Code__c` ·
`cpm__Sort_Code__c` · `cpm__Bank_Code__c` · `cpm__Branch_Code__c` · `cpm__Clearing_Member_Id__c` ·
`cpm__Holder_Name__c` · `cpm__Contact__c` · `cpm__Account__c` · `cpm__Unique_Identifier__c`
(unique external id — the dedupe key `createPaymentProfile` always upserts on) ·
`cpm__Primary_Identifier__c` · `cpm__ProcessingHub_Id__c` · `cpm__Token__c` · `cpm__Wallet_Id__c` ·
`cpm__Card_BIN__c` · `cpm__Brand__c`

There is **no** `Status__c`, `Payment_Method__c` or `Type__c` on Payment Profile. The nearest things:
`cpm__Active__c` (checkbox — always filter active profiles), `cpm__Funding_Type__c`
(`Debit`/`Credit`), `cpm__Bank_Account_Type__c` (`checking`/`savings`),
`cpm__Wallet_Type__c` (`Apple Pay`/`Google Pay`), `cpm__Country_PL__c` (`GB`/`NO`/`SE`/`US`/`Other`).
Record types include `IBAN` and `Credit_Card`; reference them as `cpm.IBAN` in a
`createPaymentProfile` `RecordTypeId` mapping.

## `Guided_Matching_Setup__c` — where the ruleset lives

| Field | Notes |
|---|---|
| `cpm__Rules__c` | Long text 131,072. The JSON array. |
| `cpm__Object__c` | `Transaction` or `Inbound_Report`. |
| `cpm__Target__c` | External id. Routes Transactions whose `Target__c` matches. |
| `cpm__Report_Type__c` / `cpm__Report_Sub_Type__c` | Route Inbound Reports. |
| `cpm__Active__c` | Default true. |
| `cpm__Job_Size__c` | Default 200 records per Apex job. |
| `cpm__Processing_Mode__c` | `Serial` (default) or `Parallel` (only for very large Transaction sets). |

The record name is generated by FinDock and truncated to 80 characters. Uniqueness is enforced in
code on `{Object__c, Report_Type__c, Report_Sub_Type__c}` (or `Target__c`), not by a DB constraint.

Known limitation: roll-up summary fields on `Transaction_Set__c` cause locked-row errors during
Guided Matching. Use reports instead.
