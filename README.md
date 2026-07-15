# FinDock Labs skills

Cross-tool [Agent Skills](https://agentskills.io) that give AI coding agents the FinDock domain
knowledge they don't ship with — starting with payment-page building on the **FinDock Payment
API**. The skills follow the open `SKILL.md` standard, so the same skill works in Claude Code,
OpenAI Codex, GitHub Copilot, Cursor, Gemini CLI, Agentforce Vibes, and 60+ other agents.

## Skills

| Skill | Description |
| --- | --- |
| [`payment-web-builder`](skills/payment-web-builder) | Build payment pages, donation forms, checkout flows, and membership sign-ups on the FinDock Payment API — standalone or on-platform in Salesforce (Experience Cloud, Multi-Framework React, Lightning, Flow, Apex). |
| [`generate-payment-config`](skills/generate-payment-config) | Generate or reset `paymentMethodConfiguration.js` for an LWC project — from an empty template, a static example library (by processor/region or selected methods), or a live, connected Salesforce org. |

## Install

### Any agent — the `skills` CLI (recommended)

Uses the open [`skills`](https://github.com/vercel-labs/skills) CLI, which auto-detects the agents
you have installed and links these skills into each:

```bash
npx skills add FinDockLabs/findock-labs-skills                                   # auto-detect agents, install all skills
npx skills add FinDockLabs/findock-labs-skills -g                                # install globally (all projects)
npx skills add FinDockLabs/findock-labs-skills --agent claude-code codex github-copilot cursor   # target specific agents
```

Works with Claude Code, Codex, Copilot, Cursor, Gemini CLI, Cline, and more.

### Agentforce Vibes

Vibes does **not** auto-install third-party skills (it only auto-installs Salesforce's own
[`sf-skills`](https://github.com/forcedotcom/sf-skills)). Copy the skill folder in manually:

```bash
cp -R skills/payment-web-builder .a4drules/skills/        # project-local
# or: cp -R skills/payment-web-builder ~/.a4drules/skills/   # global
```

Then verify it in the Skills panel.

### Claude Code plugin marketplace (alternative)

This repo is also a Claude Code plugin marketplace, if you prefer `/plugin`:

```
/plugin marketplace add FinDockLabs/findock-labs-skills
/plugin install findock-payments@findock-labs
```

### Claude Desktop app

Claude Desktop can also add this repo as a plugin marketplace directly from the UI:

1. Go to **Customize → Plugins**.
2. Click **Add → Add marketplace**.
3. Paste the GitHub repository URL (`FinDockLabs/findock-labs-skills`) or its full URL.
4. Click **Sync**.

The `findock-payments` plugin then appears in your plugin list.

## Recommended setup — FinDock docs MCP

The skills ground their code in the live FinDock docs. Wiring up the FinDock docs MCP
(`https://docs.findock.com/mcp`) gives the best results; without it the skills fall back to
fetching `https://docs.findock.com` directly. Per-tool setup is in
[`skills/payment-web-builder/references/docs-access.md`](skills/payment-web-builder/references/docs-access.md).

## Recommended setup — Salesforce `sf-skills` (for Salesforce-native builds)

The Salesforce-native build options — Experience Cloud LWC/Flow, on-platform Apex, and
Multi-Framework React — deliberately **don't** duplicate generic Salesforce mechanics. The
`payment-web-builder` skill supplies only the FinDock-specific contract (the payment-method
catalogue, the PaymentIntent shape, `cpm.API_PaymentIntent_V2`, the managed Pay Button /
Payment Method Selector components) and **defers LWC scaffolding, Apex class structure, Flow
construction, and org metadata to Salesforce's own**
[`sf-skills`](https://github.com/forcedotcom/sf-skills) (`generating-lwc-components`,
`generating-flow`, `generating-apex`, `deploying-metadata`, and more).

For the best results on Salesforce-native builds, have both installed:

- **Agentforce Vibes** — `sf-skills` are **auto-installed and auto-updated**; you only add
  `payment-web-builder` yourself (see [Install](#agentforce-vibes) above).
- **Claude Code / Codex / Cursor / others** — install `sf-skills` alongside this skill:

  ```bash
  npx skills add forcedotcom/sf-skills
  ```

Without `sf-skills` the FinDock skill still works, but it falls back on the agent's built-in
Salesforce knowledge for the surrounding scaffolding rather than Salesforce's maintained,
org-aware skills.

## Layout

```
findock-payments-plugin/
├── skills/
│   ├── payment-web-builder/        # canonical skill (SKILL.md + references/)
│   └── generate-payment-config/    # canonical skill (SKILL.md + references/)
├── plugins/
│   └── findock-payments/           # Claude Code plugin wrapper
│       ├── .claude-plugin/plugin.json
│       └── skills/payment-web-builder  → symlink to ../../../skills/payment-web-builder
├── .claude-plugin/marketplace.json # Claude Code marketplace manifest
├── package.json
└── README.md                       # this file
```

The skill lives once under `skills/`; the plugin wrapper points at it via a symlink so the Claude
Code marketplace install keeps working off the same source.

## Adding a skill

1. Create `skills/<skill-name>/SKILL.md` (required `name` + `description` frontmatter) plus any
   `references/`, `scripts/`, or `assets/`.
2. To also expose it through the Claude Code marketplace, add a symlink under the plugin's
   `skills/` directory and (if it's a new plugin) an entry in `.claude-plugin/marketplace.json`.
