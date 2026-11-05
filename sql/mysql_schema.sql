-- Optional MySQL 8.0+ schema for a managed/shared database.
-- The Streamlit demo itself runs on SQLite; this file is a migration starting point.

CREATE TABLE IF NOT EXISTS channels (
    channel_id INT UNSIGNED PRIMARY KEY,
    channel_name VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id INT UNSIGNED PRIMARY KEY,
    campaign_name VARCHAR(180) NOT NULL UNIQUE,
    campaign_type VARCHAR(60) NOT NULL,
    channel_id INT UNSIGNED NOT NULL,
    budget DECIMAL(14, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(30) NOT NULL,
    CONSTRAINT fk_campaign_channel FOREIGN KEY (channel_id) REFERENCES channels(channel_id),
    CONSTRAINT chk_campaign_budget CHECK (budget >= 0),
    INDEX idx_campaign_channel (channel_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS customers (
    customer_id INT UNSIGNED PRIMARY KEY,
    region VARCHAR(80) NOT NULL,
    segment VARCHAR(80) NOT NULL,
    signup_date DATE NOT NULL,
    INDEX idx_customer_segment_region (segment, region)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS marketing_spend (
    campaign_id INT UNSIGNED NOT NULL,
    activity_date DATE NOT NULL,
    spend DECIMAL(14, 2) NOT NULL,
    impressions BIGINT UNSIGNED NOT NULL,
    clicks BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (campaign_id, activity_date),
    CONSTRAINT fk_spend_campaign FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id),
    CONSTRAINT chk_spend_nonnegative CHECK (spend >= 0),
    INDEX idx_spend_date (activity_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS leads (
    lead_id BIGINT UNSIGNED PRIMARY KEY,
    customer_id INT UNSIGNED NOT NULL,
    campaign_id INT UNSIGNED NOT NULL,
    lead_date DATE NOT NULL,
    status VARCHAR(30) NOT NULL,
    CONSTRAINT fk_lead_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    CONSTRAINT fk_lead_campaign FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id),
    INDEX idx_lead_campaign_date (campaign_id, lead_date),
    INDEX idx_lead_customer (customer_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS conversions (
    conversion_id BIGINT UNSIGNED PRIMARY KEY,
    lead_id BIGINT UNSIGNED NOT NULL UNIQUE,
    customer_id INT UNSIGNED NOT NULL,
    campaign_id INT UNSIGNED NOT NULL,
    conversion_date DATE NOT NULL,
    revenue DECIMAL(14, 2) NOT NULL,
    CONSTRAINT fk_conversion_lead FOREIGN KEY (lead_id) REFERENCES leads(lead_id),
    CONSTRAINT fk_conversion_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    CONSTRAINT fk_conversion_campaign FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id),
    CONSTRAINT chk_conversion_revenue CHECK (revenue >= 0),
    INDEX idx_conversion_campaign_date (campaign_id, conversion_date),
    INDEX idx_conversion_customer (customer_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS products (
    product_id INT UNSIGNED PRIMARY KEY,
    product_name VARCHAR(120) NOT NULL UNIQUE,
    category VARCHAR(80) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id BIGINT UNSIGNED PRIMARY KEY,
    conversion_id BIGINT UNSIGNED NOT NULL UNIQUE,
    customer_id INT UNSIGNED NOT NULL,
    product_id INT UNSIGNED NOT NULL,
    transaction_date DATE NOT NULL,
    amount DECIMAL(14, 2) NOT NULL,
    CONSTRAINT fk_transaction_conversion FOREIGN KEY (conversion_id) REFERENCES conversions(conversion_id),
    CONSTRAINT fk_transaction_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    CONSTRAINT fk_transaction_product FOREIGN KEY (product_id) REFERENCES products(product_id),
    CONSTRAINT chk_transaction_amount CHECK (amount >= 0),
    INDEX idx_transaction_customer (customer_id),
    INDEX idx_transaction_date (transaction_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS recommendation_actions (
    recommendation_key VARCHAR(180) PRIMARY KEY,
    status ENUM('Pending', 'In Progress', 'Completed') NOT NULL DEFAULT 'Pending',
    manager_decision TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;
