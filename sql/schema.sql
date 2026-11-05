PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS channels (
    channel_id INTEGER PRIMARY KEY,
    channel_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id INTEGER PRIMARY KEY,
    campaign_name TEXT NOT NULL UNIQUE,
    campaign_type TEXT NOT NULL,
    channel_id INTEGER NOT NULL REFERENCES channels(channel_id),
    budget REAL NOT NULL CHECK (budget >= 0),
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    region TEXT NOT NULL,
    segment TEXT NOT NULL,
    signup_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS marketing_spend (
    campaign_id INTEGER NOT NULL REFERENCES campaigns(campaign_id),
    activity_date TEXT NOT NULL,
    spend REAL NOT NULL CHECK (spend >= 0),
    impressions INTEGER NOT NULL CHECK (impressions >= 0),
    clicks INTEGER NOT NULL CHECK (clicks >= 0),
    PRIMARY KEY (campaign_id, activity_date)
);

CREATE TABLE IF NOT EXISTS leads (
    lead_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    campaign_id INTEGER NOT NULL REFERENCES campaigns(campaign_id),
    lead_date TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversions (
    conversion_id INTEGER PRIMARY KEY,
    lead_id INTEGER NOT NULL UNIQUE REFERENCES leads(lead_id),
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    campaign_id INTEGER NOT NULL REFERENCES campaigns(campaign_id),
    conversion_date TEXT NOT NULL,
    revenue REAL NOT NULL CHECK (revenue >= 0)
);

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER PRIMARY KEY,
    conversion_id INTEGER NOT NULL UNIQUE REFERENCES conversions(conversion_id),
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    transaction_date TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount >= 0)
);

CREATE TABLE IF NOT EXISTS recommendation_actions (
    recommendation_key TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'Pending'
        CHECK (status IN ('Pending', 'In Progress', 'Completed')),
    manager_decision TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_marketing_spend_date ON marketing_spend(activity_date);
CREATE INDEX IF NOT EXISTS idx_leads_campaign_date ON leads(campaign_id, lead_date);
CREATE INDEX IF NOT EXISTS idx_conversions_campaign_date ON conversions(campaign_id, conversion_date);
CREATE INDEX IF NOT EXISTS idx_conversions_customer ON conversions(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_customer ON transactions(customer_id);
