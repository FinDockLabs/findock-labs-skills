# FinDock Labs marketplace

A Claude Code [plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugins) for
FinDock plugins. It distributes the FinDock domain knowledge and skills that Claude doesn't
ship with — starting with payment-page building on the FinDock Payment API.

## Add the marketplace

```
/plugin marketplace add <owner>/<repo>
```

Replace `<owner>/<repo>` with this repository (or pass a Git URL / local path). Then browse and
install plugins with `/plugin`.

## Plugins

| Plugin | Description |
| --- | --- |
| [`findock-payments`](plugins/findock-payments) | Build payment pages, donation forms, checkout flows, and membership sign-ups on the FinDock Payment API — standalone or on-platform in Salesforce. |

Install a plugin from this marketplace:

```
/plugin install findock-payments@findock-labs
```

See each plugin's own README (linked above) for what it provides and how it behaves.

## Layout

```
findock-payments-plugin/
├── .claude-plugin/
│   └── marketplace.json        # marketplace manifest — lists the plugins below
├── plugins/
│   └── findock-payments/       # one directory per plugin
│       ├── .claude-plugin/
│       │   └── plugin.json
│       ├── skills/
│       └── README.md
└── README.md                   # this file
```

## Adding a plugin to the marketplace

1. Create `plugins/<plugin-name>/` with a `.claude-plugin/plugin.json` and the plugin's
   contents (skills, commands, agents, etc.).
2. Add a `README.md` inside the plugin directory.
3. Add an entry to the `plugins` array in `.claude-plugin/marketplace.json`, pointing `source`
   at `./plugins/<plugin-name>`.
