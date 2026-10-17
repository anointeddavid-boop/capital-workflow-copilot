CREATE TABLE funds (
    fund_id SERIAL PRIMARY KEY,
    fund_name TEXT NOT NULL,
    strategy TEXT NOT NULL,
    vintage_year INTEGER NOT NULL,
    fund_size_usd_millions NUMERIC NOT NULL
);

CREATE TABLE fund_performance (
    perf_id SERIAL PRIMARY KEY,
    fund_id INTEGER NOT NULL REFERENCES funds(fund_id),
    report_year INTEGER NOT NULL,
    net_irr_percent NUMERIC NOT NULL,
    nav_usd_millions NUMERIC NOT NULL,
    distributions_usd_millions NUMERIC NOT NULL
);
