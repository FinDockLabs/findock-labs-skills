# FinDock Payments plugin

A standalone, installable plugin that provides one skill — **payment-web-builder** — for
building payment pages, donation forms, checkout flows, and membership sign-ups on top of the
**FinDock Payment API**, both standalone (hosted anywhere) and on-platform in Salesforce
(Experience Cloud, Multi-Framework React, Lightning, Flow, Apex).

This plugin is independent of any organisation-specific plugin and can be installed anywhere.

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

**Claude Code** — add the plugin via your marketplace/plugin configuration, or place this
`findock-payments/` directory where your Claude Code plugins live, then reload. The skill
appears as `findock-payments:payment-web-builder`.

**Agentforce Vibes** — the skill also works standalone: copy `skills/payment-web-builder/`
into `.a4drules/skills/`.

## Contents

```
findock-payments/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── payment-web-builder/
│       ├── SKILL.md
│       └── references/
└── README.md
```
