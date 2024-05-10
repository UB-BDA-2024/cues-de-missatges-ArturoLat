
CREATE TABLE IF NOT EXISTS sensor_data (
    sensor_id int NOT NULL,
    velocity float,
    temperature float,
    humidity float,
    battery_level float NOT NULL,
    last_seen timestamp NOT NULL,
    primary key(sensor_id, last_seen)
);

SELECT create_hypertable(
    'sensor_data',
    'last_seen',
    if_not_exists => true
);

CREATE MATERIALIZED VIEW
hour (
    hour,
    sensor_id,
    velocity,
    temperature,
    humidity,
    battery_level
)
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 hour', last_seen) AS hour,
    sensor_id,
    AVG(velocity),
    AVG(temperature),
    AVG(humidity),
    AVG(battery_level)
FROM sensor_data
GROUP BY hour, sensor_id
WITH NO DATA;

CREATE MATERIALIZED VIEW
day (
    day,
    sensor_id,
    velocity,
    temperature,
    humidity,
    battery_level
)
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 day', last_seen) AS day,
    sensor_id,
    AVG(velocity),
    AVG(temperature),
    AVG(humidity),
    AVG(battery_level)
FROM sensor_data
GROUP BY day, sensor_id
WITH NO DATA;

CREATE MATERIALIZED VIEW
week (
    week,
    sensor_id,
    velocity,
    temperature,
    humidity,
    battery_level
)
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 week', last_seen) AS week,
    sensor_id,
    AVG(velocity),
    AVG(temperature),
    AVG(humidity),
    AVG(battery_level)
FROM sensor_data
GROUP BY week, sensor_id
WITH NO DATA;

CREATE MATERIALIZED VIEW
month (
    month,
    sensor_id,
    velocity,
    temperature,
    humidity,
    battery_level
)
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 month', last_seen) AS month,
    sensor_id,
    AVG(velocity),
    AVG(temperature),
    AVG(humidity),
    AVG(battery_level)
FROM sensor_data
GROUP BY month, sensor_id
WITH NO DATA;

CREATE INDEX ON hour (sensor_id, hour ASC);
CREATE INDEX ON day (sensor_id, day ASC);
CREATE INDEX ON week (sensor_id, week ASC);
CREATE INDEX ON month (sensor_id, month ASC);

