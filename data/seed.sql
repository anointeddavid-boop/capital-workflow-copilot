INSERT INTO funds (fund_name, strategy, vintage_year, fund_size_usd_millions) VALUES
('Atlas Real Estate Partners I', 'Real Estate', 2018, 4200),
('Atlas Real Estate Partners II', 'Real Estate', 2021, 6100),
('Summit Growth Equity III', 'Growth Equity', 2019, 2800),
('Harbor Private Equity VIII', 'Private Equity', 2017, 9500),
('Harbor Private Equity IX', 'Private Equity', 2021, 12000),
('Keystone Infrastructure Fund I', 'Infrastructure', 2020, 5300);

INSERT INTO fund_performance (fund_id, report_year, net_irr_percent, nav_usd_millions, distributions_usd_millions) VALUES
(1, 2022, 9.4, 4350, 210),
(1, 2023, 7.8, 4410, 260),
(1, 2024, 8.9, 4520, 300),
(2, 2022, 11.2, 5900, 90),
(2, 2023, 10.1, 6250, 140),
(2, 2024, 12.3, 6700, 190),
(3, 2022, 14.5, 3100, 120),
(3, 2023, 12.7, 3350, 160),
(3, 2024, 15.8, 3700, 210),
(4, 2022, 16.9, 10200, 850),
(4, 2023, 13.4, 10600, 900),
(4, 2024, 14.8, 11100, 980),
(5, 2022, 8.6, 11600, 150),
(5, 2023, 11.9, 12400, 220),
(5, 2024, 13.2, 13300, 310),
(6, 2022, 7.9, 5400, 180),
(6, 2023, 8.4, 5550, 215),
(6, 2024, 9.1, 5700, 240);
