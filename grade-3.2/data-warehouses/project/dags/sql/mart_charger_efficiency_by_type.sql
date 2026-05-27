INSERT INTO mart_charger_efficiency
SELECT
    c.type              AS charger_type,
    d.month,
    d.year,
    COUNT(*)            AS total_sessions,
    AVG(f.charging_rate_kwh)        AS avg_rate_kw,
    AVG(f.charging_cost_kwh)        AS avg_cost,
    AVG(f.ambient_temperature_celsius) AS avg_temp
FROM facts_charges f
JOIN dim_charger c ON c.id = f.charger_id
JOIN dim_time    t ON t.id = f.start_time
JOIN dim_date    d ON d.id = t.date_id
GROUP BY 1, 2, 3;
