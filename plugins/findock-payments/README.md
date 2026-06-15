# findock-payments

A Claude Code plugin that provides one skill — **payment-web-builder** — for building payment
pages, donation forms, checkout flows, and membership sign-ups on top of the **FinDock Payment
API**, both standalone (hosted anywhere) and on-platform in Salesforce (Experience Cloud,
Multi-Framework React, Lightning, Flow, Apex).

Part of the [FinDock Labs marketplace](../../README.md). It is independent of any
organisation-specific plugin and can be installed anywhere.

## What the skill does

- Runs an intake (form flow, deployment target, page type, design reference, payment methods)
  to decide what to build.
- Supplies FinDock-specific knowledge: payment-method catalogue, the PaymentIntent contract,
  the on-platform Apex entry points (`cpm.API_PaymentIntent_V2.postPaymentIntent`,
  `cpm.API_PaymentMethod_V2.getPaymentMethods`), enum/parameter rendering, the Payment Method
  Selector config schema, and the FinDock UX conventions.
- Enforces quality bars: required-field validation, success/failure routing with recoverable
  (201–205) vs generic error handling, WCAG 2.2 AA, responsive/mobile, full donation-page
  structure, and method-icon rendering from the response.

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

Once installed, the skill appears as `findock-payments:payment-web-builder`.

**Other agents (Codex, Copilot, Cursor, …)** — install the skill cross-tool with the open
`skills` CLI: `npx skills add FinDockLabs/findock-labs-skills`. See the [repository README](../../README.md) for
options and the Agentforce Vibes path.

## Contents

```
findock-payments/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── payment-web-builder  → symlink to ../../skills/payment-web-builder (the canonical skill)
└── README.md
```

The skill itself lives at the repo root under `skills/payment-web-builder/`; this plugin links to
it so the Claude Code marketplace install and the cross-tool `npx skills` install share one source.
