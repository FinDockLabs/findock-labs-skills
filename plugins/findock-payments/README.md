# findock-payments

A Claude Code plugin that provides two skills for building on the **FinDock Payment API**:
**payment-web-builder** and **generate-payment-config**.

Part of the [FinDock Labs marketplace](../../README.md). It is independent of any
organisation-specific plugin and can be installed anywhere.

## What the skills do

**payment-web-builder** — builds payment pages, donation forms, checkout flows, and membership
sign-ups, both standalone (hosted anywhere) and on-platform in Salesforce (Experience Cloud,
Multi-Framework React, Lightning, Flow, Apex).

- Runs an intake (form flow, deployment target, page type, design reference, payment methods)
  to decide what to build.
- Supplies FinDock-specific knowledge: payment-method catalogue, the PaymentIntent contract,
  the on-platform Apex entry points (`cpm.API_PaymentIntent_V2.postPaymentIntent`,
  `cpm.API_PaymentMethod_V2.getPaymentMethods`), enum/parameter rendering, the Payment Method
  Selector config schema, and the FinDock UX conventions.
- Enforces quality bars: required-field validation, success/failure routing with recoverable
  (201–205) vs generic error handling, WCAG 2.2 AA, responsive/mobile, full donation-page
  structure, and method-icon rendering from the response.

**generate-payment-config** — generates or resets `paymentMethodConfiguration.js` for an LWC
project, in four modes: an empty template, a full or selective list of methods from a static
example library (by processor or region), or generation from a live, connected Salesforce org.

## Adapts to the host

- **Standalone / no Salesforce host**: carries the full stack (REST patterns, OAuth proxy,
  credential setup + doctor tooling).
- **Inside Agentforce Vibes or Claude Code with org tooling**: supplies the FinDock contract
  and defers Salesforce scaffolding to the host. Does not bundle or depend on the `sf` CLI
  skill — it only points the user to Salesforce tooling when a task actually touches the org.

## Install

**Claude Code (via the FinDock Labs marketplace)** — add the marketplace, then install:

```
/plugin marketplace add FinDockLabs/findock-labs-skills
/plugin install findock-payments@findock-labs
```

Once installed, the skills appear as `findock-payments:payment-web-builder` and
`findock-payments:generate-payment-config`.

**Other agents (Codex, Copilot, Cursor, …)** — install the skills cross-tool with the open
`skills` CLI: `npx skills add FinDockLabs/findock-labs-skills`. See the [repository README](../../README.md) for
options and the Agentforce Vibes path.

## Contents

```
findock-payments/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── payment-web-builder       → symlink to ../../skills/payment-web-builder (canonical skill)
│   └── generate-payment-config   → symlink to ../../skills/generate-payment-config (canonical skill)
└── README.md
```

The skills themselves live at the repo root under `skills/`; this plugin links to them so the
Claude Code marketplace install and the cross-tool `npx skills` install share one source.
