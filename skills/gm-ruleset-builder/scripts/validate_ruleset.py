#!/usr/bin/env python3
"""
validate_ruleset.py - validate a FinDock Guided Matching ruleset before it goes
into Guided_Matching_Setup__c.Rules__c.

It re-implements GuidedMatchingRuleOrderCalculator.calculate() from the FinDock
codebase, so it catches the failure that actually blocks a save:

    "The system has been unable to calculate a full rule execution plan.
     This is almost certainly because of a cycle in rule dependencies."

and prints both orders that matter:
  * ARRAY order   - what the engine actually executes (the handler walks Rules__c in order).
  * CALCULATED    - what the Guided Matching Setup UI will re-sort the array to the first
                    time someone opens and saves it.
If those differ, the ruleset will behave differently after the first UI edit.

Usage:
    python3 validate_ruleset.py ruleset.json [--object transaction|inbound_report]
    cat ruleset.json | python3 validate_ruleset.py --object inbound_report
    python3 validate_ruleset.py ruleset.json --allow-managed   # skip unmanaged policy checks

Exit 0 = valid, 1 = errors found.
"""

import argparse
import json
import re
import sys

# ---------------------------------------------------------------------------
# Registry - GuidedMatchingFactory.GUIDED_MATCHING_RULE_TYPES (26 types)
# ---------------------------------------------------------------------------

RULE_TYPES = {
    "constant", "manualInput", "regexp", "query", "keywordSearch",
    "createRecord", "updateRecord", "createContact", "createPaymentProfile",
    "createInstallment", "updateInstallment", "createCampaignMember",
    "updateCampaignMember", "normalize", "findDuplicates", "fixedWidthExtract",
    "apex", "sendMessage", "guaranteedOrdering", "handleNotification",
    "processRefund", "processPaymentIntent", "processInstallment", "forwardToSource",
    "dataCloudQuery", "promptTemplate",
}
# Only offered when the org has the feature (GuidedMatchingSetupController.getRuleTypeSetupDefinitions):
# dataCloudQuery needs Data 360 (AppDefinition standard.Audience360), promptTemplate needs Agentforce
# (AppDefinition standard.AgentforceStudio) plus the FinDock Agentforce package (namespace fdafs).
ORG_GATED_TYPES = {
    "dataCloudQuery": "Data 360 (Data Cloud) is provisioned in the org",
    "promptTemplate": "Agentforce is enabled and the FinDock Agentforce package (fdafs) is installed",
}
# Pseudo-type: expands to a FinDock-managed block. Rejected unless --allow-managed.
MANAGED_PSEUDO_TYPE = "managedRuleSet"

TERMINAL_TYPES = {"processInstallment", "processPaymentIntent", "processRefund", "handleNotification"}

DML_TYPES = {"createRecord", "updateRecord", "createContact", "createPaymentProfile",
             "createInstallment", "updateInstallment", "createCampaignMember",
             "updateCampaignMember"}

REFERENCE_ONLY_TYPES = {"createRecord", "updateRecord", "findDuplicates"}

# getJobOrderIndex() / getPreferredOrder() - drive tie-breaking in determineNextRule()
JOB_ORDER_INDEX = {"createPaymentProfile": 2, "createInstallment": 3,
                   "updateInstallment": 4, "createCampaignMember": 4,
                   "updateCampaignMember": 4, "processInstallment": 5}
PREFERRED_ORDER = {"constant": 1, "findDuplicates": 1, "guaranteedOrdering": 1,
                   "handleNotification": 1, "processPaymentIntent": 1, "processRefund": 1,
                   "sendMessage": 1, "regexp": 2, "normalize": 2, "fixedWidthExtract": 2,
                   "keywordSearch": 2, "query": 3, "dataCloudQuery": 3, "promptTemplate": 1,
                   "manualInput": 4, "updateRecord": 5,
                   "createContact": 5, "createRecord": 5, "createPaymentProfile": 6,
                   "createInstallment": 7, "updateInstallment": 7,
                   "createCampaignMember": 7, "updateCampaignMember": 7,
                   "processInstallment": 100, "forwardToSource": 101, "apex": 998}

FIELD_TYPES = {"string", "textarea", "picklist", "multipicklist", "reference", "boolean",
               "currency", "double", "percent", "integer", "date", "datetime", "time",
               "email", "phone", "url", "id", "encryptedstring", "address", "combobox"}

ENTRY_OPERATORS = {"equals", "notEquals", "startsWith", "greaterThan", "greaterThanOrEqual",
                   "lessThan", "lessThanOrEqual", "inPaymentIntent", "notInPaymentIntent"}
# QueryGuidedMatchingRule.OPERATOR_MAP keys (lower-cased lookup).
QUERY_OPERATOR_MAP_KEYS = {"equals", "notequals", "greaterthan", "lessthan",
                           "greaterthanorequal", "lessthanequal"}
PAYMENT_INTENT_VALUES = {"contact", "account", "contactId", "accountId", "paymentProfile",
                         "oneTimeId", "oneTimeOrRecurring"}

MULTI_RESULT_STRATEGIES = {"takeFirst", "noResult", "guidedReview", "takeAllInstallmentIds"}
SINGLE_RESULT_STRATEGIES = {"takeSingleResult", "guidedReview"}
GUIDED_REVIEW_TYPES = {"field", "search", "contactAccountSearch"}
CASE_STRATEGIES = {"toUpperCase", "toLowerCase"}
WHITESPACE_STRATEGIES = {"trim", "deleteWhitespace"}
OVERPAID_STRATEGIES = {"bookAllOnFirst", "bookRemainderOnNext", "leaveRemainder"}

REQUIRED_BY_TYPE = {
    "constant": ["constant"],
    "regexp": ["inputFieldName", "regExp", "regExpCapturingGroup"],
    "fixedWidthExtract": ["inputFieldName", "fixedWidthExtractStartPosition",
                          "fixedWidthExtractEndPosition"],
    "query": ["queryObject", "queryReturnField", "queryFirstWhereQueryObjectField",
              "queryFirstWhereTransactionField"],
    "keywordSearch": ["queryObject", "queryReturnField", "queryFirstWhereQueryObjectField",
                      "queryFirstWhereTransactionField"],
    "dataCloudQuery": ["queryObject", "queryReturnField", "queryFirstWhereQueryObjectField",
                       "queryFirstWhereTransactionField"],
    "promptTemplate": ["promptTemplateName"],
    "apex": ["logicClass"],
    "sendMessage": ["handler"],
}

ID_RE = re.compile(r"^[A-Za-z0-9]{6}-\d{8}$")


def bare(name):
    """Normalise a field API name for comparison: drop the namespace, casefold.

    Apex String == is case-insensitive, so FinDock forms an edge between
    cpm__End_To_End_Id__c and cpm__End_To_End_ID__c. So must we.
    """
    if not isinstance(name, str):
        return None
    n = name.strip()
    low = n.lower()
    if low.startswith("cpm__"):
        n = n[5:]
    return n.casefold()


# ---------------------------------------------------------------------------
# getFieldDependencies() per rule type - the read-set that builds the graph
# ---------------------------------------------------------------------------

def _entry_criteria_fields(rule):
    out = set()
    for c in rule.get("entryCriteria") or []:
        if isinstance(c, dict) and c.get("fieldName"):
            out.add(bare(c["fieldName"]))
    return out


def _field_mapping_sources(rule):
    out = set()
    fm = rule.get("fieldMapping") or {}
    if isinstance(fm, dict):
        for v in fm.values():
            if isinstance(v, dict) and v.get("type") == "field" and v.get("fieldName"):
                out.add(bare(v["fieldName"]))
    return out


def field_dependencies(rule, src):
    """src is 'trx' or 'inbound_report'. Mirrors getFieldDependencies() exactly."""
    t = rule.get("ruleType")
    trx = src == "trx"
    ir = src == "inbound_report"

    # updateInstallment does NOT call super() - it declares Campaign__c only.
    if t == "updateInstallment":
        return {"Campaign__c"}

    deps = _entry_criteria_fields(rule)

    if t in ("query", "keywordSearch", "dataCloudQuery"):
        if rule.get("queryFirstWhereTransactionField"):
            deps.add(bare(rule["queryFirstWhereTransactionField"]))
        for c in rule.get("queryCriteria") or []:
            if isinstance(c, dict) and c.get("mappingType") == "field" and c.get("value"):
                deps.add(bare(c["value"]))

    elif t in ("regexp", "fixedWidthExtract"):
        if rule.get("inputFieldName"):
            deps.add(bare(rule["inputFieldName"]))

    elif t == "manualInput":
        if rule.get("guidedReviewType") in ("search", "contactAccountSearch"):
            p = rule.get("prefillSearchBoxTransactionField")
            if isinstance(p, str) and p.strip():
                deps.add(bare(p))

    elif t == "findDuplicates":
        if ir:
            deps.add("Raw_Message__c")
        deps |= _field_mapping_sources(rule)

    elif t in DML_TYPES:
        deps |= _field_mapping_sources(rule)
        if ir:
            deps.add("Report_Type__c")
        if t == "createContact":
            deps.add("Account__c")
        elif t == "createPaymentProfile":
            deps |= {"Contact__c", "Account__c", "Account_Holder_Name__c"}
            if trx:
                deps |= {"IBAN__c", "BIC_Code__c", "City__c", "Country__c",
                         "Street__c", "PostalCode__c"}
        elif t == "createInstallment":
            deps |= {"Account__c", "Contact__c", "Amount__c", "Date__c", "Payment_Profile__c"}
            if trx:
                deps |= {"Campaign__c", "Processor__c", "Target__c", "Type__c",
                         "Account_Holder_name__c", "IBAN__c", "BIC_Code__c",
                         "Mandate_Reference__c", "Payment_Reference__c", "Value_Date__c",
                         "Reason_Code__c", "End_To_End_Id__c"}
            elif ir:
                deps.add("Debit_Credit_Type__c")

    elif t == "processInstallment":
        deps |= {"Amount__c", "Status__c", "Date__c", "Guided_Matching_Installment_Processed__c"}
        deps |= {"Type__c", "Reason_Code__c"} if trx else {"Debit_Credit_Type__c"}

    elif t == "processRefund":
        deps |= {"Raw_Message__c", "Payment_Intent_Id__c", "Event_Parameters__c",
                 "Account__c", "Contact__c", "Report_SubType__c"}

    elif t == "handleNotification":
        deps.add("Payment_Processor__c")

    elif t == "processPaymentIntent":
        deps |= {"Raw_Message__c", "Payment_Intent_Id__c", "Event_Parameters__c", "Account__c",
                 "Contact__c", "Payment_Profile__c", "Payment_Processor__c", "Campaign__c",
                 "Origin__c", "Report_SubType__c"}

    deps = {bare(d) for d in deps}
    deps.discard(None)
    deps.discard("")
    return deps


# ---------------------------------------------------------------------------
# Static checks
# ---------------------------------------------------------------------------

def static_checks(rules, src, allow_managed):
    errors, warnings = [], []

    def tag(i, r):
        return f"[{i}] {r.get('name') or r.get('ruleType') or '?'}"

    seen_ids = {}
    for i, r in enumerate(rules):
        if not isinstance(r, dict):
            errors.append(f"[{i}] Rule is not a JSON object.")
            continue
        t = r.get("ruleType")

        if t == MANAGED_PSEUDO_TYPE:
            if allow_managed:
                if not r.get("managedRuleSetName") or not r.get("package"):
                    errors.append(f"{tag(i, r)}: managedRuleSet needs both 'managedRuleSetName' and 'package'.")
                continue
            errors.append(
                f"{tag(i, r)}: ruleType 'managedRuleSet' pulls in a FinDock-maintained block. "
                "Every rule it expands to is flagged managed=true and becomes read-only, "
                "non-reorderable and non-deletable in the Guided Matching Setup UI. "
                "Write the rules out explicitly instead (or pass --allow-managed).")
            continue
        if t not in RULE_TYPES:
            errors.append(f"{tag(i, r)}: unknown ruleType {t!r}. "
                          f"Saving throws 'Rule type {t} unknown.'")
            continue

        # --- unmanaged policy ---
        if not allow_managed:
            if r.get("managed") in (True, "true"):
                errors.append(f"{tag(i, r)}: has \"managed\": true - the rule becomes read-only in the UI. Remove it.")
            for k in ("managedRuleSetName", "managedRuleSetPackage", "package", "lastInManagedRuleSet", "doFirst"):
                if k in r:
                    errors.append(f"{tag(i, r)}: remove '{k}' - it marks the rule as part of a managed rule set.")
        if t == "forwardToSource":
            errors.append(f"{tag(i, r)}: forwardToSource is injected at runtime and stripped on save. "
                          "Never put it in Rules__c.")

        # --- id ---
        rid = r.get("id")
        if not rid:
            errors.append(f"{tag(i, r)}: missing 'id'. The order calculator keys its output map by id; "
                          "a null id yields a blank seqNr and the save throws the cyclic-dependency error.")
        else:
            if rid in seen_ids:
                errors.append(f"{tag(i, r)}: duplicate id {rid!r} (also on rule [{seen_ids[rid]}]). "
                              "The Setup UI assigns the calculated seqNr to the first match only, so the "
                              "duplicate is left without one and Save stays disabled.")
            seen_ids[rid] = i
            if rid not in ("PROCINS", "FWDTOSRC") and not ID_RE.match(rid):
                warnings.append(f"{tag(i, r)}: id {rid!r} does not match FinDock's generated format "
                                "'AbC123-12345678' (6 alphanumerics, dash, 8 digits). Works, but looks hand-made.")

        # --- common required keys ---
        for k in ("name", "fieldName", "fieldType", "seqNr", "jobNr"):
            if not r.get(k):
                errors.append(f"{tag(i, r)}: missing required key '{k}'.")
        if r.get("fieldType") is not None and not isinstance(r.get("fieldType"), str):
            errors.append(f"{tag(i, r)}: fieldType must be a string, got {type(r['fieldType']).__name__}.")
        ft = str(r.get("fieldType") or "").lower()
        if ft and ft not in FIELD_TYPES:
            warnings.append(f"{tag(i, r)}: fieldType {r.get('fieldType')!r} is not a lower-cased "
                            "Schema.DisplayType value FinDock coerces on.")
        if isinstance(r.get("fieldType"), str) and r["fieldType"] != ft:
            warnings.append(f"{tag(i, r)}: fieldType should be lower case ({ft!r}).")
        if r.get("jobNr") not in (None, "1"):
            warnings.append(f"{tag(i, r)}: jobNr={r.get('jobNr')!r}. Multi-job chaining is disabled in the "
                            "codebase - processing stops at the job boundary and never resumes. Use \"1\".")

        # --- per-type required keys ---
        for k in REQUIRED_BY_TYPE.get(t, []):
            if r.get(k) in (None, ""):
                errors.append(f"{tag(i, r)}: {t} requires '{k}'.")

        # --- terminal ids ---
        if t == "processInstallment" and r.get("id") != "PROCINS":
            errors.append(f"{tag(i, r)}: processInstallment must use id \"PROCINS\" - that literal is how the "
                          "order calculator pins it second-to-last.")

        # --- type-specific ---
        if t in REFERENCE_ONLY_TYPES and ft != "reference":
            errors.append(f"{tag(i, r)}: {t} throws unless fieldType is 'reference'.")
        if t == "normalize" and ft not in ("string", "textarea"):
            warnings.append(f"{tag(i, r)}: normalize only transforms string/textarea fields; "
                            f"on {ft!r} it is a no-op.")
        if t == "apex":
            warnings.append(f"{tag(i, r)}: an apex rule's dependencies come from its logicClass's "
                            "getUsedFields(), which this checker cannot see - the real execution order "
                            "may differ. Also: an unresolvable logicClass makes the order calculator "
                            "throw, so deploy the class before saving the ruleset.")
        if t == "keywordSearch":
            if r.get("multipleResultsStrategy") or r.get("singleResultStrategy"):
                warnings.append(f"{tag(i, r)}: keywordSearch ignores multipleResultsStrategy / "
                                "singleResultStrategy - the first regex match always wins.")
            for c in r.get("queryCriteria") or []:
                if not isinstance(c, dict):
                    continue
                if c.get("value") == "INSTALLMENT_CLOSED_STATUS" or \
                        str(c.get("fieldName") or "").endswith("RecordTypeId"):
                    errors.append(
                        f"{tag(i, r)}: keywordSearch skips the first WHERE clause, but the "
                        "INSTALLMENT_CLOSED_STATUS and RecordTypeId branches still prepend ' and ', "
                        "producing 'WHERE  and ...' with no bind map. Every record fails at runtime. "
                        "Use a query rule, or drop this criterion.")
        if t == "dataCloudQuery":
            qo = str(r.get("queryObject") or "")
            if qo and not qo.endswith("__dlm"):
                errors.append(f"{tag(i, r)}: dataCloudQuery must query a Data 360 DMO - queryObject "
                              f"{qo!r} does not end in '__dlm'. The Setup UI rejects it. Use a query rule "
                              "for regular Salesforce objects.")
            for c in r.get("queryCriteria") or []:
                if isinstance(c, dict) and c.get("value") == "INSTALLMENT_CLOSED_STATUS":
                    warnings.append(f"{tag(i, r)}: INSTALLMENT_CLOSED_STATUS only makes sense on "
                                    "Installment__c, not on a DMO.")
        if t == "promptTemplate":
            inputs = r.get("promptTemplateInputs")
            if inputs is not None and not isinstance(inputs, list):
                errors.append(f"{tag(i, r)}: promptTemplateInputs must be an array.")
            elif not inputs or not any(isinstance(x, dict) and str(x.get("name") or "").strip()
                                       for x in inputs):
                warnings.append(f"{tag(i, r)}: no named promptTemplateInputs - the template is called "
                                "without the record. Add {\"id\": \"record\", \"name\": \"Transaction\" "
                                "(or \"InboundReport\"), \"inputSourceType\": \"object\", "
                                "\"recordContextField\": \"THIS_RECORD\"}, named like the template's input.")
            if ft not in ("string", "textarea"):
                warnings.append(f"{tag(i, r)}: promptTemplate writes the model's raw text into a "
                                f"{ft!r} field - it must return exactly a valid value (e.g. a bare 18-char Id "
                                "for a reference) or the write fails. Prefer a text field plus a later "
                                "query/regexp rule.")
            if not r.get("entryCriteria") and not r.get("forcedExecuteAfterRule"):
                warnings.append(f"{tag(i, r)}: promptTemplate has no dependencies (the fields the template "
                                "reads are invisible to the order calculator), so it is scheduled near the "
                                "start. Add an entryCriteria on a field an earlier rule writes, or "
                                "forcedExecuteAfterRule, to run it after that field is filled.")
        if t in ("query", "keywordSearch", "dataCloudQuery"):
            ms = r.get("multipleResultsStrategy")
            if ms is not None and ms not in MULTI_RESULT_STRATEGIES:
                warnings.append(f"{tag(i, r)}: multipleResultsStrategy {ms!r} is unrecognised - "
                                "anything unknown falls through to guidedReview.")
            ss = r.get("singleResultStrategy")
            if ss is not None and ss not in SINGLE_RESULT_STRATEGIES:
                warnings.append(f"{tag(i, r)}: singleResultStrategy {ss!r} unrecognised.")
            if ms == "guidedReview" and not r.get("multipleResultsFieldsToDisplay"):
                warnings.append(f"{tag(i, r)}: multipleResultsStrategy 'guidedReview' with no "
                                "multipleResultsFieldsToDisplay - the reviewer gets an empty table.")
            if ms == "takeAllInstallmentIds":
                warnings.append(f"{tag(i, r)}: takeAllInstallmentIds populates "
                                "cpm__Multiple_Installment_Ids__c, and every later rule writing "
                                "cpm__Installment__c is then auto-skipped. Put this rung last in the "
                                "installment ladder.")
            if r.get("queryOrderByField") and ms == "noResult":
                warnings.append(f"{tag(i, r)}: queryOrderByField has no effect with "
                                "multipleResultsStrategy 'noResult'.")
            for c in r.get("queryCriteria") or []:
                if not isinstance(c, dict):
                    continue
                op = (c.get("comparisonOperator") or "")
                if c.get("mappingType") == "field":
                    if op not in ENTRY_OPERATORS:
                        warnings.append(f"{tag(i, r)}: queryCriteria operator {op!r} unknown.")
                else:
                    if op.lower() == "lessthanorequal":
                        errors.append(f"{tag(i, r)}: queryCriteria comparisonOperator 'lessThanOrEqual' is a known "
                                      "FinDock bug on value-type criteria - OPERATOR_MAP has no such key and the "
                                      "generated SOQL silently degrades to '='. Use 'lessThan' or "
                                      "mappingType 'field'.")
                    elif op.lower() not in QUERY_OPERATOR_MAP_KEYS:
                        warnings.append(f"{tag(i, r)}: queryCriteria operator {op!r} is not in OPERATOR_MAP; "
                                        "the SOQL will fall back to '='.")
        if t == "manualInput":
            grt = r.get("guidedReviewType")
            if grt and grt not in GUIDED_REVIEW_TYPES:
                warnings.append(f"{tag(i, r)}: guidedReviewType {grt!r} unknown - renders a plain field input.")
            if grt in ("search", "contactAccountSearch") and not r.get("referencedObject"):
                errors.append(f"{tag(i, r)}: guidedReviewType {grt!r} requires 'referencedObject'.")
            if not r.get("userGuidance"):
                warnings.append(f"{tag(i, r)}: no userGuidance - the reviewer gets no instructions.")
        if t == "normalize":
            if r.get("caseStrategy") and r["caseStrategy"] not in CASE_STRATEGIES:
                warnings.append(f"{tag(i, r)}: caseStrategy {r['caseStrategy']!r} unknown - no-op.")
            if r.get("whitespaceStrategy") and r["whitespaceStrategy"] not in WHITESPACE_STRATEGIES:
                warnings.append(f"{tag(i, r)}: whitespaceStrategy {r['whitespaceStrategy']!r} unknown - no-op.")
        if t == "processInstallment":
            ov = r.get("overpaidInstallmentHandlingStrategy")
            if ov and ov not in OVERPAID_STRATEGIES:
                warnings.append(f"{tag(i, r)}: overpaidInstallmentHandlingStrategy {ov!r} unknown - "
                                "silently falls back to bookAllOnFirst.")
        if t == "regexp":
            try:
                re.compile(r.get("regExp") or "")
            except re.error as e:
                warnings.append(f"{tag(i, r)}: regExp may be invalid ({e}). Note FinDock uses Java regex, "
                                "so this is only a rough check.")

        # --- entry criteria ---
        for c in r.get("entryCriteria") or []:
            if not isinstance(c, dict):
                errors.append(f"{tag(i, r)}: entryCriteria entry is not an object.")
                continue
            if "mappingType" in c:
                warnings.append(f"{tag(i, r)}: entryCriteria has no 'mappingType' concept - it is ignored. "
                                "Only queryCriteria supports it.")
            op = c.get("comparisonOperator")
            if op not in ENTRY_OPERATORS:
                errors.append(f"{tag(i, r)}: entryCriteria comparisonOperator {op!r} is not one of "
                              f"{sorted(ENTRY_OPERATORS)}.")
            if op in ("inPaymentIntent", "notInPaymentIntent") and c.get("value") not in PAYMENT_INTENT_VALUES:
                warnings.append(f"{tag(i, r)}: {op} value must be one of {sorted(PAYMENT_INTENT_VALUES)}.")
            if bare(c.get("fieldName")) == bare(r.get("fieldName")):
                errors.append(
                    f"{tag(i, r)}: entryCriteria on its own output field {c.get('fieldName')!r}. "
                    "The rule becomes its own dependency -> cyclic-dependency error on save. "
                    "It is also redundant: FinDock already skips any rule whose output field is non-blank.")

        # --- redundant empty-check hint ---
        for k in ("emptyEntryCriteriumDisabled", "entryCriteriumDisabled"):
            if r.get(k) is True:
                errors.append(f"{tag(i, r)}: {k} must be the string \"true\" - Apex compares it to a "
                              "string literal, so a JSON boolean is silently ignored.")
        if r.get("emptyEntryCriteriumDisabled") == "true" and t not in ("apex", "constant"):
            warnings.append(f"{tag(i, r)}: emptyEntryCriteriumDisabled='true' turns off the automatic "
                            "skip-if-already-filled. The rule will re-run and overwrite earlier matches.")

    # --- ruleset-level ---
    terminals = [r for r in rules if isinstance(r, dict) and r.get("ruleType") in TERMINAL_TYPES]
    if not terminals:
        errors.append("No terminal rule. A reconciliation ruleset needs processInstallment "
                      "(or processPaymentIntent / processRefund / handleNotification).")
    elif len(terminals) > 1:
        warnings.append(f"{len(terminals)} terminal rules found: "
                        f"{', '.join(t.get('ruleType') for t in terminals)}. Usually there is exactly one.")
    if terminals and rules and rules[-1] is not terminals[-1]:
        warnings.append("The terminal rule is not last in the array. processInstallment is forced "
                        "second-to-last regardless, but the Setup UI assumes the last array element "
                        "is Process Installment when inserting new rules.")
    return errors, warnings


# ---------------------------------------------------------------------------
# Order simulation - GuidedMatchingRuleOrderCalculator.calculate()
# ---------------------------------------------------------------------------

def determine_next_rule(candidates):
    """Faithful port of GuidedMatchingRuleOrderCalculator.determineNextRule().

    Note the quirk we deliberately reproduce: lowest_po is NOT reset when the
    job-order-index branch wins, so the preferred-order threshold can be
    inherited from a rule with a different job index.
    """
    if not candidates:
        return None
    chosen = candidates[0]
    lowest_joi = JOB_ORDER_INDEX.get(chosen.get("ruleType"), 1)
    lowest_po = PREFERRED_ORDER.get(chosen.get("ruleType"), 1)
    for r in candidates:
        joi = JOB_ORDER_INDEX.get(r.get("ruleType"), 1)
        po = PREFERRED_ORDER.get(r.get("ruleType"), 1)
        if joi < lowest_joi:
            chosen = r
            lowest_joi = joi
        elif joi == lowest_joi and po < lowest_po:
            chosen = r
            lowest_po = po
    return chosen


def simulate_order(rules, src):
    """Returns (ordered, stuck, edges). ordered = list of (seqNr, rule)."""
    orderable, procins, fwd = [], None, None
    for r in rules:
        if not isinstance(r, dict):
            continue
        if r.get("id") == "PROCINS":
            procins = r
        elif r.get("id") == "FWDTOSRC":
            fwd = r
        elif r.get("ruleType") == MANAGED_PSEUDO_TYPE or r.get("managed") in (True, "true"):
            orderable.append(r)  # approximation: treat a managed block as one opaque node
        else:
            orderable.append(r)

    idx = {id(r): i for i, r in enumerate(orderable)}
    deps = {id(r): set() for r in orderable}
    edges = {}
    last_rule_for_field = {}

    for r in orderable:
        d = set()
        wf = bare(r.get("fieldName"))
        prev = last_rule_for_field.get(wf)
        if prev is not None:
            d.add(id(prev))
        read = field_dependencies(r, src)
        for dep_field in read:
            for r2 in orderable:
                if bare(r2.get("fieldName")) == dep_field and r2.get("forcedExecuteAfterRule") is None:
                    d.add(id(r2))
        deps[id(r)] = d
        edges[id(r)] = read
        if r.get("forcedExecuteAfterRule") is None:
            last_rule_for_field[wf] = r

    to_order = {id(r): set(deps[id(r)]) for r in orderable}
    by_id = {id(r): r for r in orderable}
    ordered_ids, ordered = set(), []
    seq = 1
    while True:
        nxt = None
        for r in orderable:
            if id(r) not in to_order:
                continue
            far = r.get("forcedExecuteAfterRule")
            if far is not None and far in ordered_ids:
                nxt = r
                break
        if nxt is None:
            candidates = [r for r in orderable
                          if id(r) in to_order
                          and r.get("forcedExecuteAfterRule") is None and not to_order[id(r)]]
            nxt = determine_next_rule(candidates)
        if nxt is None:
            break
        ordered_ids.add(nxt.get("id"))
        ordered.append((seq, nxt))
        seq += 1
        del to_order[id(nxt)]
        for k in to_order:
            to_order[k].discard(id(nxt))

    if procins is not None:
        ordered.append((seq, procins))
        seq += 1
    if fwd is not None:
        ordered.append((seq, fwd))

    stuck = [by_id[k] for k in to_order]
    return ordered, stuck, deps, by_id


def explain_stuck(stuck, deps, by_id, src):
    lines = []
    stuck_ids = {id(r) for r in stuck}
    for r in stuck:
        far = r.get("forcedExecuteAfterRule")
        unmet = [by_id[k] for k in deps[id(r)] if k in stuck_ids]
        why = []
        if far is not None:
            why.append(f"waits on forcedExecuteAfterRule={far!r} which never gets ordered")
        for u in unmet:
            if id(u) == id(r):
                why.append(f"reads its own output field {r.get('fieldName')!r}")
            else:
                reads_it = bare(u.get("fieldName")) in field_dependencies(r, src)
                why.append(f"waits on '{u.get('name')}', which writes {u.get('fieldName')}"
                           + (" (read by this rule)" if reads_it else " (same output field)"))
        lines.append(f"  - '{r.get('name')}' [{r.get('ruleType')} -> {r.get('fieldName')}]: "
                     + ("; ".join(why) if why else "unreachable"))
    return lines


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", help="ruleset JSON file (default: stdin)")
    ap.add_argument("--object", default="transaction",
                    choices=["transaction", "trx", "inbound_report", "inboundreport", "ir"],
                    help="which source object the setup targets (default: transaction)")
    ap.add_argument("--allow-managed", action="store_true",
                    help="permit managedRuleSet entries and managed=true rules")
    ap.add_argument("--quiet", action="store_true", help="suppress the execution-order dump")
    args = ap.parse_args()

    src = "trx" if args.object in ("transaction", "trx") else "inbound_report"
    raw = open(args.path).read() if args.path else sys.stdin.read()
    try:
        rules = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"INVALID: not parseable JSON - {e}")
        sys.exit(1)
    if not isinstance(rules, list):
        print("INVALID: Rules__c must be a JSON array of rule objects.")
        sys.exit(1)
    if not rules:
        print("INVALID: empty ruleset.")
        sys.exit(1)

    errors, warnings = static_checks(rules, src, args.allow_managed)
    ordered, stuck, deps, by_id = simulate_order(rules, src)

    if stuck:
        errors.append(
            "CYCLE - the order calculator cannot place "
            f"{len(stuck)} rule(s). Saving throws: 'Could not save Guided Matching setup record "
            "because the system was not able to calculate a full rule execution plan. This is almost "
            "certainly because of a cycle in rule dependencies.'")
        errors.extend(explain_stuck(stuck, deps, by_id, src))

    # Runtime order == array order. The Setup UI re-sorts to the calculated order on save.
    array_ids = [r.get("id") for r in rules if isinstance(r, dict) and r.get("id") != "FWDTOSRC"]
    calc_ids = [r.get("id") for _, r in ordered if r.get("id") != "FWDTOSRC"]
    if not stuck and array_ids != calc_ids:
        warnings.append(
            "Array order and calculated order differ. The engine runs the array as written, but the "
            "Guided Matching Setup UI will re-sort it to the calculated order the first time anyone "
            "opens and saves this setup. Reorder the array to match, or accept the change.")

    if not args.quiet and ordered:
        print(f"Array order = runtime order ({args.object}):")
        for n, r in enumerate((r for r in rules if isinstance(r, dict)), 1):
            if r.get("ruleType") == MANAGED_PSEUDO_TYPE:
                print(f"  {n:>3}. {'managedRuleSet':<22} {'(managed block)':<38} "
                      f"{r.get('managedRuleSetName')} @ {r.get('package')}")
                continue
            print(f"  {n:>3}. {str(r.get('ruleType')):<22} {str(r.get('fieldName')):<38} {r.get('name')}")
        print()
        print(f"Calculated order (what the Setup UI re-sorts to):")
        for seq, r in ordered:
            far = r.get("forcedExecuteAfterRule")
            suffix = f"   (forced after {far})" if far else ""
            if r.get("ruleType") == MANAGED_PSEUDO_TYPE:
                print(f"  {seq:>3}. {'managedRuleSet':<22} {'(managed block)':<38} "
                      f"{r.get('managedRuleSetName')} @ {r.get('package')}")
                continue
            print(f"  {seq:>3}. {str(r.get('ruleType')):<22} {str(r.get('fieldName')):<38} "
                  f"{r.get('name')}{suffix}")
        print()

    gated = sorted({r.get("ruleType") for r in rules
                    if isinstance(r, dict) and r.get("ruleType") in ORG_GATED_TYPES})
    for t in gated:
        print(f"NOTE   {t} only works when {ORG_GATED_TYPES[t]}. Confirm with the user before handing over.")
    for w in warnings:
        print(f"WARN   {w}")
    for e in errors:
        print(f"ERROR  {e}")

    if errors:
        print(f"\nINVALID: {len(errors)} error(s), {len(warnings)} warning(s).")
        sys.exit(1)
    managed_note = ""
    if args.allow_managed:
        n = sum(1 for r in rules if isinstance(r, dict)
                and (r.get("ruleType") == MANAGED_PSEUDO_TYPE or r.get("managed") in (True, "true")))
        managed_note = (f" {n} managed entr{'y' if n == 1 else 'ies'} present (read-only in the UI; "
                        "order simulated as one opaque node each)." if n else " all unmanaged.")
    else:
        managed_note = " all unmanaged."
    print(f"VALID: {len(rules)} rules, no cycles,{managed_note} {len(warnings)} warning(s).")
    sys.exit(0)


if __name__ == "__main__":
    main()
