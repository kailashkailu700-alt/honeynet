# HoneyNet architecture

## Components and trust boundaries

```text
 UNTRUSTED INTERNET / CONTROLLED DEMO NETWORK
┌────────────────────┐   TCP 2222 / HTTP 8080 / TCP 2121
│ Remote test client │ ───────────────────────────────────┐
└────────────────────┘                                    │
                                                          ▼
                                             ┌────────────────────────┐
                                             │ Laptop HoneyNet agent  │
                                             │ Python socket + HTTP   │
                                             │ SSH / web / FTP decoys │
                                             └───────────┬────────────┘
                                                         │ HTTPS JSON
                                                         │ POST /api/attack
                                                         │ POST /api/register
                                                         ▼
                                             ┌────────────────────────┐
                                             │ Express API on Render  │
                                             │ input checks + REST    │
                                             └───────────┬────────────┘
                                                         │ TLS PostgreSQL
                                                         ▼
                                             ┌────────────────────────┐
                                             │ Supabase PostgreSQL    │
                                             │ attacks / nodes tables│
                                             └───────────┬────────────┘
                                                         │ SELECT aggregates
                                                         ▼
                                             ┌────────────────────────┐
                                             │ Static dashboard       │
                                             │ Vercel / Netlify       │
                                             │ polls every 2 seconds │
                                             └────────────────────────┘
```

## Data flow

1. The agent registers `node-001` at startup. The API upserts the node and refreshes `last_seen`.
2. The SSH and FTP TCP listeners capture the peer IP and first client bytes. The HTTP decoy serves a fake router login and captures POST form data. They send observations to `/api/attack` as JSON over HTTPS.
3. Express checks the required fields, bounds payload size, uses parameterized PostgreSQL queries, and inserts the observation in `attacks`. The API logs a concise alert.
4. The dashboard polls `/api/stats` and `/api/attacks` every two seconds and updates its cards and latest-100 table.

## Deployment and safety boundary

The laptop agent is an intentionally minimal sensor, not a real SSH/FTP implementation: it does not authenticate users or execute commands. Its HTTP form and captured traffic are decoys. Keep it on a controlled lab network, firewall ports to known demo clients, and do not collect real passwords or personal data. The demo API has no authentication by requirement, so it is publicly writable when deployed; do not use it for production or sensitive data. Configure the exact database connection string as a private Render environment variable and never publish `.env` or database credentials.
