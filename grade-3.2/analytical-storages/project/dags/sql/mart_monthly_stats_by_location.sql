INSERT INTO mart_monthly_by_location
SELECT
    DATE_TRUNC('month', d.iso::date)::date  AS year_month,
    l.name                                   AS location_name,
    COUNT(*)                                 AS total_sessions,
    SUM(f.energy_consumed_kwh)               AS total_energy,
    SUM(f.charging_cost_kwh)                 AS total_cost,
    AVG(f.duration_hours)                    AS avg_duration
FROM facts_charges f
JOIN dim_time   t ON t.id = f.start_time
JOIN dim_date   d ON d.id = t.date_id
JOIN dim_charger c ON c.id = f.charger_id
JOIN dim_location l ON l.id = c.location_id
GROUP BY 1, 2;
