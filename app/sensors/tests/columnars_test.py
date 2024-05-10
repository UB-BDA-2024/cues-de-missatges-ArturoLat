from fastapi.testclient import TestClient
import pytest
from app.main import app
from shared.redis_client import RedisClient
from shared.mongodb_client import MongoDBClient
from shared.elasticsearch_client import ElasticsearchClient
from shared.timescale import Timescale
from shared.cassandra_client import CassandraClient
import time

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def clear_dbs():
    from shared.database import SessionLocal, engine
    from shared.sensors import models
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    redis = RedisClient(host="redis")
    redis.clearAll()
    redis.close()
    mongo = MongoDBClient(host="mongodb")
    mongo.clearDb("sensors")
    mongo.close()
    es = ElasticsearchClient(host="elasticsearch")
    es.clearIndex("sensors")
    ts = Timescale()
    ts.delete("sensor_data")
    ts.close()

    while True:
        try:
            cassandra = CassandraClient(["cassandra"])
            cassandra.get_session().execute("DROP KEYSPACE IF EXISTS sensor")
            cassandra.close()
            break
        except Exception as e:
            time.sleep(5)


def test_columnars_create_sensor_temperatura_1():
    """A sensor can be properly created"""
    response = client.post("/sensors", json={"name": "Sensor Temperatura 1", "latitude": 1.0, "longitude": 1.0,
                                             "type": "Temperatura", "mac_address": "00:00:00:00:00:00",
                                             "manufacturer": "Dummy", "model": "Dummy Temp",
                                             "serie_number": "0000 0000 0000 0000", "firmware_version": "1.0",
                                             "description": "Sensor de temperatura model Dummy Temp del fabricant Dummy"})
    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "Sensor Temperatura 1", "latitude": 1.0, "longitude": 1.0,
                               "type": "Temperatura", "mac_address": "00:00:00:00:00:00", "manufacturer": "Dummy",
                               "model": "Dummy Temp", "serie_number": "0000 0000 0000 0000", "firmware_version": "1.0",
                               "description": "Sensor de temperatura model Dummy Temp del fabricant Dummy"}


def test_columnars_create_sensor_velocitat_1():
    response = client.post("/sensors",
                           json={"name": "Velocitat 1", "latitude": 1.0, "longitude": 1.0, "type": "Velocitat",
                                 "mac_address": "00:00:00:00:00:01", "manufacturer": "Dummy", "model": "Dummy Vel",
                                 "serie_number": "0000 0000 0000 0000", "firmware_version": "1.0",
                                 "description": "Sensor de velocitat model Dummy Vel del fabricant Dummy cruïlla 1"})
    assert response.status_code == 200
    assert response.json() == {"id": 2, "name": "Velocitat 1", "latitude": 1.0, "longitude": 1.0, "type": "Velocitat",
                               "mac_address": "00:00:00:00:00:01", "manufacturer": "Dummy", "model": "Dummy Vel",
                               "serie_number": "0000 0000 0000 0000", "firmware_version": "1.0",
                               "description": "Sensor de velocitat model Dummy Vel del fabricant Dummy cruïlla 1"}


def test_columnars_create_sensor_velocitat_2():
    response = client.post("/sensors",
                           json={"name": "Velocitat 2", "latitude": 2.0, "longitude": 2.0, "type": "Velocitat",
                                 "mac_address": "00:00:00:00:00:02", "manufacturer": "Dummy", "model": "Dummy Vel",
                                 "serie_number": "0000 0000 0000 0000", "firmware_version": "1.0",
                                 "description": "Sensor de velocitat model Dummy Vel del fabricant Dummy cruïlla 2"})
    assert response.status_code == 200
    assert response.json() == {"id": 3, "name": "Velocitat 2", "latitude": 2.0, "longitude": 2.0, "type": "Velocitat",
                               "mac_address": "00:00:00:00:00:02", "manufacturer": "Dummy", "model": "Dummy Vel",
                               "serie_number": "0000 0000 0000 0000", "firmware_version": "1.0",
                               "description": "Sensor de velocitat model Dummy Vel del fabricant Dummy cruïlla 2"}


def test_columnars_create_sensor_temperatura_2():
    """A sensor can be properly created"""
    response = client.post("/sensors", json={"name": "Sensor Temperatura 2", "latitude": 2.0, "longitude": 2.0,
                                             "type": "Temperatura", "mac_address": "00:00:00:00:00:03",
                                             "manufacturer": "Dummy", "model": "Dummy Temp",
                                             "serie_number": "0000 0000 0000 0000", "firmware_version": "1.0",
                                             "description": "Sensor de temperatura model Dummy Temp del fabricant Dummy"})
    assert response.status_code == 200
    assert response.json() == {"id": 4, "name": "Sensor Temperatura 2", "latitude": 2.0, "longitude": 2.0,
                               "type": "Temperatura", "mac_address": "00:00:00:00:00:03", "manufacturer": "Dummy",
                               "model": "Dummy Temp", "serie_number": "0000 0000 0000 0000", "firmware_version": "1.0",
                               "description": "Sensor de temperatura model Dummy Temp del fabricant Dummy"}


def test_columnars_post_sensor_data_temperatura_1():
    response = client.post("/sensors/1/data", json={"temperature": 1.0, "humidity": 1.0, "battery_level": 1.0,
                                                    "last_seen": "2020-01-01T00:00:00.000Z"})
    assert response.status_code == 200


def test_columnars_post_sensor_data_temperatura_2():
    response = client.post("/sensors/1/data", json={"temperature": 4.0, "humidity": 1.0, "battery_level": 1.0,
                                                    "last_seen": "2020-01-01T00:00:00.000Z"})
    assert response.status_code == 200


def test_columnars_post_sensor_data_temperatura_3():
    response = client.post("/sensors/4/data", json={"temperature": 15.0, "humidity": 1.0, "battery_level": 1.0,
                                                    "last_seen": "2020-01-02T00:00:00.000Z"})
    assert response.status_code == 200


def test_columnars_post_sensor_data_temperatura_4():
    response = client.post("/sensors/4/data", json={"temperature": 17.0, "humidity": 1.0, "battery_level": 1.0,
                                                    "last_seen": "2020-01-02T00:00:00.000Z"})
    assert response.status_code == 200


def test_columnars_post_sensor_data_veolicitat_1():
    response = client.post("/sensors/2/data",
                           json={"velocity": 1.0, "battery_level": 0.1, "last_seen": "2020-01-01T00:00:00.000Z"})
    assert response.status_code == 200


def test_columnars_post_sensor_data_veolicitat_2():
    response = client.post("/sensors/3/data",
                           json={"velocity": 15.0, "battery_level": 0.15, "last_seen": "2020-01-01T01:00:00.000Z"})
    assert response.status_code == 200


def test_columnars_get_values_sensor_temperatura():
    response = client.get("/sensors/temperature/values")
    assert response.status_code == 200
    assert response.json() == {
        "sensors": [{"id": 1, "name": "Sensor Temperatura 1", "latitude": 1.0, "longitude": 1.0, "type": "Temperatura",
                     "mac_address": "00:00:00:00:00:00", "manufacturer": "Dummy", "model": "Dummy Temp",
                     "serie_number": "0000 0000 0000 0000", "firmware_version": "1.0",
                     "description": "Sensor de temperatura model Dummy Temp del fabricant Dummy",
                     "values": [{"max_temperature": 4.0, "min_temperature": 1.0, "average_temperature": 2.5}]},
                    {"id": 4, "name": "Sensor Temperatura 2", "latitude": 2.0, "longitude": 2.0,
                     "type": "Temperatura", "mac_address": "00:00:00:00:00:03", "manufacturer": "Dummy",
                     "model": "Dummy Temp", "serie_number": "0000 0000 0000 0000",
                     "firmware_version": "1.0",
                     "description": "Sensor de temperatura model Dummy Temp del fabricant Dummy",
                     "values": [{"max_temperature": 17.0, "min_temperature": 15.0,
                                 "average_temperature": 16.0}]}]}


def test_columnars_get_sensors_quantity():
    response = client.get("/sensors/quantity_by_type")
    assert response.status_code == 200
    assert response.json() == {
        "sensors": [{"type": "Temperatura", "quantity": 2}, {"type": "Velocitat", "quantity": 2}]}


def test_columnars_get_sensors_low_battery():
    response = client.get("/sensors/low_battery")
    assert response.status_code == 200
    assert response.json() == {"sensors": [
        {"id": 2, "name": "Velocitat 1", "latitude": 1.0, "longitude": 1.0, "type": "Velocitat",
         "mac_address": "00:00:00:00:00:01", "manufacturer": "Dummy", "model": "Dummy Vel",
         "serie_number": "0000 0000 0000 0000", "firmware_version": "1.0",
         "description": "Sensor de velocitat model Dummy Vel del fabricant Dummy cruïlla 1", "battery_level": 0.1},
        {"id": 3, "name": "Velocitat 2", "latitude": 2.0, "longitude": 2.0, "type": "Velocitat",
         "mac_address": "00:00:00:00:00:02", "manufacturer": "Dummy", "model": "Dummy Vel",
         "serie_number": "0000 0000 0000 0000", "firmware_version": "1.0",
         "description": "Sensor de velocitat model Dummy Vel del fabricant Dummy cruïlla 2", "battery_level": 0.15}]}
