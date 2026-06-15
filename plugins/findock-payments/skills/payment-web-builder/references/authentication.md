# Authentication — Salesforce OAuth2 for the FinDock Payment API

The FinDock Payment API uses standard Salesforce OAuth2. Every request needs a
`Authorization: Bearer <access_token>` header. This guide covers the full setup from
Connected App creation through token refresh in your server proxy.

---

## Step 1 — Create a Connected App in Salesforce

1. Log in to your Salesforce org as an admin.
2. Go to **Setup** → search **External Client Apps** → open **Settings**.
3. Enable **Allow access to External Client App consumer secrets via REST API**.
4. Go to **Setup** → **App Manager** → **New Connected App**.
5. Fill in the basic info (name, contact email).
6. Check **Enable OAuth Settings** and configure:
   - **Callback URL**: your server's redirect URI, e.g. `https://yourserver.com/oauth/callback`
     (for local dev: `http://localhost:3000/oauth/callback`)
   - **Selected OAuth Scopes**: add **Manage user data via APIs (api)** and
     **Perform requests at any time (refresh_token, offline_access)**
   - **Uncheck** "Require Proof Key for Code Exchange (PKCE)" — FinDock does not use PKCE
7. Click **Save** → **Continue**.
8. Click **Manage Consumer Details** and verify your identity.
9. Copy **Consumer Key** (= `client_id`) and **Consumer Secret** (= `client_secret`).

> **Sandbox vs production**: use `test.salesforce.com` as the auth host for sandboxes,
> `login.salesforce.com` for production.

---

## Step 2 — Add the FinDock Integration User permission set

The Salesforce user whose token will be used must have the **FinDock Integration User**
permission set group assigned. Without it, API calls will be rejected.

Setup → Users → [your user] → Permission Set Group Assignments → Add **FinDock Integration User**.

---

## Step 3 — The OAuth2 Web Server Flow

This is the recommended flow for server-side apps. It exchanges an authorization code for
tokens without ever exposing credentials to the browser.

### Flow overview

```
Browser                  Your server               Salesforce
   |                          |                         |
   |  GET /connect            |                         |
   |------------------------->|                         |
   |                          | redirect to SF login    |
   |<-------------------------|------------------------>|
   |                                                    |
   |  User logs in + approves                           |
   |                                                    |
   |  GET /oauth/callback?code=AUTH_CODE                |
   |------------------------->|                         |
   |                          | POST /oauth2/token      |
   |                          |------------------------>|
   |                          | { access_token,         |
   |                          |   refresh_token,        |
   |                          |   instance_url }        |
   |                          |<------------------------|
   |  Redirect to app         |                         |
   |<-------------------------|                         |
```

### Step 3a — Redirect user to Salesforce login

```javascript
// server.js

const SF_AUTH_HOST    = process.env.SF_AUTH_HOST    // 'https://test.salesforce.com' (sandbox)
                                                    // 'https://login.salesforce.com' (production)
const SF_CLIENT_ID    = process.env.SF_CLIENT_ID    // Consumer Key from Connected App
const SF_CLIENT_SECRET= process.env.SF_CLIENT_SECRET// Consumer Secret
const SF_REDIRECT_URI = process.env.SF_REDIRECT_URI // e.g. 'https://yourserver.com/oauth/callback'

app.get('/connect', (req, res) => {
  const params = new URLSearchParams({
    response_type: 'code',
    client_id:     SF_CLIENT_ID,
    redirect_uri:  SF_REDIRECT_URI,
    scope:         'api refresh_token',
  });
  // FinDock: redirect the user to Salesforce to log in and approve access
  res.redirect(`${SF_AUTH_HOST}/services/oauth2/authorize?${params}`);
});
```

### Step 3b — Handle the callback and exchange code for tokens

```javascript
// In-memory token store — replace with a database or secrets manager in production
let tokenStore = { accessToken: null, refreshToken: null, instanceUrl: null };

app.get('/oauth/callback', async (req, res) => {
  const { code } = req.query;
  if (!code) return res.status(400).send('Missing authorization code');

  // FinDock: exchange the authorization code for an access token + refresh token
  const response = await fetch(`${SF_AUTH_HOST}/services/oauth2/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type:    'authorization_code',
      code,
      client_id:     SF_CLIENT_ID,
      client_secret: SF_CLIENT_SECRET,
      redirect_uri:  SF_REDIRECT_URI,
    }),
  });

  const tokens = await response.json();
  if (!response.ok) {
    return res.status(500).send(`Auth error: ${tokens.error_description}`);
  }

  // FinDock: store these server-side — never send to the browser
  // instance_url is the org-specific base URL for all API calls
  tokenStore.accessToken  = tokens.access_token;
  tokenStore.refreshToken = tokens.refresh_token;
  tokenStore.instanceUrl  = tokens.instance_url; // e.g. https://yourorg.my.salesforce.com

  res.redirect('/');
});
```

---

## Step 4 — Use the access token in API calls

```javascript
// FinDock: proxy endpoint — browser calls this, server adds the Bearer token
app.post('/api/payment-intent', async (req, res) => {
  const token = await getValidToken(); // see Step 5 below

  const response = await fetch(
    `${tokenStore.instanceUrl}/services/apexrest/cpm/v2/PaymentIntent`,
    {
      method:  'POST',
      headers: {
        'Content-Type':  'application/json',
        // FinDock: Bearer token from Salesforce OAuth2 — never expose in browser JS
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(req.body),
    }
  );
  res.status(response.status).json(await response.json());
});

// Same pattern for GET /PaymentMethods, GET /SourceConnector, etc.
app.get('/api/payment-methods', async (req, res) => {
  const token = await getValidToken();
  const response = await fetch(
    `${tokenStore.instanceUrl}/services/apexrest/cpm/v2/PaymentMethods`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );
  res.status(response.status).json(await response.json());
});
```

---

## Step 5 — Refresh the access token when it expires

Salesforce access tokens expire (typically after the session timeout configured in the org,
often 2 hours). Use the refresh token to get a new one without re-prompting the user.

```javascript
async function getValidToken() {
  // Simple check — in production, decode the JWT to check expiry time
  if (tokenStore.accessToken) return tokenStore.accessToken;
  return await refreshAccessToken();
}

async function refreshAccessToken() {
  // FinDock: use the refresh token to get a new access token
  const response = await fetch(`${SF_AUTH_HOST}/services/oauth2/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type:    'refresh_token',
      refresh_token: tokenStore.refreshToken,
      client_id:     SF_CLIENT_ID,
      client_secret: SF_CLIENT_SECRET,
    }),
  });

  const tokens = await response.json();
  if (!response.ok) throw new Error(`Token refresh failed: ${tokens.error_description}`);

  tokenStore.accessToken = tokens.access_token;
  // instance_url is re-returned and should be updated
  if (tokens.instance_url) tokenStore.instanceUrl = tokens.instance_url;

  return tokenStore.accessToken;
}
```

For production, add retry logic: if a `401` comes back from a FinDock API call, call
`refreshAccessToken()` once and retry the original request before returning an error.

```javascript
async function callFinDock(path, options = {}) {
  const makeRequest = async () => {
    const token = await getValidToken();
    return fetch(`${tokenStore.instanceUrl}/services/apexrest/cpm/v2${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
    });
  };

  let res = await makeRequest();

  // FinDock: 401 = token expired — refresh and retry once
  if (res.status === 401) {
    tokenStore.accessToken = null; // force refresh
    res = await makeRequest();
  }

  return res;
}
```

---

## Step 6 — JWT Bearer Flow (optional, for service-to-service / headless)

If there's no interactive user login (e.g. a background service or cron job calling the
FinDock API), use the **JWT Bearer Flow** instead. This skips the browser redirect entirely.

Requirements: a certificate uploaded to the Connected App in Salesforce, and pre-authorisation
of the integration user by an admin.

```javascript
import jwt from 'jsonwebtoken';
import fs  from 'fs';

const privateKey = fs.readFileSync('server.key'); // your private key

async function getTokenViaJWT() {
  const claim = {
    iss: SF_CLIENT_ID,
    sub: 'integration-user@yourorg.com', // the Salesforce username
    aud: SF_AUTH_HOST,
    exp: Math.floor(Date.now() / 1000) + 180, // 3 min expiry
  };

  const signedJwt = jwt.sign(claim, privateKey, { algorithm: 'RS256' });

  const response = await fetch(`${SF_AUTH_HOST}/services/oauth2/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
      assertion:  signedJwt,
    }),
  });

  const tokens = await response.json();
  tokenStore.accessToken = tokens.access_token;
  tokenStore.instanceUrl = tokens.instance_url;
  return tokens.access_token;
}
```

Use this flow when:
- The integration runs unattended on a server (no browser available)
- You want to avoid storing a refresh token
- An admin can pre-approve the Connected App for the integration user

---

## Environment variables summary

```bash
# .env
SF_AUTH_HOST=https://test.salesforce.com     # sandbox; use login.salesforce.com for prod
SF_CLIENT_ID=3MVG9...                        # Consumer Key from Connected App
SF_CLIENT_SECRET=1955...                     # Consumer Secret
SF_REDIRECT_URI=http://localhost:3000/oauth/callback
```

---

## Quick reference

| What | Where |
|------|-------|
| Authorize URL | `{SF_AUTH_HOST}/services/oauth2/authorize` |
| Token URL | `{SF_AUTH_HOST}/services/oauth2/token` |
| API base URL | `{instance_url}/services/apexrest/cpm/v2` |
| Sandbox auth host | `https://test.salesforce.com` |
| Production auth host | `https://login.salesforce.com` |
| Required scope | `api refresh_token` |
| Required permission set | FinDock Integration User |

---

## Resources

- [FinDock: Getting started with the Payment API](https://docs.findock.com/api/getting-started-with-the-payment-api-v2)
- [Salesforce: OAuth 2.0 Web Server Flow](https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_oauth_web_server_flow.htm)
- [Salesforce: OAuth 2.0 JWT Bearer Flow](https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_oauth_jwt_flow.htm)
- [Salesforce: OAuth 2.0 Refresh Token Flow](https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_oauth_refresh_token_flow.htm)
