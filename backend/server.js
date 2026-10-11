// HoneyNet's small REST API. Set DATABASE_URL in the deployment environment.
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');

const app = express();
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
});

app.use(cors());
app.use(express.json({ limit: '32kb' }));

app.get('/', (req, res) => {
  try {
    return res.json({ status: 'HoneyNet API running' });
  } catch (error) {
    console.error('Failed to serve API status:', error.message);
    return res.status(500).json({ error: 'Failed to serve API status' });
  }
});

app.get('/health', (req, res) => {
  try {
    return res.json({ status: 'ok' });
  } catch (error) {
    console.error('Failed to serve health check:', error.message);
    return res.status(500).json({ error: 'Health check failed' });
  }
});

app.post('/api/attack', async (req, res) => {
  try {
    const { attacker_ip, service, port, payload } = req.body || {};
    const parsedPort = Number(port);
    if (typeof attacker_ip !== 'string' || !attacker_ip.trim() || attacker_ip.length > 45 ||
        typeof service !== 'string' || !service.trim() || service.length > 50 ||
        !Number.isInteger(parsedPort) || parsedPort < 1 || parsedPort > 65535 ||
        typeof payload !== 'string') {
      return res.status(400).json({ error: 'attacker_ip, service, a valid port, and string payload are required' });
    }

    console.log(`🚨 Attack from ${attacker_ip.trim()} on ${service.trim()}:${parsedPort}`);
    const { rows } = await pool.query(
      'INSERT INTO attacks (attacker_ip, service, port, payload) VALUES ($1, $2, $3, $4) RETURNING *',
      [attacker_ip.trim(), service.trim(), parsedPort, payload.slice(0, 10000)]
    );
    return res.status(201).json({ success: true, attack: rows[0] });
  } catch (error) {
    console.error('Failed to record attack:', error.message);
    return res.status(500).json({ error: 'Failed to record attack' });
  }
});

app.post('/api/register', async (req, res) => {
  try {
    const { node_id, name } = req.body || {};
    if (typeof node_id !== 'string' || !node_id.trim() || node_id.length > 100 ||
        typeof name !== 'string' || !name.trim() || name.length > 200) {
      return res.status(400).json({ error: 'node_id and name are required' });
    }

    const { rows } = await pool.query(
      `INSERT INTO nodes (node_id, name, status, last_seen)
       VALUES ($1, $2, 'online', NOW())
       ON CONFLICT (node_id) DO UPDATE
       SET name = EXCLUDED.name, status = 'online', last_seen = NOW()
       RETURNING *`,
      [node_id.trim(), name.trim()]
    );
    return res.json({ success: true, node: rows[0] });
  } catch (error) {
    console.error('Failed to register node:', error.message);
    return res.status(500).json({ error: 'Failed to register node' });
  }
});

app.get('/api/attacks', async (req, res) => {
  try {
    const { rows } = await pool.query('SELECT * FROM attacks ORDER BY timestamp DESC LIMIT 100');
    return res.json(rows);
  } catch (error) {
    console.error('Failed to load attacks:', error.message);
    return res.status(500).json({ error: 'Failed to load attacks' });
  }
});

app.get('/api/stats', async (req, res) => {
  try {
    const { rows } = await pool.query(
      `SELECT COUNT(*)::integer AS total_attacks,
              COUNT(DISTINCT attacker_ip)::integer AS unique_attackers,
              COUNT(DISTINCT service)::integer AS services_targeted
       FROM attacks`
    );
    return res.json(rows[0]);
  } catch (error) {
    console.error('Failed to load stats:', error.message);
    return res.status(500).json({ error: 'Failed to load stats' });
  }
});

const port = Number(process.env.PORT) || 3000;
const server = app.listen(port, () => console.log(`HoneyNet API listening on port ${port}`));

async function shutdown() {
  server.close(async () => {
    await pool.end();
    process.exit(0);
  });
}
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
