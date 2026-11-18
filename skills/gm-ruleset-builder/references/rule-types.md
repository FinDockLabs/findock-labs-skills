# Rule JSON schema — every key FinDock actually reads

Derived from `sfdx-source/cpm/guidedMatching/classes/` (PaymentHub, March '26 build, namespace `cpm`;
`dataCloudQuery` and `promptTemplate` added from the September '26 `main`).
`Rules__c` is a **JSON array of rule objects**. A non-array root, or a non-object element, throws an
unhandled Apex exception on save.

---

## Keys every rule supports

| Key | Type | Required | Notes |
|---|---|---|---|
| `ruleType` | string | yes | Must be one of the 26 literals in the next section, exactly. Anything else throws `Rule type <x> unknown.` |
| `id` | string | yes | Unique. The order calculator keys its output map by id — a missing or duplicate id leaves a rule without a `seqNr`, which disables Save in the Setup UI with the cyclic-dependency banner. FinDock's generator makes `<6 alphanumerics>-<8 digits>`, e.g. `Qa1Bc7-10000003`. Two reserved literals: `PROCINS` (processInstallment) and `FWDTOSRC` (forwardToSource, never stored). |
| `name` | string | yes | Shown in Guided Matching Progress and Guided Review. Write it as the reviewer's answer to "what did this step do?" |
| `fieldName` | string | yes | The one Transaction / Inbound Report field this rule **writes**. API name with `cpm__` prefix. |
| `fieldType` | string | yes | Lower-cased `Schema.DisplayType` of `fieldName`: `string`, `textarea`, `picklist`, `reference`, `boolean`, `currency`, `double`, `percent`, `date`, `datetime`, `time`. Drives value coercion — get it wrong and the write silently misbehaves. |
| `seqNr` | numeric string | yes | Ignored at runtime (the engine walks array order) and recalculated by the Setup UI. Supply it anyway, matching array position. |
| `jobNr` | numeric string | yes | Always `"1"` — job chaining is disabled in the codebase. |
| `iconName` | string | no | SLDS icon in the setup UI. Conventions: `standard:topic2` constant, `standard:display_text` regexp, `standard:text` normalize, `standard:entity` query, `standard:record_create` create, `standard:record_update` update, `standard:search` / `standard:user` manualInput, `utility:data_cloud` dataCloudQuery, `standard:agent_astro` promptTemplate, `standard:partner_fund_allocation` processInstallment. |
| `entryCriteria` | array | no | Gate on **input** fields only. Never reference `fieldName` here (see `ordering.md` §3a). |
| `forcedExecuteAfterRule` | string (another rule's `id`) | no | Hard ordering pin + removes the rule from the dependency graph. See `ordering.md` §4. |
| `emptyEntryCriteriumDisabled` | `"true"` (**string**, not boolean) | no | Turns off the automatic skip-if-output-already-filled. Apex compares to a string literal, so a JSON `true` is silently ignored. Use only when a rule must overwrite (e.g. an `apex` normalisation step). Legacy alias: `entryCriteriumDisabled`. |
| `notMatchedByProcessingHubEntryCriteriumDisabled` | boolean | no | Set `true` to let the rule run on transactions ProcessingHub already matched. Default: those are skipped. |
| `persistBeforeProcessing` | boolean | no | Rarely needed. |
| `userGuidance` | string | no | Reviewer-facing text. Read by the UI, not by Apex. |
| `allowSkip` | boolean | no | Shows "Skip & Continue" in Guided Review. UI-only. |
| `showOtherRow` | boolean | no | Adds a "no match" row to a guided-review result table. UI-only. |
| `managed`, `managedRuleSetName`, `managedRuleSetPackage`, `package`, `doFirst`, `lastInManagedRuleSet` | — | **never emit** | These mark a rule as FinDock-managed and make it read-only in the UI. |

### `entryCriteria` item

```json
{ "id": "Ec1Aa1-10000032", "fieldName": "cpm__Payment_Reference__c",
  "fieldType": "string", "comparisonOperator": "notEquals", "value": "" }
```

`comparisonOperator` ∈ `equals`, `notEquals`, `startsWith`, `greaterThan`, `greaterThanOrEqual`,
`lessThan`, `lessThanOrEqual`, `inPaymentIntent`, `notInPaymentIntent`.

- Numeric comparison when `fieldType` is `currency`/`double`/`percent`; date comparison for
  `date`/`datetime`; otherwise string comparison.
- `inPaymentIntent` / `notInPaymentIntent` test the deserialised PaymentIntent in `Raw_Message__c`;
  `value` ∈ `contact`, `account`, `contactId`, `accountId`, `paymentProfile`, `oneTimeId`,
  `oneTimeOrRecurring` (last one only with `inPaymentIntent`).
- There is **no `mappingType`** on entry criteria — that key only exists on `queryCriteria`.

### `fieldMapping` (DML rule types)

```json
"fieldMapping": {
  "cpm__Payment_Method__c": { "type": "value", "value": "Bank Transfer" },
  "cpm__IBAN__c":           { "type": "field", "fieldName": "cpm__Account_Number__c" },
  "cpm__Bank_Name__c":      { "type": "field", "fieldName": "cpm__Custom_1__c", "onlyIfBlank": true }
}
```

Default behaviour overwrites the target whenever the source value differs. `onlyIfBlank: true`
restricts it to filling blanks. `type: "field"` sources are what create ordering dependencies.

---

## The 26 valid `ruleType` values

`constant` · `regexp` · `fixedWidthExtract` · `normalize` · `query` · `keywordSearch` ·
`findDuplicates` · `createRecord` · `updateRecord` · `createContact` · `createPaymentProfile` ·
`createInstallment` · `updateInstallment` · `createCampaignMember` · `updateCampaignMember` ·
`manualInput` · `apex` · `sendMessage` · `guaranteedOrdering` · `handleNotification` ·
`processInstallment` · `processPaymentIntent` · `processRefund` · `forwardToSource` ·
`dataCloudQuery` · `promptTemplate`

**Org-gated:** `dataCloudQuery` and `promptTemplate` are registered in every org, but the Setup UI only
offers them when the org has the feature — Data 360 for `dataCloudQuery`, Agentforce (plus the
FinDock Agentforce package) for `promptTemplate`. Never put either in a ruleset until the user has
confirmed their org has it (see SKILL.md). In an org without the feature the rule cannot be edited in
the UI and fails at runtime.

Plus the pseudo-type `managedRuleSet` — **do not use it**, see `ordering.md` §8.

`apex`, `sendMessage`, `guaranteedOrdering`, `handleNotification`, `processRefund`,
`processPaymentIntent`, `processInstallment` and `forwardToSource` are not offered in the Add-Rule
picker in the UI (`ruleTypeNotChangeable`). Only build them into JSON when the use case genuinely
needs them.

---

## Per-type keys

### `constant`
| Key | Req | Notes |
|---|---|---|
| `constant` | yes | Literal written to `fieldName`, coerced by `fieldType`. |

A `constant` rule writing `Status__c` always bypasses the auto-skip.

### `regexp`
| Key | Req | Notes |
|---|---|---|
| `inputFieldName` | yes | Source field, usually `cpm__RAW_Message__c` / `cpm__Remittance_Information_Long__c`. |
| `regExp` | yes | **Java** regex. |
| `regExpCapturingGroup` | yes | Group index as a string. `"0"` = whole match — with `fieldType: "boolean"` this checks the box on any match. |
| `regExpCapturingGroup2` | no | With `fieldType: "currency"`: group 1 = whole units, group 2 = cents. With a date: group 2 = month. |
| `regExpCapturingGroup3` | no | Date: day (group 1 = year, 2 = month). Two-digit years pivot at 80. |
| `regExpMultiValue` | no | `true` joins all matches comma-separated (string targets only, truncated to field length). |

### `fixedWidthExtract`
For CODA, N43 and other fixed-position formats. Extracted values are trimmed.

| Key | Req | Notes |
|---|---|---|
| `inputFieldName` | yes | |
| `fixedWidthExtractStartPosition` / `fixedWidthExtractEndPosition` | yes | 1-based, inclusive, clamped to range. |
| `fixedWidthExtractLineStartsWith` | no | Pick the line by prefix; blank = first line. |
| `fixedWidthExtractOnlyIfLineStartsWith` / `...OnlyIfStartPosition` / `...OnlyIfEndPosition` / `...OnlyIfValue` | no | Conditional extraction: only extract when that other window equals `OnlyIfValue`. |

### `normalize`
| Key | Req | Notes |
|---|---|---|
| `caseStrategy` | no | `toUpperCase` \| `toLowerCase` |
| `whitespaceStrategy` | no | `trim` \| `deleteWhitespace` |

Transforms the value already in `fieldName`; only acts on `string`/`textarea`. Always runs (auto-skip
is permanently off), so it is safe to place after several rules that may have written the field.

### `query`
| Key | Req | Notes |
|---|---|---|
| `queryObject` | yes | SObject API name to query. |
| `queryReturnField` | yes | Field on that object whose value lands in `fieldName` — `Id` for a lookup, or e.g. `cpm__Contact__c` to hop one relationship. |
| `queryFirstWhereQueryObjectField` | yes | Left side of the first WHERE. |
| `queryFirstWhereTransactionField` | yes | Transaction field supplying the value. **Creates a dependency.** |
| `queryFirstWhereTransactionFieldMultiValue` | no | `true` treats the transaction value as a comma list, matched with `IN`. |
| `queryCriteria` | no | Extra conditions, see below. |
| `queryOrderByField` / `querySortOrder` | no | `asc` (anything but the literal `desc`) \| `desc`. The ORDER BY is always applied — it decides the winner under `takeFirst` and `takeAllInstallmentIds`, and the row order of the guided-review picker. |
| `multipleResultsStrategy` | no | `takeFirst` \| `noResult` \| `takeAllInstallmentIds` \| `guidedReview`. **Unrecognised or absent falls through to guided review** — always set it explicitly. `takeAllInstallmentIds` fills `cpm__Multiple_Installment_Ids__c`, which auto-skips every later rule writing `cpm__Installment__c` — so it must be the last rung of the ladder. |
| `singleResultStrategy` | no | `takeSingleResult` (default) \| `guidedReview`. |
| `multipleResultsFieldsToDisplay` | no | Columns in the guided-review picker. Required in practice when `multipleResultsStrategy` is `guidedReview`. |
| `allowSkip` | no | |

Performance: FinDock logs the query time for every query and hard-fails when a query would exceed
the 50,000-row governor limit. Filter on indexed fields where you can.

`queryCriteria` item:

```json
{ "id": "Cc1Aa1-10000031", "mappingType": "value", "fieldName": "cpm__Status__c",
  "fieldType": "picklist", "comparisonOperator": "notEquals", "value": "INSTALLMENT_CLOSED_STATUS" }
```

- `mappingType: "value"` → literal SOQL clause. Supported operators: `equals`, `notEquals`,
  `greaterThan`, `lessThan`, `greaterThanOrEqual`. **`lessThanOrEqual` is broken here** — the
  operator map has no matching key and the clause silently degrades to `=`. Use `lessThan` or a
  `field` mapping instead.
- `mappingType: "field"` → `value` holds a *transaction* field API name. The clause is **not** in the
  SOQL; results are filtered in Apex afterwards, with the full operator set working correctly. Also
  creates an ordering dependency.
- `value: "INSTALLMENT_CLOSED_STATUS"` with `equals`/`notEquals` expands to the closed-status set:
  `Collected`, `Reversed`, `Refunded`, `Rejected`, `Cancelled`, `Failed`, `Paid`. Use
  `notEquals` to restrict a query to open installments — this is the standard guard and it reads no
  transaction field, so it is cycle-safe.
- A `RecordTypeId` criterion accepts either a real id (starting `012`) or a RecordType
  DeveloperName.

### `keywordSearch`
Same key *names* as `query`, but three real differences:

- `multipleResultsStrategy` and `singleResultStrategy` are **never read** — the first regex match wins.
- A `queryCriteria` entry with `mappingType: "field"` is **silently ignored** (it only adds a SELECT),
  while still creating an ordering dependency.
- `INSTALLMENT_CLOSED_STATUS` and `RecordTypeId` criteria **break it at runtime**: keywordSearch skips
  the first WHERE clause, but those two branches still prepend `' and '`, producing
  `WHERE  and ...` with no bind map, and every record fails. Use a `query` rule if you need either.

Each candidate record's `queryFirstWhereQueryObjectField` value is treated as a **case-insensitive
regex** and tested against the transaction field. The whole keyword table is scanned — limit 500
rows. Point it at a small custom keyword object.

### `dataCloudQuery` (Data360 Query Rule)
A `query` rule pointed at a **Data 360 Data Model Object (DMO)** instead of a Salesforce object. It
subclasses `QueryGuidedMatchingRule`, so it takes exactly the `query` keys and behaves the same way —
`queryFirstWhere*`, `queryCriteria`, `queryOrderByField`, `multipleResultsStrategy` /
`singleResultStrategy`, guided review on multiple results, `userGuidance`, `allowSkip`, `showOtherRow`.
Ordering dependencies and `preferredOrder` (3) are identical to `query`.

What is different:

- **Availability.** Only offered in the Setup UI when Data 360 is provisioned (the
  `standard.Audience360` app exists). Ask before using it.
- **`queryObject` must be a DMO API name ending in `__dlm`** (e.g. `ssot__Individual__dlm` or a custom
  `Donor_Bank_Account__dlm`). The UI takes it as free text and rejects anything else; DMOs cannot be
  listed from packaged code, so get the exact name and field names from the user or from the org
  (`sf sobject describe --sobject <Name>__dlm`).
- **`queryReturnField` must hold a value that fits `fieldName`.** To fill a lookup such as
  `cpm__Contact__c`, the DMO field must contain a real Salesforce record id (typically the source
  record id mapped into the DMO). A DMO's own `ssot__Id__c` is not a Salesforce id. Confirm which DMO
  field carries the CRM id.
- **It is a callout** (`hasCallout() = true`). The engine commits progress and continues in a new
  queueable before a callout rule, and commits again after it. Each Data 360 rule therefore splits
  processing; keep the number of them small, and avoid `guidedReview` strategies on high-volume PSP
  flows.
- `INSTALLMENT_CLOSED_STATUS` and `RecordTypeId` criteria are meaningless on a DMO — filter on DMO
  fields with `mappingType: "value"` or `"field"` like any query.
- Data 360 data is only as fresh as its last ingestion / identity-resolution run. Do not rely on it
  for records created moments earlier in the same ruleset (e.g. by `createContact`).

### `findDuplicates`
Runs Salesforce Duplicate Management against an in-memory record built from `fieldMapping`; nothing
is inserted. `fieldName` must be `reference`. Same `multipleResultsStrategy` /
`singleResultStrategy` / `multipleResultsFieldsToDisplay` keys as `query`, but **the default differs**:
an absent `multipleResultsStrategy` means `takeFirst` here (it means guided review on `query`). Set it
explicitly unless you really want the first duplicate attached silently. If no active duplicate
rule applies it skips with "No active duplicate rules". Standard use: run it on `Contact__c` /
`Account__c` before a create rule.

### `createRecord` / `updateRecord`
Generic DML on the record referenced by `fieldName`. `fieldType` **must** be `reference`, and the
lookup must resolve to exactly one object, or the rule throws. `updateRecord` only queries and
touches the fields you map. `createRecord` supports `upsertField` (an external-id field) to dedupe.
Do not use these for Contact / Installment / Payment Profile — the dedicated types below exist and
the setup UI hides the generic ones for those fields.

### `createContact`
`fieldMapping` against `Contact`, plus `upsertField` (an external-id field on Contact) to dedupe
instead of always inserting. `AccountId` is always set from the transaction's `Account__c`, mapped
or not.

### `createPaymentProfile`
`fieldMapping` against `Payment_Profile__c`. Populated automatically regardless of the mapping:
`Contact__c`, `Account__c`, `Active__c = true`, and (from `Transaction__c`) `BIC_Code__c`,
`Bank_Account__c`, `City__c`, `Country__c`, `Holder_Name__c`, `IBAN__c`, `Street__c`, `Zipcode__c`;
from an Inbound Report, `Holder_Name__c` only. Always upserts on `Unique_Identifier__c` — the common
`upsertField` key is ignored. A `RecordTypeId` mapping takes a RecordType key such as `cpm.IBAN`, not
an id.

### `createInstallment`
`fieldMapping` against `Installment__c`, plus `upsertField`. Set automatically regardless of the
mapping: `Account__c` / `Contact__c` / `Payment_Profile__c` from the transaction, `Amount__c` and
`Amount_Open__c` from the amount, the three date fields from the transaction date, `CurrencyIsoCode`,
`Status__c = "New"`, `RecordTypeId` = `Payable` for a Debit transaction else `Receivable`, and (from
`Transaction__c`) `Originating_Campaign__c`, `Processor__c`, `Target__c`, `Collection_Count__c = 0`,
`Custom_Mandate_Id__c`, `Custom_Payment_Reference__c`, `Generated_Payment_Reference__c`,
`Last_ReasonCode_Received__c`, `Mandatory_Payment__c = false`, `Payment_Transaction_Id__c`. So the
mapping usually only needs `Payment_Method__c`, `Payment_Processor__c`, campaign/designation fields
and any custom fields.

Note the wide implicit dependency set (`ordering.md` §2) — this rule is the usual cycle culprit.

### `updateInstallment`
`fieldMapping` against `Installment__c`. Copies `Campaign__c` → `Originating_Campaign__c` when
populated — **Transaction source only**; on an Inbound Report you must map
`cpm__Originating_Campaign__c` explicitly. Auto-skip permanently off. Declares only `Campaign__c` as a dependency, which makes it a
safe way to touch an installment late in the pipeline.

### `createCampaignMember` / `updateCampaignMember`
Inbound Report only, on the text field `cpm__Campaign_Member_Id__c` (Salesforce allows no
CampaignMember lookup). `createCampaignMember` skips when the field is already set;
`updateCampaignMember` skips when it is empty. `fieldMapping` against `CampaignMember`.

### `promptTemplate` (Prompt Template — Prompt Builder)
Runs a Salesforce **Prompt Builder** prompt template against the record being matched and writes the
generated text into `fieldName`.

| Key | Req | Notes |
|---|---|---|
| `promptTemplateName` | yes | API name (DeveloperName) of a Flex prompt template, e.g. `Extract_Payment_Reference`. Listed in the UI picker; from the CLI: `sf org list metadata --metadata-type GenAiPromptTemplate`. |
| `promptTemplateInputs` | yes in practice | Array with **one** fixed entry: `{ "id": "record", "name": "<input name>", "inputSourceType": "object", "recordContextField": "THIS_RECORD" }`. `name` must equal the template's input API name (the UI defaults it to `Transaction` or `InboundReport`); the rule sends it as `Input:<name>` → `{ id: <record id> }`. Blank names are skipped; with no named input the template gets no record. |

Behaviour:

- **Availability.** Only offered in the Setup UI when Agentforce is enabled (the
  `standard.AgentforceStudio` app exists), and it only generates when the **FinDock Agentforce
  package** (namespace `fdafs`) is installed — without it the rule logs "AgentForce for PaymentHub not
  installed" and ends with no result. The prompt template itself must exist in the org and be active.
  Ask before using it.
- **Output.** A blank response → "done, no result" (the field stays empty, so the next rung of the
  ladder runs). Otherwise the raw text is written to `fieldName`, coerced by `fieldType`. Target a
  `string` / `textarea` field and let a later `normalize`, `regexp` or `query` rule use it; writing
  straight into a `reference`, `picklist`, `date` or `currency` field only works if the template is
  guaranteed to return exactly a valid value. Auto-skip applies: it does not run when `fieldName`
  is already filled. There is no guided-review section and no `fieldMapping`.
- **Ordering — the main trap.** Its dependencies are its `entryCriteria` only. The template reads the
  record from the database by id, and those reads are invisible to the order calculator. With
  `preferredOrder` 1 and no entry criteria, it is scheduled at the very start. If the template needs
  fields that earlier rules fill (e.g. `cpm__Contact__c`), add an entry criterion `notEquals ""` on
  that field (it orders *and* gates the rule), or pin it with `forcedExecuteAfterRule`.
- **It is a callout**, same as `dataCloudQuery`: progress is committed before it, so the template sees
  everything earlier rules wrote, and processing continues in a new job. One LLM call per record that
  reaches it, billed in Flex Credits per 2,000-token block by model category, sandboxes included
  (see the prompt template builder's `references/cost.md`). Use it for the long tail that regex cannot handle, not as the
  first rung on high-volume files.
- **Non-deterministic.** Treat its output as a *suggestion*: follow it with a query that must still
  find a real record, and keep a guided review rung behind it. Say in `userGuidance` that a value may
  come from AI.
- The prompt response and template name are written to the Guided Matching log
  (`promptResponse`, `promptTemplateName`), which helps when debugging a template.

Typical uses: pull a payment / invoice reference out of messy free-text remittance info; classify a
transaction into a picklist-like category written to a text field; summarise the raw payload for the
reviewer.

### `manualInput` (Guided Review)
| Key | Req | Notes |
|---|---|---|
| `guidedReviewType` | no | `field` (default — edit the field directly) \| `search` \| `contactAccountSearch`. |
| `referencedObject` | yes for `search` / `contactAccountSearch` | SObject to search. |
| `guidedReviewSearchFieldsToDisplay` | no | Result columns. |
| `guidedReviewAccountSearchFieldsToDisplay` | no | Account columns for `contactAccountSearch`. |
| `prefillSearchBoxTransactionField` | no | Prefills the search box. **Creates a dependency.** |
| `searchCriteria` / `accountSearchCriteria` | no | `{ fieldName, fieldType, comparisonOperator, value }`. Only `notEquals` is distinguished; every other operator becomes `=`. |
| `userGuidance` | strongly recommended | What the reviewer should do. |
| `allowSkip` | no | |

`contactAccountSearch` additionally skips if `Account__c` is already set, and writes an Account
result straight to `Account__c`.

Placement: a `manualInput` writing the same field as your automatic rules is the natural last rung of
a ladder — it is chained after them automatically. If it has no `entryCriteria` and no earlier rule
writes its field, it has zero dependencies and will be scheduled *early*; pin it with
`forcedExecuteAfterRule` in that case.

Caution for PSP notification and PaymentIntent reports: a human pause can blow the PSP's
capture window. Prefer `takeFirst` there.

### `processInstallment` — the terminal rule for reconciliation
`id` must be `PROCINS`. `fieldName` is `cpm__Installment__c`, `fieldType` `reference`.

| Key | Values | Notes |
|---|---|---|
| `overpaidInstallmentHandlingStrategy` | `bookAllOnFirst` (default) \| `bookRemainderOnNext` \| `leaveRemainder` | Unrecognised values fall back silently. |
| `guidedReviewStrategyAlways` | bool | Always review non-batch transactions. |
| `guidedReviewStrategyAlwaysBatch` | bool | Always review batch/group transactions. |
| `guidedReviewStrategyMultipleInstallmentsIdentified` | bool | `Multiple_Installment_Ids__c` is populated. |
| `guidedReviewStrategyMultipleInstallmentsMatched` | bool | More than one installment change computed. |
| `guidedReviewStrategyNotAllIdentifiedInstallmentsMatched` | bool | Identified count ≠ matched count. |
| `guidedReviewStrategyOverpaid` | bool | |
| `guidedReviewStrategyPartiallyPaid` | bool | |
| `userGuidance` | string | Shown when it lands in review. |

Sensible default: straight through when exactly one open installment matched; review on
multiple-matched, overpaid and partially-paid.

### `processPaymentIntent`
Inbound Report, `Report_Type__c = PaymentIntent`. Optional `primaryRelation` (`Contact` / `Account`),
only consulted when the report carries both. Throws if neither Account nor Contact is set.

### `processRefund`
No rule-specific keys; branches on the Inbound Report's own `Report_Type__c`.

### `apex`
| Key | Req | Notes |
|---|---|---|
| `logicClass` | yes | Fully-qualified class implementing `ApexGuidedMatchingRuleLogic`. |

Runs as late as tie-breaking allows. Guided review save-and-continue is not implemented for it. Its
ordering dependencies come from the class's own `getUsedFields()`, so they are invisible in the JSON.
A missing or unresolvable `logicClass` throws inside the order calculator — the Setup UI cannot
compute a plan at all — so deploy the Apex class *before* adding the rule.

### `sendMessage`
| Key | Req | Notes |
|---|---|---|
| `handler` | yes | Messages handler key. Always treated as a callout, which splits the batch. |

### `guaranteedOrdering` / `handleNotification`
No configurable keys; they delegate to platform / PSP logic and in practice only reach a ruleset via
FinDock-managed blocks. Include them only when the user explicitly asks.

### `forwardToSource`
Never write it. It is injected at runtime and stripped on save.
