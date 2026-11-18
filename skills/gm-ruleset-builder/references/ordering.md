# Rule order, cycles, and keeping rules unmanaged

Everything here is read off `GuidedMatchingRuleOrderCalculator.cls`, `GuidedMatchingFactory.cls`,
`GuidedMatchingRule.cls` and the `guidedMatchingSetup` / `gmRule` / `gmFieldRules` LWCs in the
FinDock PaymentHub codebase (March '26 build, namespace `cpm`).

---

## 1. Where order actually comes from

Two different things, and mixing them up is the main source of confusion.

**At runtime, execution order is the array order in `Rules__c`.**
`GuidedMatchingTransactionHandler` walks `rules[ruleNumber]` over the list `GuidedMatchingFactory.getRules()`
returns, and that list preserves the JSON order. Nothing sorts by `seqNr` at run time.

**In the Setup UI, the array gets re-sorted for you.** On every edit the LWC calls
`GuidedMatchingSetupController.calculateRuleExecutionOrder`, which runs
`GuidedMatchingRuleOrderCalculator`, writes the computed `seqNr`/`jobNr` back onto each rule, sorts
`this.rules` by `seqNr`, and posts that already-sorted array to `saveSetup`. If any rule comes back
without a `seqNr`, Save is disabled and the cyclic-dependency banner appears.

`saveSetup` itself does **not** reorder and does **not** cycle-check — it only calls
`finalizeRuleSetup` (collapse managed blocks, strip `FWDTOSRC`). So:

- **Pasting JSON straight into `cpm__Rules__c`** (Data Loader, dev console, deploy) skips the
  reorder *and* the cycle check entirely. Your array order is the execution order, verbatim.
- **The first time someone opens that setup in the Guided Matching UI and saves**, the calculator
  runs, the array is re-sorted into dependency order, and a cycle blocks the save.

Practical consequence: emit rules **in the order you want them to run**, and make sure the
dependency graph is acyclic and produces that same order. Otherwise the ruleset works today and
silently reshuffles — or refuses to save — the first time someone edits it in the UI. The bundled
validator prints both: your array order and the order the calculator would compute.

What you control:

| Lever | Effect |
|---|---|
| Array position | Runtime order, and the tie-break the calculator falls back to. Two rules writing the *same* field are also chained in array order (`lastRuleForFieldNames`). |
| Which fields a rule **reads** | Graph edges: the rule is ordered after every rule that writes one of those fields. |
| `forcedExecuteAfterRule` | Hard pin, and it removes the rule from the graph — see §4. |
| Rule type | Ties broken by `getJobOrderIndex()` then `getPreferredOrder()` (§6). |
| `seqNr` | Nothing. It is recalculated by the UI and ignored at runtime. Supply it anyway (it is required) and keep it consistent with array order. |

## 2. What counts as "reading a field"

`getFieldDependencies(sourceType)` per rule type. `trx` = the setup targets `Transaction__c`,
`ir` = `Inbound_Report__c`.

| Rule type | Reads |
|---|---|
| *all types (base)* | every `entryCriteria[].fieldName` |
| `query`, `keywordSearch`, `dataCloudQuery` | base + `queryFirstWhereTransactionField` + every `queryCriteria[]` where `mappingType == "field"` (its `value`) |
| `regexp`, `fixedWidthExtract` | base + `inputFieldName` |
| `manualInput` | base + `prefillSearchBoxTransactionField` (only when `guidedReviewType` is `search` / `contactAccountSearch`) |
| `createRecord`, `updateRecord`, `createContact`, `createPaymentProfile`, `createInstallment`, `createCampaignMember`, `updateCampaignMember` | base + every `fieldMapping` entry with `type == "field"` (its `fieldName`) + `Report_Type__c` when `ir` — **plus the implicit reads below** |
| `createContact` | + `Account__c` |
| `createPaymentProfile` | + `Contact__c`, `Account__c`, `Account_Holder_Name__c`; `trx` also + `IBAN__c`, `BIC_Code__c`, `City__c`, `Country__c`, `Street__c`, `PostalCode__c` |
| `createInstallment` | + `Account__c`, `Contact__c`, `Amount__c`, `Date__c`, `Payment_Profile__c`; `trx` also + `Campaign__c`, `Processor__c`, `Target__c`, `Type__c`, `Account_Holder_name__c`, `IBAN__c`, `BIC_Code__c`, `Mandate_Reference__c`, `Payment_Reference__c`, `Value_Date__c`, `Reason_Code__c`, `End_To_End_Id__c`; `ir` also + `Debit_Credit_Type__c` |
| `updateInstallment` | **`Campaign__c` only.** It does *not* call the base method — `entryCriteria` and `fieldMapping` are ignored for ordering, and `Installment__c` is deliberately commented out. |
| `findDuplicates` | base + `fieldMapping` field sources + `Raw_Message__c` when `ir` |
| `processInstallment` | `Amount__c`, `Status__c`, `Date__c`, `Guided_Matching_Installment_Processed__c`, plus `Type__c`+`Reason_Code__c` (`trx`) or `Debit_Credit_Type__c` (`ir`). `Installment__c` and the multi-installment fields are deliberately excluded. Moot in practice — `id: "PROCINS"` is pulled out of the graph. |
| `processPaymentIntent` | `Raw_Message__c`, `Payment_Intent_Id__c`, `Event_Parameters__c`, `Account__c`, `Contact__c`, `Payment_Profile__c`, `Payment_Processor__c`, `Campaign__c`, `Origin__c`, `Report_SubType__c` |
| `processRefund` | base + `Raw_Message__c`, `Payment_Intent_Id__c`, `Event_Parameters__c`, `Account__c`, `Contact__c`, `Report_SubType__c` |
| `handleNotification` | base + `Payment_Processor__c` |
| `apex` | base + whatever `logicClass.getUsedFields()` returns — unknowable from the JSON alone |
| `constant`, `normalize`, `sendMessage`, `guaranteedOrdering` | base only |
| `promptTemplate` | base only. The fields the template reads from the record are **not** declared, so add entry criteria or `forcedExecuteAfterRule` to place it after the rules it relies on. |

The **write** field is always `fieldName` — one output field per rule.

## 3. The three ways to deadlock

The calculator loops picking rules with zero unmet dependencies. When nothing is pickable it stops,
those rules never get a `seqNr`, and the save throws:

> Could not save Guided Matching setup record because the system was not able to calculate a full
> rule execution plan. This is almost certainly because of a cycle in rule dependencies.

(The Setup UI shows the client-side twin of this and disables Save.)

**(a) Self-dependency — by far the most common.** The dependency loop has no
"skip myself" guard, so a rule that reads its own `fieldName` becomes its own dependency. The usual
cause is an entry criterion like `{"fieldName": "cpm__Installment__c", "comparisonOperator": "equals", "value": ""}`
on a rule that writes `cpm__Installment__c`. It is also **unnecessary**: FinDock automatically skips
any rule whose output field is already non-blank (`meetsEntryCriteria`, the "is empty check"). That
auto-skip is exactly what makes a fallback ladder work — you never write empty-checks yourself.

Exceptions to the auto-skip, worth knowing: it is bypassed when `fieldType` is `boolean`, when
`fieldName` is `CurrencyIsoCode`, when `emptyEntryCriteriumDisabled` is the **string** `"true"`
(a JSON boolean does not match), for a `constant` rule writing `Status__c`, and permanently for
`updateRecord`, `updateInstallment`, `updateCampaignMember`, `normalize`, `forwardToSource`, and
every `process*` / `handleNotification` / `guaranteedOrdering` / `sendMessage` rule.

A second, less obvious skip: any rule writing `cpm__Installment__c` is skipped when
`cpm__Multiple_Installment_Ids__c` is non-blank. A `query` with
`multipleResultsStrategy: "takeAllInstallmentIds"` populates exactly that field, so it silently
disables every later rung of the installment ladder. Put that rung last.

**(b) Two-rule cycles between related records.** The classic ones:

- `query` "Contact from Payment Profile" (writes `Contact__c`, reads `Payment_Profile__c`)
  vs `createPaymentProfile` (writes `Payment_Profile__c`, implicitly reads `Contact__c`).
- `query` "Contact from Installment" (writes `Contact__c`, reads `Installment__c`)
  vs `createInstallment` (writes `Installment__c`, implicitly reads `Contact__c`).
- Any "enrich X from the installment" rule combined with `createInstallment`, because
  `createInstallment` implicitly reads `Account__c`, `Contact__c`, `Amount__c`, `Date__c` and
  `Payment_Profile__c`.

**Any ruleset that both enriches from a record and creates that record will cycle** unless you break
it. See §4.

**(c) Missing or duplicate `id`.** The calculator writes its result into a map keyed by rule id.

- **Missing id** → `getId()` returns the string `"null"` while the lookup uses a real `null`, so the
  rule never gets a `seqNr`. In the UI, Save is disabled with the cyclic-dependency banner even
  though there is no cycle.
- **Duplicate id** → the two rules collide in the map. In the UI, `findRuleById` matches only the
  first, so the second is left without a `seqNr` and Save stays disabled. (Through the Apex
  `reorderRules` path, no exception is thrown — both rules silently receive the same `seqNr`.)

Every rule needs a unique id. FinDock's generator produces `<6 alphanumerics>-<8 digits>`, e.g.
`Qa1Bc7-10000003`. `processInstallment` must use the literal `PROCINS`.

## 4. `forcedExecuteAfterRule` — the cycle breaker

Set it to another rule's `id`. Three things happen, and the second and third are the point:

1. The rule is scheduled as soon as its target has been ordered — the forced scan runs **before** the
   zero-dependency scan on every iteration, so a forced chain jumps the queue.
2. The rule is **excluded from being anyone else's dependency** (`rule2.getForcedExecuteAfterRuleId() == null`
   is required for a rule to be picked up as a dependency target).
3. The rule does **not** update `lastRuleForFieldNames`, so it does not chain with other rules writing
   the same field.

So pinning the enrichment rule breaks the enrich/create cycle: `createPaymentProfile` stops waiting
on "Contact from Payment Profile", while the forced-scan priority still guarantees the enrichment
runs immediately after the lookup it depends on. This is exactly what FinDock's own Tikkie ruleset
does. `references/examples/inbound-report-create-if-missing.json` shows the pattern.

Caveat: a chain of forced rules that never has its first target ordered will hang forever — the
validator reports it as a cycle, correctly.

## 5. Terminal rules

- `processInstallment` with `id: "PROCINS"` is lifted out of the graph and appended second-to-last,
  whatever its position. Use the literal id or you lose that guarantee.
- `forwardToSource` (`id: "FWDTOSRC"`) is **injected at runtime and stripped on save**. Never put it
  in `Rules__c`.
- `processPaymentIntent`, `processRefund`, `handleNotification` and `guaranteedOrdering` get no
  special treatment — they are ordered like any other rule.

## 6. Tie-breaking

Among rules with zero unmet dependencies, `determineNextRule` seeds on the **first candidate in
array order** and then scans: a strictly lower `getJobOrderIndex()` wins; a matching job index wins
on a strictly lower `getPreferredOrder()`. Note the quirk — `lowestPreferredOrder` is *not* reset
when the job-index branch fires, so the preferred-order threshold can be inherited from a rule with
a different job index. The upshot is that array order matters more than the tables below suggest.
Do not lean on the tie-break; express the order you want through array position and dependencies.

`jobOrderIndex` — default `1`; `createPaymentProfile` 2; `createInstallment` 3;
`updateInstallment` / `createCampaignMember` / `updateCampaignMember` 4; `processInstallment` 5.

`preferredOrder` — `constant`/`findDuplicates`/`processPaymentIntent`/`processRefund`/`sendMessage`/
`guaranteedOrdering`/`handleNotification`/`promptTemplate` 1; `regexp`/`normalize`/`fixedWidthExtract`/`keywordSearch` 2;
`query`/`dataCloudQuery` 3; `manualInput` 4; `updateRecord`/`createContact`/`createRecord` 5; `createPaymentProfile` 6;
`createInstallment`/`updateInstallment`/`createCampaignMember`/`updateCampaignMember` 7;
`processInstallment` 100; `apex` 998.

## 7. `jobNr` — always `"1"`

The calculator's job-increment line is commented out, and the handler's job-chaining block is
commented out too, so a second `jobNr` would simply stop processing at the boundary and never
resume. Always emit `"1"`.

## 8. Keeping every rule unmanaged

"Managed" is a per-rule flag, and it is what makes a rule **read-only, non-reorderable and
non-deletable** in the Guided Matching Setup UI (`gmRule.js`: `isNotOrderable` / `isNotDeletable`
are true when `rule.managed`; `guidedMatchingSetup.js`: `modalRuleIsNotChangeable` disables every
input in the edit modal). A managed rule also cannot be picked as a "Force Execute After Rule"
target unless it happens to be the last rule of its block.

Only two things set that flag:

1. **A `{"ruleType": "managedRuleSet", "managedRuleSetName": "...", "package": "..."}` entry.**
   `GuidedMatchingFactory.getRules()` expands it and calls `setManaged()` on *every* rule in the
   block. On save, `finalizeRuleSetup()` collapses the block back to the single reference, so any
   edits you made are discarded.
2. **Hand-writing `"managed": true`** on a rule (`isManaged()` just reads the key).

So: never emit a `managedRuleSet` entry, never emit `managed`, `managedRuleSetName`,
`managedRuleSetPackage`, `package`, `doFirst` or `lastInManagedRuleSet`. Write every rule out in full.

For reference, the blocks you are deliberately *not* referencing (all package `FinDock`, from
`CoreManagedRuleSetRepository`): `inboundReportStatusToMatched`, `guaranteedOrdering`,
`handleNotification`, `paymentIntentGetInstallmentByIds`, `paymentIntentGetRelationByIds`,
`postProcessPaymentIntent`, `TransactionInstallmentPaymentReferenceSearch`,
`TransactionFindPaymentProfileByIBAN`, `TransactionCreateIBANPaymentProfile`,
`TransactionGetRelationFromInstallment`, `TransactionGetPaymentProfileFromInstallmentWithSameIBAN`,
`TransactionGetRelationFromPaymentProfile`; plus
`FinDock_BankFeed` blocks and the Tikkie / Bollettino Postale blocks shipped by connector packages.
If the user wants one of those behaviours, reproduce it as explicit rules rather than referencing it.

One consequence to state honestly when handing over: unmanaged rules do **not** receive FinDock's
platform updates. A managed block gets fixed and reordered by FinDock across releases; your explicit
copy will not. That is the trade for editability.

Separately, and independent of `managed`: `processInstallment`, `forwardToSource`, `apex`,
`sendMessage`, `guaranteedOrdering`, `handleNotification`, `processRefund` and `processPaymentIntent`
carry `notOrderable` / `notDeletable` / `ruleTypeNotChangeable` at the *rule-type* level and are not
offered in the Add-Rule picker. Nothing can change that.
