-- Analytics examples queries for the weather table

SELECT
    date,
    avg(air_temperature_avg) AS avg_temp,
    avg(wind_speed_avg) AS avg_wind
FROM weather
WHERE date >= current_date - interval '30 days'
GROUP BY date
ORDER BY date;

-- Hottest stations on a given day
SELECT
    station_id,
    air_temperature_max
FROM weather
WHERE date = current_date - 1
ORDER BY air_temperature_max DESC
LIMIT 20;
