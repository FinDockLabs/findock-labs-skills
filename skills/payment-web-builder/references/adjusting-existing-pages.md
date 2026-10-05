# Adjusting an Existing Payment Page

Use this when the intake mode question (Step 0, Question 0) was **Adjust an existing page**: the
customer already has a FinDock payment page, form, or Flow — most often one installed from the
FinDock Labs **payment-experiences-templates** unlocked packages — and wants it changed rather
than rebuilt. The build intake (Questions 1–8) is skipped; this file replaces it with a discovery
step, a change-request map, and an upgrade-safe editing recipe.

> Verify against the live templates repo before relying on a name below — the packages are
> versioned (`0.1.0-x`) and the templates evolve: https://github.com/FinDockLabs/payment-experiences-templates
> (`sfdx-project.json` lists the package names and aliases; each `sfdx-source/packages/*/README.md`
> documents its own knobs).

---

## Step A — Discover what is there (instead of the build intake)

Do not ask the user to describe their stack. Look, classify, then confirm in one question.

### A1. Where to look

| Host situation | How to discover |
|---|---|
| Org-aware host (Vibes, Claude Code / Codex / Cursor with `sf` CLI or a Salesforce MCP) | Ask the host to list installed packages and retrieve the candidate metadata: `sf package installed list -o <alias>` (look for the package names in the fingerprint table), then `sf project retrieve start -o <alias> -m Flow:Donation_Flow -m Flow:One_Screen_Donation_Flow -m Flow:Checkout_Flow -m LightningComponentBundle:paymentForm -m LightningComponentBundle:amountAndFrequency`. Only retrieve names that exist; missing members just error out, which is fine. |
| Local SFDX project / repo | Grep `force-app/` (or the project's package directories) for the artefact names in the fingerprint table, and for `cpm-pay-button`, `cpm:payButton`, `cpm-payment-method-selector`, `cpm:paymentMethodSelector`, `cpm.API_PaymentIntent_V2`. |
| Neither (user only has a site URL or a screenshot) | Ask for a link to the repo, or for the Flow/LWC name shown in Experience Builder. Do not guess. |

### A2. Fingerprint table — what each FinDock Labs package installs

All packages are **unlocked, no namespace** (components appear as `c:` / `c-`). Package names are
as installed in the org; folder names are from the repo.

| Package (as installed) | Repo folder | Flows | LWCs | Other artefacts |
|---|---|---|---|---|
| FinDock Experiences - Fundraising | `donation-fundraising` | `Donation_Flow` (multi-screen), `One_Screen_Donation_Flow`, `Contact_Assignment` (subflow) | shared: `amountAndFrequency` (+ `amountAndFrequencyConfig`), `currencyPicker` (+ `currencyPickerConfig`), `experienceProgressStages` | perm set `FinDockLabs_Donation_Flow_Guest_Access`, translations XLF |
| FinDock Experiences - Fundraising UK | `donation-fundraising-uk` | `Donation_Flow` (Gift Aid variant) | same shared LWCs | static resource `giftaid`, same guest perm set |
| FinDock Experiences - NPSP | `donation-npsp` | `Donation_Flow` (NPSP variant) | same shared LWCs | same guest perm set |
| FinDock Experiences - Checkout | `checkout` | `Checkout_Flow` | `paymentAmount` | perm set `FinDockLabs_Checkout_Flow_Guest_Access`, Custom Labels |
| FinDock Experiences - Donation Site | `donation-site` | — | — | Experience Bundle for a *Build Your Own (LWR)* site named `Donation Page`, CSP trusted site `FinDock_External`, static resources `findockAssets`, `favicon` |
| FinDock Experiences - Checkout Site | `checkout-site` | — | — | Experience Bundle for site `Checkout_Page1`, same CSP / static resources |
| *(pro-code, deployed from source; also published standalone as `FinDockLabs/experience-cloud-lwc`, which the docs' pro-code page links)* | `lwc-procode` | — | `paymentForm` (`c-payment-form`, exposed), `paymentSelector` (`c-payment-selector`), with `paymentMethodConfiguration.js`, `paymentFormLabels.js` | perm set `FinDockLabs_Payment_Components_Guest_Access`, Custom Labels, `npm run generate:config` script |

Compatibility rule from the repo README: the three donation variants share the same component
names and are **mutually exclusive — only one per org**. Checkout can coexist with one donation
variant.

### A3. Classify

| Found | Classification | Primary reference |
|---|---|---|
| A `Donation_Flow` / `One_Screen_Donation_Flow` / `Checkout_Flow` using `cpm:payButton` + `cpm:paymentMethodSelector` | **Flow template** (Experience Cloud, Route A, Flow-assembled) | `experience-cloud.md` → "Worked example — Flow assembling the managed components" |
| `c-payment-form` / `paymentMethodConfiguration.js` | **Pro-code LWC template** (Experience Cloud, Route A, LWC-assembled) | `experience-cloud.md` → "Worked example — custom LWC", `payment-method-selector-config.md` |
| A Flow or LWC above, exposed through a Lightning Out 2.0 app on an external site | **Embedded template** | `lightning-out.md` plus the row above for the inner form |
| `uiBundles/` + `sdk.fetch` to `/services/apexrest/…`, `Donation_Page_Setting` custom metadata | **Multi-Framework example** (`FinDockLabs/findock-multi-framework-react`) | `salesforce-multi-framework.md`; follow the example's own `AGENTS.md` |
| Hand-written Apex calling `cpm.API_PaymentIntent_V2` with a custom LWC | **Custom build** (Route B) | `on-platform-apex-lwc-flow.md` |
| A standalone site calling the REST API through a proxy | **Standalone build** | `authentication.md`, `one-time-payment.md` / `recurring-payment.md` |

### A4. Confirm, then ask what should change

One structured question (header `Found`): "I found *X* (classification + package/version). Is this
the page to change?" with the options *Yes*, *No, a different one* (ask for the name/path).
Then one more question (header `Change`): what should change — offer the four most likely items
from the change-request map below for that classification, and let "Other" catch the rest.

Skip the build intake Questions 1–8 entirely. Only ask a build question when the change itself
introduces something new — e.g. adding a recurring option to a one-time-only form reopens
Question 3 (frequency) for the new part, and adding payment methods reopens Question 7/8 (region
and methods) for the additions only.

---

## Step B — Change-request map

For each request: where the knob lives, what to touch, and which reference holds the rules. Names
below are from the current `Donation_Flow` and `lwc-procode` sources; re-check them in the
retrieved metadata before editing.

### Flow templates (`Donation_Flow`, `One_Screen_Donation_Flow`, `Checkout_Flow`)

| Request | Where the knob is | Reference |
|---|---|---|
| Change suggested / preset amounts | `c:amountAndFrequency` on the amount screen: `presetAmountsOneTime` (default `25,50,100,250,500,1000`), `presetAmountsRecurring` (`5,10,25,60,125,250`), `minAmount`. Checkout: `c:paymentAmount`. | `donation-page-structure.md` (amount step rules) |
| Change default or offered frequencies | `c:amountAndFrequency`: `showFrequencyToggle`, `defaultFrequency` (`oneTime`/`recurring`), `freq1Value`/`freq2Value`; the recurring frequency sent to FinDock is `cpm:payButton.frequencyRecurring` (template default `Monthly`), `startDateRecurring` defaults to `$Flow.CurrentDate`. | `recurring-payment.md` (allowed frequencies, `InitialPaymentOnRecurring`) |
| Add / remove payment methods or processors, change merchant account (target) | `cpm:paymentMethodSelector` on the pay screen — open the component in Flow Builder and edit its method/processor/target configuration. Nothing in code. | `payment-method-selector-config.md`, `payment-methods-catalogue.md` (is the method supported? is its extension installed?) |
| Change success / failure (thank-you) pages | `cpm:payButton` → `successUrl` / `failureUrl` (templates ship `https://www.example.com/...` placeholders). Point them at pages in the same site. | `experience-cloud.md` setup checklist |
| Change which Contact/Account the gift is attributed to | `Contact_Assignment` subflow (Fundraising / NPSP: Person Account vs Contact), `Pay_Button.account` input. | `on-platform-apex-lwc-flow.md` → Payer object; SKILL.md "Payer object" (NPC Person Accounts vs NPSP) |
| Add / remove Gift Tributes, cover-fees | Flow variables `Enable_Gift_Tributes` / `GiftTributesEnabled`, the `GiftTribute*` inputs on `cpm:payButton`, `CoverFees` + `CoverFeesDisplayText`. | — (Fundraising-specific; verify in docs MCP) |
| Add Gift Aid | Use the **Fundraising UK** variant (`donation-fundraising-uk`) instead of bolting it on; the variants are mutually exclusive, so this is a swap, not an addition. | `experience-cloud.md` → Templates |
| Add or change currency | `c:currencyPicker` on the amount screen; `currencyOneTime` / `currencyRecurring` on `cpm:payButton` read `currencyPicker.value`. | `parameters-and-enums.md` |
| Change copy / labels / translations | Flow display text and screen labels → Translation Workbench (Setup Component: Flow); shared LWC strings → Custom Labels + XLIFF import. Never hardcode strings in formulas. | templates README → "Localizing FinDock Payment Experiences" |
| Change page layout, branding, header/footer | Experience Builder (theme, branding set, page sections), not the Flow. Site templates: `donation-site` / `checkout-site` bundles. | `page-quality.md`, `donation-page-structure.md`, `accessibility.md` |
| Fewer / more steps (multi-screen ↔ single-screen) | Swap between `Donation_Flow` and `One_Screen_Donation_Flow` rather than restructuring screens; same component wiring. | `experience-cloud.md` → Worked example |
| Collect an extra field (phone, campaign, consent) | Add the screen input, map it in the `Assign_custom_*` assignments to the Installment / Recurring record or to the Contact in `Contact_Assignment`. | `required-fields-and-errors.md` |
| Move the page onto the customer's own website | Keep the Flow; wrap it in a thin LWC and expose it through Lightning Out 2.0. | `lightning-out.md` (1c–1f questions, setup checklist) |
| Payments fail for guests but work for admins | Not a page change — run the public-site prerequisite checklist (ProcessingHub connected, FinDock Payer group on the Guest User, template guest perm set, API access preference). | `experience-cloud.md` → REQUIRED for public sites |

### Pro-code LWC template (`c-payment-form`, `c-payment-selector`)

| Request | Where the knob is | Reference |
|---|---|---|
| Add / remove payment methods, set target, defaults | `paymentMethodConfiguration.js`. **Regenerate from the org** with the sibling skill `/generate-payment-config <orgAlias> [processor] [methods] [target="…"]` (Mode D) rather than hand-editing; then narrow or set `target`. | `generate-payment-config/SKILL.md`, `payment-method-selector-config.md` |
| Change amount, currency, frequency | `@api` defaults in `paymentForm.js`: `amount`, `defaultCurrency`, `allowedCurrencies`, `defaultFrequency`. Not exposed in Experience Builder. | lwc-procode README → Configuration Properties |
| Let the payer choose the amount | The template is a fixed-checkout model. Fork `paymentForm` or embed `c-payment-selector` in a custom LWC with your own amount input. | `experience-cloud.md` → Worked example — custom LWC |
| Change success / failure pages | `SuccessURL` / `FailureURL` are part of the PaymentIntent object the LWC passes to `cpm-pay-button` via `payment-intent` (docs: the custom LWC must hand the Pay Button a *complete* intent). In the Labs template that object is built in `_updatePaymentIntentContext()` in `paymentForm.js`, with `https://example.com/...` placeholders — replace them there (or lift them to `@api` properties on your fork). | `payment-method-selector-config.md` → Pay Button interface |
| Add a recurring frequency other than Monthly | Add a frequency property; the template sends `Recurring.Frequency: 'Monthly'` only. | `recurring-payment.md` |
| Show a parameter to the payer (e.g. `locale`, `description`) | The entry's `parameters[]` in `paymentMethodConfiguration.js`: `visibleToCustomer: true`, `displayLabel`, `required`. | `parameters-and-enums.md` |
| Labels / translations | `paymentFormLabels.js` + Custom Labels; `displayLabel` / `redirectInstruction` as `labels.<name>` references. | lwc-procode README → Localization |

### Multi-Framework example, custom builds, standalone builds

Follow the build-mode references for that surface (`salesforce-multi-framework.md`,
`on-platform-apex-lwc-flow.md`, `authentication.md`) — the change-request map above tells you
*which* FinDock rule applies (frequency, methods, payer object, URLs); the surface reference tells
you *how* it is wired there. For the Multi-Framework example, org-specific values live in the
`Donation_Page_Setting.Default` custom metadata record; change those before touching code.

---

## Step C — Upgrade-safe editing recipe (always)

The templates are **unlocked packages**. Metadata the package owns is overwritten on the next
package upgrade, and local edits to it block or conflict with that upgrade. The templates are
explicitly "meant to be customized" — do it on a copy:

1. **Flows**: in Flow Builder, *Save As → A New Flow* with a project-owned API name (e.g.
   `ACME_Donation_Flow`). Make every change on the copy. Keep the package Flow untouched and
   deactivated if no longer used. Re-point any `Contact_Assignment` subflow reference if you cloned
   that too.
2. **Shared LWCs** (`amountAndFrequency`, `currencyPicker`, `experienceProgressStages`,
   `paymentAmount`): prefer configuring them through their Flow inputs. If code must change, copy
   the bundle under a new name (`acmeAmountAndFrequency`) and swap the screen component in the
   cloned Flow. Do not edit the package bundle. (The Amount & Frequency component is a Labs
   component — usable but unsupported; for production prefer a managed/custom amount input.)
3. **Pro-code LWC**: it is deployed from source, not installed, so the project already owns it.
   Still keep `paymentMethodConfiguration.js` regenerable (`generate:config`) and put custom
   behaviour in a wrapper or fork rather than in the generated file.
4. **Managed FinDock components** (`cpm:payButton`, `cpm:paymentMethodSelector`): never copy or
   modify; configure only through their inputs.
5. **Site bundles** (`donation-site`, `checkout-site`): edits in Experience Builder are stored on
   the site, not in the package — safe to change directly.
6. **Permission sets**: don't edit the package guest perm sets; add a project-owned perm set for new
   Flows/LWCs and assign it to the Guest User alongside them.
7. Point the Experience Builder page (or the Lightning Out 2.0 wrapper) at the **copy**, then
   remove the original from the page.

Tell the user explicitly which artefacts you cloned and which you left as package-owned.

---

## Step D — Post-change checklist

1. **Activate** the new Flow version (and deactivate the old one if replaced).
2. **Payment Method Selector / config**: methods, processors and targets still match what is active
   in FinDock Setup → Processors & Methods (regenerate the pro-code config if the org changed).
3. **Pay Button**: `successUrl` / `failureUrl` point to real pages in the site; amount, currency
   and frequency inputs are wired to the (possibly renamed) screen components.
4. **Guest access**: FinDock Payer permission set group on the Guest User, the template guest
   perm set (or your project-owned one) grants run access to the *new* Flow / LWC, API access
   preference enabled, ProcessingHub connected. See `experience-cloud.md` → REQUIRED for public sites.
5. **Translations**: new labels added to Translation Workbench / Custom Labels if the site is
   multilingual.
6. **Publish** the Experience Cloud site; for Lightning Out 2.0, confirm the LO2 app still lists
   every component the cloned Flow uses (see `lightning-out.md`).
7. Test as a guest in an incognito window: one-time and recurring (if offered), one redirect method
   (e.g. iDEAL) and one inline method (e.g. card), success and failure return.
8. Re-run the delivery self-check in `page-quality.md` for any layout or copy change.
