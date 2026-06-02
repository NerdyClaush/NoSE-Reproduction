param(
    [string]$DataDir = "D:\Database_Project\NoSE-Reproduction\experiments\data\air_pollution_synthetic"
)

$ErrorActionPreference = "Stop"

$projectRoot = "D:\Database_Project\NoSE-Reproduction"
$containerDir = "/air_pollution_data"

docker compose -f "$projectRoot\docker-compose.yml" up -d cassandra-rubis

docker compose -f "$projectRoot\docker-compose.yml" exec -T cassandra-rubis mkdir -p $containerDir
docker compose -f "$projectRoot\docker-compose.yml" cp "$DataDir\schema.cql" "cassandra-rubis:$containerDir/schema.cql"
docker compose -f "$projectRoot\docker-compose.yml" cp "$DataDir\measurements_by_pollutant.csv" "cassandra-rubis:$containerDir/measurements_by_pollutant.csv"
docker compose -f "$projectRoot\docker-compose.yml" cp "$DataDir\measurements_by_station_month.csv" "cassandra-rubis:$containerDir/measurements_by_station_month.csv"
docker compose -f "$projectRoot\docker-compose.yml" cp "$DataDir\measurements_by_station_pollutant.csv" "cassandra-rubis:$containerDir/measurements_by_station_pollutant.csv"

docker compose -f "$projectRoot\docker-compose.yml" exec -T cassandra-rubis cqlsh 127.0.0.1 9042 -f "$containerDir/schema.cql"

docker compose -f "$projectRoot\docker-compose.yml" exec -T cassandra-rubis cqlsh 127.0.0.1 9042 -e "COPY air_pollution.measurements_by_pollutant (pollutant_id, month, measurement_id, average_value, note, station_id, region_name, station_type) FROM '$containerDir/measurements_by_pollutant.csv' WITH HEADER = true;"

docker compose -f "$projectRoot\docker-compose.yml" exec -T cassandra-rubis cqlsh 127.0.0.1 9042 -e "COPY air_pollution.measurements_by_station_month (station_id, month, measurement_id, pollutant_id, average_value, pollutant_name, unit, region_name, station_type, note) FROM '$containerDir/measurements_by_station_month.csv' WITH HEADER = true;"

docker compose -f "$projectRoot\docker-compose.yml" exec -T cassandra-rubis cqlsh 127.0.0.1 9042 -e "COPY air_pollution.measurements_by_station_pollutant (station_id, pollutant_id, month, measurement_id, average_value, pollutant_name, unit, region_name, station_type, note) FROM '$containerDir/measurements_by_station_pollutant.csv' WITH HEADER = true;"

docker compose -f "$projectRoot\docker-compose.yml" exec -T cassandra-rubis cqlsh 127.0.0.1 9042 -e "SELECT COUNT(*) FROM air_pollution.measurements_by_pollutant;"
docker compose -f "$projectRoot\docker-compose.yml" exec -T cassandra-rubis cqlsh 127.0.0.1 9042 -e "SELECT COUNT(*) FROM air_pollution.measurements_by_station_month;"
docker compose -f "$projectRoot\docker-compose.yml" exec -T cassandra-rubis cqlsh 127.0.0.1 9042 -e "SELECT COUNT(*) FROM air_pollution.measurements_by_station_pollutant;"
