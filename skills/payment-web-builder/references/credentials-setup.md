# Credentials Setup — `npm run setup` & `npm run doctor`

For every **standalone** output (deployment target "Anywhere"), ship the files below alongside
the page and proxy. They remove the credential hunt: setup auto-detects an authenticated
Salesforce CLI when present, falls back to guided manual entry with format validation, and
doctor verifies the values actually work against the org before the first real payment.

Not needed for Multi-Framework or Experience Cloud targets (platform handles auth there).

## What to ship

```
payment-form/
├── index.html
├── server.js          (proxy — reads .env)
├── setup.mjs          (this reference, verbatim below)
├── .env.example
├── .gitignore         (must contain .env)
└── package.json       (scripts: setup, doctor, start)
```

`package.json` scripts:

```json
{
  "scripts": {
    "setup":  "node setup.mjs",
    "doctor": "node setup.mjs doctor",
    "start":  "node server.js"
  }
}
```

## `.env.example` (placeholders carry the exact click-path)

```bash
# Where to find these values — see also: npm run setup (guided)
# Sandbox: https://test.salesforce.com | Production: https://login.salesforce.com
SF_AUTH_HOST=https://test.salesforce.com

# Setup → App Manager → your Connected App → Manage Consumer Details → Consumer Key
SF_CLIENT_ID=

# Same screen → Consumer Secret
SF_CLIENT_SECRET=

# Your org's My Domain, e.g. https://yourorg.my.salesforce.com
# Setup → My Domain, or run: sf org display
SF_INSTANCE_URL=

# Filled by the OAuth flow or by setup.mjs via the sf CLI — leave empty initially
SF_ACCESS_TOKEN=
SF_REFRESH_TOKEN=
```

## `setup.mjs` (include verbatim)

```javascript
#!/usr/bin/env node
// FinDock credentials setup & doctor.
//   node setup.mjs          → guided setup, writes .env
//   node setup.mjs doctor   → verifies credentials against the org
import { execSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync, appendFileSync } from 'node:fs';
import readline from 'node:readline/promises';

const ENV = '.env';
const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

// ── helpers ──────────────────────────────────────────────────────────────────
const loadEnv = () => Object.fromEntries(
  (existsSync(ENV) ? readFileSync(ENV, 'utf8') : '')
    .split('\n').filter(l => l.includes('=') && !l.startsWith('#'))
    .map(l => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim()])
);

const saveEnv = (vars) => {
  writeFileSync(ENV, Object.entries(vars).map(([k, v]) => `${k}=${v ?? ''}`).join('\n') + '\n');
  if (!existsSync('.gitignore') || !readFileSync('.gitignore', 'utf8').includes('.env')) {
    appendFileSync('.gitignore', '\n.env\n');
  }
  console.log(`✓ wrote ${ENV} (and ensured it is gitignored)`);
};

const ask = async (label, hint, validate) => {
  for (;;) {
    const v = (await rl.question(`${label}\n  ${hint}\n> `)).trim();
    const err = validate?.(v);
    if (!err) return v;
    console.log(`  ✗ ${err} — try again.`);
  }
};

// ── sf CLI auto-detect ───────────────────────────────────────────────────────
// NOTE: This calls the user's OWN Salesforce CLI if it is installed — it does not
// install or bundle it. If `sf` is absent, setup falls back to manual entry below.

function detectSfCli() {
  try {
    const out = execSync('sf org display --json', { stdio: ['ignore', 'pipe', 'ignore'] });
    const r = JSON.parse(out).result;
    if (r?.accessToken && r?.instanceUrl) return r;
  } catch { /* sf not installed or not authenticated */ }
  return null;
}

// ── setup ────────────────────────────────────────────────────────────────────
async function setup() {
  console.log('\nFinDock Payment API — credential setup\n');
  const vars = loadEnv();

  const sf = detectSfCli();
  if (sf) {
    console.log(`Found authenticated Salesforce CLI org: ${sf.username ?? sf.instanceUrl}`);
    const use = (await rl.question('Use it for dev/testing? No Connected App needed. [Y/n] ')).trim().toLowerCase();
    if (use !== 'n') {
      vars.SF_INSTANCE_URL = sf.instanceUrl;
      vars.SF_ACCESS_TOKEN = sf.accessToken;
      vars.SF_AUTH_HOST = sf.instanceUrl.includes('sandbox')
        ? 'https://test.salesforce.com' : 'https://login.salesforce.com';
      saveEnv(vars);
      console.log('\nNote: CLI tokens expire with the org session. For production, re-run');
      console.log('setup and choose manual entry to configure a Connected App.\n');
      return doctor();
    }
  } else {
    console.log('No authenticated sf CLI found (install + `sf org login web` for the easy path).');
    console.log('Falling back to manual Connected App entry.\n');
  }

  vars.SF_AUTH_HOST = (await rl.question('Sandbox or production org? [sandbox/prod] '))
    .trim().toLowerCase().startsWith('p')
      ? 'https://login.salesforce.com' : 'https://test.salesforce.com';

  vars.SF_CLIENT_ID = await ask(
    'Consumer Key',
    'Setup → App Manager → your Connected App → Manage Consumer Details',
    v => v.startsWith('3MVG') ? null : 'Consumer Keys start with "3MVG"');

  vars.SF_CLIENT_SECRET = await ask(
    'Consumer Secret', 'Same screen as the Consumer Key',
    v => v.length >= 10 ? null : 'That looks too short for a Consumer Secret');

  vars.SF_INSTANCE_URL = await ask(
    'Instance URL', 'Setup → My Domain, e.g. https://yourorg.my.salesforce.com',
    v => /^https:\/\/.+\.salesforce\.com$/.test(v.replace(/\/$/, ''))
      ? null : 'Expected https://<domain>.my.salesforce.com');
  vars.SF_INSTANCE_URL = vars.SF_INSTANCE_URL.replace(/\/$/, '');

  saveEnv(vars);
  console.log('\nNext: complete the OAuth flow once via the proxy (/connect) to obtain tokens,');
  console.log('then run `npm run doctor` to verify.\n');
}

// ── doctor ───────────────────────────────────────────────────────────────────
async function doctor() {
  console.log('\nFinDock credential doctor\n');
  const v = loadEnv();
  const fail = (msg, fix) => { console.log(`✗ ${msg}\n  → ${fix}\n`); process.exit(1); };

  if (!v.SF_INSTANCE_URL) fail('SF_INSTANCE_URL missing', 'Run `npm run setup`');
  if (!v.SF_ACCESS_TOKEN && !(v.SF_CLIENT_ID && v.SF_REFRESH_TOKEN))
    fail('No access token and no refresh-token pair',
         'Run `npm run setup`, or complete the OAuth flow via /connect on the proxy');

  let token = v.SF_ACCESS_TOKEN;

  const call = (t) => fetch(`${v.SF_INSTANCE_URL}/services/apexrest/cpm/v2/PaymentMethods`,
    { headers: { Authorization: `Bearer ${t}` } });

  let res = await call(token);

  // 401 → try refresh, then sf CLI re-fetch
  if (res.status === 401) {
    if (v.SF_REFRESH_TOKEN && v.SF_CLIENT_ID) {
      console.log('… access token expired, trying refresh token');
      const r = await fetch(`${v.SF_AUTH_HOST}/services/oauth2/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ grant_type: 'refresh_token',
          refresh_token: v.SF_REFRESH_TOKEN, client_id: v.SF_CLIENT_ID,
          client_secret: v.SF_CLIENT_SECRET }),
      });
      const j = await r.json();
      if (!r.ok) fail(`Token refresh failed: ${j.error_description}`,
        'Re-authorize via /connect, or check Consumer Key/Secret');
      token = j.access_token; v.SF_ACCESS_TOKEN = token; saveEnv(v);
      res = await call(token);
    } else {
      const sf = detectSfCli();
      if (sf?.accessToken) {
        console.log('… access token expired, refreshed via sf CLI');
        token = sf.accessToken; v.SF_ACCESS_TOKEN = token; saveEnv(v);
        res = await call(token);
      }
    }
  }

  if (res.status === 401) fail('Still 401 after refresh',
    'Session invalid — re-run `npm run setup` or re-authorize via /connect');
  if (res.status === 403) fail('403 Forbidden from the Payment API',
    'Assign the "FinDock Integration User" permission set group to this user (Setup → Users)');
  if (res.status === 404) fail('Payment API endpoint not found',
    'Is the FinDock package installed in this org? Check SF_INSTANCE_URL points at the right org');
  if (!res.ok) fail(`Unexpected ${res.status} from /PaymentMethods`,
    (await res.text()).slice(0, 300));

  const data = await res.json();
  const methods = data.PaymentMethods ?? [];
  console.log(`✓ Authenticated against ${v.SF_INSTANCE_URL}`);
  console.log(`✓ Payment API reachable`);
  if (methods.length === 0) {
    console.log('⚠ No payment methods activated — activate processors in FinDock Setup → Processors & Methods');
  } else {
    console.log(`✓ ${methods.length} payment method(s) active:`);
    methods.forEach(m => console.log(`    • ${m.Name}`));
  }
  console.log('\nAll good — start the proxy with `npm start`.\n');
}

(process.argv[2] === 'doctor' ? doctor() : setup()).finally(() => rl.close());
```

## Behaviour notes for the skill

- Generate `server.js` to read all values from `process.env` (dotenv or `node --env-file=.env`).
- After delivering a standalone build, tell the user: "Run `npm run setup` to configure
  credentials (auto-detects the Salesforce CLI), then `npm run doctor` to verify."
- If running inside Claude Code with shell access, offer to run setup/doctor directly and
  interpret the results — that is Workflow Step 6.
- The doctor failure → fix mapping doubles as a debugging guide: 401 = token,
  403 = FinDock Integration User permission set, 404 = package/org mismatch,
  empty methods = no processors activated.
