-- "Which charger types are most efficient across seasons?"
CREATE TABLE IF NOT EXISTS mart_charger_efficiency (
    charger_type    TEXT,
    month           INT,
    year            INT,
    total_sessions  BIGINT,
    avg_rate_kw     FLOAT,
    avg_cost        FLOAT,
    avg_temp        FLOAT
);

TRUNCATE mart_charger_efficiency;

-- "How much energy was consumed and revenue generated per location per month?"
CREATE TABLE IF NOT EXISTS mart_monthly_by_location (
    year_month      DATE,
    location_name   TEXT,
    total_sessions  BIGINT,
    total_energy    FLOAT,
    total_cost      FLOAT,
    avg_duration    FLOAT
);

TRUNCATE mart_monthly_by_location;

-- "When do different user types charge, and how efficiently?"
CREATE TABLE IF NOT EXISTS mart_usage_by_membership (
    membership_type     TEXT,
    time_of_day         TEXT,
    total_sessions      BIGINT,
    avg_energy          FLOAT,
    avg_battery_gain    FLOAT
);

TRUNCATE mart_usage_by_membership;
