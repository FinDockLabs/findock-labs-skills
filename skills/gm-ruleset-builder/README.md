# gm-ruleset-builder

Builds or edits a FinDock **Guided Matching** ruleset — the JSON array stored in `Guided_Matching_Setup__c.Rules__c` — by interviewing you about what should match to what, then emitting rules that stay fully unmanaged and editable. Covers both `Transaction__c` (bank files) and `Inbound_Report__c` (PSP notifications, PaymentIntents).

## What it does

Guided Matching runs an ordered list of rules against each incoming payment to extract raw data, look up the Installment it pays (plus Payment Profile, Contact, Account, Campaign), create what's missing, and process it. This skill turns a plain-language description of that ladder into a ruleset that saves and runs correctly:

- **Interviews first**: always asks whether the org has Data 360 and Agentforce (with the FinDock Agentforce package), then walks through source/destination, what arrives populated vs. what must be extracted, the primary match, multiple-match strategy, the fallback ladder, enrichment, create-if-missing, the human (Guided Review) fallback, and `processInstallment` behaviour — then restates the ladder as one numbered list for sign-off before writing any JSON.
- **Emits unmanaged rules only** — no `managedRuleSet`, no `"managed": true`; every rule stays editable, reorderable, and deletable in the Guided Matching Setup UI.
- **Respects the engine's two hard behaviours** — array order *is* execution order (the Setup UI re-sorts by a dependency graph and refuses to save on a cycle), and FinDock auto-skips a rule whose output field is already filled (which is what makes a fallback ladder work).
- **Supports the org-gated rule types**: `dataCloudQuery` (Data360 Query Rule, queries a Data 360 DMO) and `promptTemplate` (runs a Prompt Builder template and writes the answer to a field). They are used only when you confirm your org has the feature.
- **Reads from your org**: with the Salesforce connector or the `sf` CLI it pulls existing Guided Matching Setups, field metadata, picklist values, DMO fields and prompt template names. It only reads; nothing is written back unless you explicitly ask.
- **Validates before handover** — a bundled Python script re-implements `GuidedMatchingRuleOrderCalculator`, catching the cyclic-dependency error before the org does and printing both the array order (what the engine runs) and the calculated order (what the Setup UI re-sorts to).

It also edits existing rulesets: paste the current `Rules__c` JSON and it returns the complete updated array, preserving every existing `id`, and it can explain "why won't this save" by running the validator and reading its cycle explanation.

## What to provide

The skill asks for anything missing, but the more you provide upfront the better:

- **Object** — `Transaction` (bank statement / return file) or `Inbound_Report` (PSP notification, PaymentIntent, webhook)
- **A real sample payload or line** — needed to write any regex or fixed-width extraction
- **The primary match** — which transaction field identifies the installment, which installment field it matches against, and what narrows it (open statuses, amount, due-date window, record type, campaign)
- **The fallback ladder, in order** — array position *is* the fallback order
- **Org-specific picklist values** — payment method and processor values vary per connector and can't be guessed
- **Org capabilities**: whether Data 360 and/or Agentforce + the FinDock Agentforce package are available
- **For edits**: the current `Rules__c` JSON, or a connected org it can read the JSON from

## Example triggers

- "Build a guided matching ruleset"
- "Match bank transactions to installments"
- "Reconcile camt.053 / MT940 / CODA / BACS returns"
- "Match on payment reference / IBAN / end-to-end id"
- "Create the installment if none is found" / "add a guided review fallback"
- "Set up guided matching for this PSP webhook"
- "Why does my ruleset say cyclic dependency"
- "Explain / debug / extend this Rules__c JSON"
- "Pull the guided matching rules from my org and review them"
- "Use Data 360 to find the contact" / "use a prompt template to extract the reference"

**Not for** ProcessingHub matching settings or the deprecated Manual Review feature.

## Output

- The agreed ladder as one short numbered list
- The ruleset JSON, ready to paste into `Rules__c` on the Guided Matching Setup record
- Where it goes and what to do next (open it once in FinDock Setup → Guided Matching to let the UI validate and re-sort), plus a plain note that the rules are unmanaged and therefore not updated by FinDock across releases

## Connectors

None required. The skill can run entirely from the conversation and the bundled validator (`scripts/validate_ruleset.py`, plain `python3`). Optional: the **Salesforce connector** or the **`sf` CLI** with an authenticated org, used read-only to fetch existing setups and metadata. Either way, you paste the result into your org yourself.

## Updating this skill

Edit `SKILL.md` to change the interview flow or the building rules; edit `references/` for the rule-type keys, field catalogue, ordering logic, or worked examples; edit `scripts/validate_ruleset.py` for validation. If the skill is also exposed through a Claude Code plugin in this repo, bump that plugin's version in its `plugin.json` and the matching entry in `.claude-plugin/marketplace.json`.
