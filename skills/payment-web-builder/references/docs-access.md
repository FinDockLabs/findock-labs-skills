# Accessing the FinDock docs (MCP or fetch fallback)

This skill must ground its code in the live FinDock documentation — never guess the Payment API
contract from memory. There are two ways to reach the docs; either is fine.

## Option A — FinDock docs MCP (recommended)

The FinDock docs are served over MCP at:

```
https://docs.findock.com/mcp
```

Wire it into your agent once, then the skill can query it directly. Configure it per tool:

### Claude Code
```bash
claude mcp add --transport http findock-docs https://docs.findock.com/mcp
```
(or add it to `.mcp.json` at the project root). Verify with `/mcp`.

### OpenAI Codex
Add to `~/.codex/config.toml`:
```toml
[mcp_servers.findock-docs]
url = "https://docs.findock.com/mcp"
```
If your Codex build only supports stdio MCP servers, bridge the remote endpoint:
```toml
[mcp_servers.findock-docs]
command = "npx"
args = ["-y", "mcp-remote", "https://docs.findock.com/mcp"]
```

### GitHub Copilot (VS Code)
Add to `.vscode/mcp.json` (workspace) or your user MCP config:
```json
{
  "servers": {
    "findock-docs": { "type": "http", "url": "https://docs.findock.com/mcp" }
  }
}
```

### Cursor
Add to `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global):
```json
{
  "mcpServers": {
    "findock-docs": { "url": "https://docs.findock.com/mcp" }
  }
}
```

## Option B — Fetch fallback (no MCP, works anywhere)

If no MCP is configured, use the agent's web-fetch/browse capability against the public docs at:

```
https://docs.findock.com
```

Pull the **Payment API v2** reference (endpoints, the PaymentIntent payload schema, payment-method
parameters/enums, and processor-specific requirements) before writing code. Treat the fetched docs
as the source of truth exactly as you would the MCP response. If web access is unavailable too,
tell the user you need either the docs MCP configured or network access, and ask them to confirm
the specific contract details rather than guessing.
