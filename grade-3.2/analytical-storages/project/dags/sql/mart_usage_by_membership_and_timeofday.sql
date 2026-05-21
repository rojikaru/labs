INSERT INTO mart_usage_by_membership
SELECT
    u.membership_type,
    t.time_of_day,
    COUNT(*)                                            AS total_sessions,
    AVG(f.energy_consumed_kwh)                          AS avg_energy,
    AVG(f.battery_percentage_end - f.battery_percentage_start) AS avg_battery_gain
FROM facts_charges f
JOIN dim_user u  ON u.id = f.user_id
JOIN dim_time t  ON t.id = f.start_time
GROUP BY 1, 2;
