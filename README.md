# HoneyNet

A distributed, educational honeypot that records connection attempts from decoy SSH, HTTP, and FTP services and displays them on a live dashboard.

## Architecture

```text
Attacker / test client
        │ connects to decoy ports
        ▼
Laptop Honeypot Agent (Python)
        │ HTTPS JSON events
        ▼
Cloud API (Node.js + Express on Render)
        │ PostgreSQL/TLS
        ▼
Supabase Database ─────► Static Dashboard (Vercel / Netlify)
                         polls every 2 seconds
```

## Tech stack

- **Agent:** Python 3, standard-library sockets and HTTP server, `requests`
- **API:** Node.js, Express, `pg`, `cors`, `dotenv`
- **Database:** Supabase PostgreSQL
- **Dashboard:** One self-contained HTML file, vanilla CSS and JavaScript
- **Free-tier hosting options:** Render for API; Vercel or Netlify for the static page; Supabase for PostgreSQL (free-tier limits and availability can change)

## Setup and deployment

1. **Create the database.** Create a Supabase project. Open its SQL Editor and run [`database/schema.sql`](./database/schema.sql). Copy the PostgreSQL connection string from the project’s database settings; replace its password placeholder with the database password. Keep this value private.
2. **Deploy the backend to Render.** Push this project to GitHub, create a Render **Web Service** from the repository, and set its root directory to `honeynet/backend` (or `backend` if this repository contains only the project). Render should use `npm install` to install dependencies and `npm start` to launch. Add `DATABASE_URL` as an environment variable using the Supabase connection string, then deploy. The API listens on Render’s `PORT`.
3. **Deploy the frontend.** Copy the deployed Render service URL, such as `https://your-service.onrender.com`, into `API_URL` in [`frontend/index.html`](./frontend/index.html), replacing the example `https://honeynet-api.onrender.com`. Deploy the `frontend` folder by drag-and-drop to Netlify or with `vercel --prod` from that folder. No build step is required.
4. **Run the honeypot.** On the laptop that will host the decoys, set `API_URL` near the top of [`agent/honeypot.py`](./agent/honeypot.py) to the same deployed Render URL. From the `agent` directory, run `python -m pip install -r requirements.txt`, then `python honeypot.py`. Approve/firewall only the intended inbound demo ports (2222, 8080, 2121). Make sure the network permits inbound connections; do not expose the agent broadly to the public internet.
5. **Test from an authorized device on the same network.** Find the laptop’s local IP address. Try `ssh -p 2222 test@[YOUR_IP]` or open `http://[YOUR_IP]:8080/admin` in a browser. A direct test can also use `curl http://[YOUR_IP]:8080/admin`. FTP listens on TCP port 2121.
6. **Watch the dashboard.** Open the deployed static-site URL. The statistics and latest attacks refresh every two seconds. The first dashboard visit can take a short time if Render’s free service has been idle.

## API endpoints

All API URLs below are relative to the deployed backend base URL. JSON endpoints respond with `application/json`.

| Method | Path | Body | Response |
| --- | --- | --- | --- |
| GET | `/` | — | `{ "status": "HoneyNet API running" }` |
| GET | `/health` | — | `{ "status": "ok" }` |
| POST | `/api/register` | `{ "node_id": "node-001", "name": "Laptop Honeypot" }` | `{ "success": true, "node": { ... } }`; upserts the node and updates `last_seen` |
| POST | `/api/attack` | `{ "attacker_ip": "192.0.2.10", "service": "ssh", "port": 2222, "payload": "..." }` | HTTP 201: `{ "success": true, "attack": { ... } }` |
| GET | `/api/attacks` | — | Array of up to 100 newest attack rows |
| GET | `/api/stats` | — | `{ "total_attacks": 0, "unique_attackers": 0, "services_targeted": 0 }` |

Invalid request fields receive HTTP 400. Server/database errors receive HTTP 500 with a short error message; check Render logs for details. The API is intentionally unauthenticated for this student demo: anyone who can reach it can submit events. Do not use for real monitoring or sensitive information.

## Cybersecurity concepts

- **Honeypot:** A decoy service intended to attract and observe unsolicited connections without offering a real service.
- **Attack surface:** The network ports and application interfaces that can be reached. This demo deliberately opens decoy ports; firewall them to the intended demo network.
- **Threat intelligence:** Aggregated observations (source IP, target service, time, and request data) can help illustrate attacker behaviors. An IP address alone does not prove who operated a host, and payloads may contain sensitive data; handle collected data responsibly.

## Troubleshooting

- **API returns a database error:** Confirm the Render `DATABASE_URL` is correct, includes the right password, and the Supabase project is active. Verify `schema.sql` ran successfully.
- **Render deployment fails or API sleeps:** Check the Render build/start logs and ensure the service root directory points to `backend`. Free instances may sleep and take a little time to wake.
- **Dashboard stays blank:** Replace `API_URL` with the deployed backend’s HTTPS base URL (no extra path), check `/health`, and inspect browser network errors. The static dashboard requires CORS, which the API enables.
- **Agent cannot reach the API:** Check the laptop internet connection, API URL, DNS, and Render availability. Registration/report errors are printed in the agent terminal.
- **No remote test connects:** Use the laptop’s reachable LAN IP, ensure devices are on the same network, allow the chosen ports through the host firewall, and check for router/client isolation. Avoid opening these ports to the public internet.
- **Port is already in use:** Stop the other process using that port or adjust the listener port in `main()` and matching test instructions; restart the agent.
- **No attacks appear after a request:** Confirm the backend is deployed, schema exists, agent reports to that same API URL, and request reached the laptop’s correct port. Look at Render logs for insert errors.

## Demo safety

This is a classroom demonstration, not a production honeypot. The agent binds to all laptop interfaces and the public API has no authentication. Use a controlled, authorized network, avoid collecting real credentials, and stop the agent with Ctrl+C after the demo.
