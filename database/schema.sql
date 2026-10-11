-- HoneyNet database schema. Safe to run again after initial setup.
CREATE TABLE IF NOT EXISTS attacks (
    id SERIAL PRIMARY KEY,
    attacker_ip VARCHAR(45),
    service VARCHAR(50),
    port INTEGER,
    payload TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS nodes (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(100) UNIQUE,
    name VARCHAR(200),
    status VARCHAR(20) DEFAULT 'online',
    last_seen TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attacks_timestamp_desc ON attacks (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_attacks_attacker_ip ON attacks (attacker_ip);

INSERT INTO nodes (node_id, name)
VALUES ('node-001', 'Laptop Honeypot')
ON CONFLICT (node_id) DO NOTHING;
