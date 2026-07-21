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

-- Monthly average temperature trend
SELECT
    date_trunc('month', date) AS month,
    round(avg(air_temperature_avg)::numeric, 1) AS avg_temp
FROM weather
GROUP BY 1
ORDER BY 1 DESC
LIMIT 12;

-- Coldest stations on a given day
SELECT
    station_id,
    air_temperature_min
FROM weather
WHERE date = current_date - 1
ORDER BY air_temperature_min ASC
LIMIT 20;
