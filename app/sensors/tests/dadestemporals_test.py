import time
from fastapi.testclient import TestClient
import pytest
from app.main import app
from shared.cassandra_client import CassandraClient
from shared.redis_client import RedisClient
from shared.mongodb_client import MongoDBClient
from shared.elasticsearch_client import ElasticsearchClient
from shared.timescale import Timescale

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

def test_temporals_create_sensor_temperatura():
    """A sensor can be properly created"""
    response = client.post("/sensors", json={"name": "Sensor Temperatura 1", "latitude": 1.0, "longitude": 1.0, "type": "Temperatura", "mac_address": "00:00:00:00:00:00", "manufacturer": "Dummy", "model":"Dummy Temp", "serie_number": "0000 0000 0000 0000", "firmware_version": "1.0", "description": "Sensor de temperatura model Dummy Temp del fabricant Dummy"})
    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "Sensor Temperatura 1", "latitude": 1.0, "longitude": 1.0, "type": "Temperatura", "mac_address": "00:00:00:00:00:00", "manufacturer": "Dummy", "model":"Dummy Temp", "serie_number": "0000 0000 0000 0000", "firmware_version": "1.0", "description": "Sensor de temperatura model Dummy Temp del fabricant Dummy"}
     
def test_temporals_create_sensor_velocitat_1():
    response = client.post("/sensors", json={"name": "Velocitat 1", "latitude": 1.0, "longitude": 1.0, "type": "Velocitat", "mac_address": "00:00:00:00:00:01", "manufacturer": "Dummy", "model":"Dummy Vel", "serie_number": "0000 0000 0000 0000", "firmware_version": "1.0", "description": "Sensor de velocitat model Dummy Vel del fabricant Dummy cruïlla 1"})
    assert response.status_code == 200
    assert response.json() == {"id": 2, "name": "Velocitat 1", "latitude": 1.0, "longitude": 1.0, "type": "Velocitat", "mac_address": "00:00:00:00:00:01", "manufacturer": "Dummy", "model":"Dummy Vel", "serie_number": "0000 0000 0000 0000", "firmware_version": "1.0", "description": "Sensor de velocitat model Dummy Vel del fabricant Dummy cruïlla 1"}

def test_temporals_create_sensor_velocitat_2():
    response = client.post("/sensors", json={"name": "Velocitat 2", "latitude": 2.0, "longitude": 2.0, "type": "Velocitat", "mac_address": "00:00:00:00:00:02", "manufacturer": "Dummy", "model":"Dummy Vel", "serie_number": "0000 0000 0000 0000", "firmware_version": "1.0", "description": "Sensor de velocitat model Dummy Vel del fabricant Dummy cruïlla 2"})
    assert response.status_code == 200
    assert response.json() == {"id": 3, "name": "Velocitat 2", "latitude": 2.0, "longitude": 2.0, "type": "Velocitat", "mac_address": "00:00:00:00:00:02", "manufacturer": "Dummy", "model":"Dummy Vel", "serie_number": "0000 0000 0000 0000", "firmware_version": "1.0", "description": "Sensor de velocitat model Dummy Vel del fabricant Dummy cruïlla 2"}

def test_temporals_post_sensor_data_dia_1():
    response = client.post("/sensors/1/data", json={"temperature": 1.0, "humidity": 1.0, "battery_level": 1.0, "last_seen": "2020-01-01T00:00:00.000Z"})
    assert response.status_code == 200

def test_temporals_post_sensor_data_dia_2():
    response = client.post("/sensors/1/data", json={"temperature": 15.0, "humidity": 1.0, "battery_level": 1.0, "last_seen": "2020-01-02T00:00:00.000Z"})
    assert response.status_code == 200

def test_temporals_post_sensor_data_dia_3():
    response = client.post("/sensors/1/data", json={"temperature": 18.0, "humidity": 1.0, "battery_level": 0.9, "last_seen": "2020-01-03T00:00:00.000Z"})
    assert response.status_code == 200

def test_temporals_post_sensor_data_veolicitat_hora_1():
    response = client.post("/sensors/2/data", json={"velocity": 1.0, "battery_level": 1.0, "last_seen": "2020-01-01T00:00:00.000Z"})
    assert response.status_code == 200

def test_temporals_post_sensor_data_veolicitat_hora_2():
    response = client.post("/sensors/2/data", json={"velocity": 15.0, "battery_level": 1.0, "last_seen": "2020-01-01T01:00:00.000Z"})
    assert response.status_code == 200

def test_temporals_post_sensor_data_veolicitat_hora_3():
    response = client.post("/sensors/2/data", json={"velocity": 18.0, "battery_level": 0.9, "last_seen": "2020-01-01T02:00:00.000Z"})
    assert response.status_code == 200

def test_temporals_post_sensor_data_veolicitat_week_1():
    response = client.post("/sensors/3/data", json={"velocity": 1.0, "battery_level": 1.0, "last_seen": "2020-01-01T00:00:00.000Z"})
    assert response.status_code == 200

def test_temporals_post_sensor_data_veolicitat_week_2():
    response = client.post("/sensors/3/data", json={"velocity": 15.0, "battery_level": 1.0, "last_seen": "2020-01-08T00:00:00.000Z"})
    assert response.status_code == 200

def test_temporals_post_sensor_data_veolicitat_week_3():
    response = client.post("/sensors/3/data", json={"velocity": 18.0, "battery_level": 0.9, "last_seen": "2020-01-15T00:00:00.000Z"})
    assert response.status_code == 200

def test_temporals_get_sensor_data_1_day():
    """We can get a sensor by its id"""
    response = client.get("/sensors/1/data?from=2020-01-01T00:00:00.000Z&to=2020-01-03T00:00:00.000Z&bucket=day")
    assert response.status_code == 200
    json = response.json()
    assert len(json) == 3

def test_temporals_get_sensor_data_1_week():
    response = client.get("/sensors/1/data?from=2020-01-01T00:00:00.000Z&to=2020-01-07T00:00:00.000Z&bucket=week")
    assert response.status_code == 200
    json = response.json()
    assert len(json) == 1

def test_temporals_get_sensor_data_2_hour():
    response = client.get("/sensors/2/data?from=2020-01-01T00:00:00.000Z&to=2020-01-01T02:00:00.000Z&bucket=hour")
    assert response.status_code == 200
    json = response.json()
    assert len(json) == 3

def test_temporals_get_sensor_data_2_day():
    response = client.get("/sensors/2/data?from=2020-01-01T00:00:00.000Z&to=2020-01-02T00:00:00.000Z&bucket=day")
    assert response.status_code == 200
    json = response.json()
    assert len(json) == 1

def test_temporals_get_sensor_data_3_week():
    response = client.get("/sensors/3/data?from=2020-01-01T00:00:00.000Z&to=2020-01-15T00:00:00.000Z&bucket=week")
    assert response.status_code == 200
    json = response.json()
    assert len(json) == 3

def test_temporals_get_sensor_data_3_month():
    response = client.get("/sensors/3/data?from=2020-01-01T00:00:00.000Z&to=2020-01-31T00:00:00.000Z&bucket=month")
    assert response.status_code == 200
    json = response.json()
    assert len(json) == 1
    
def test_temporals_post_sensor_data_not_exists():
    response = client.post("/sensors/4/data", json={"temperature": 1.0, "humidity": 1.0, "battery_level": 1.0, "last_seen": "2020-01-01T00:00:00.000Z"})
    assert response.status_code == 404
    assert "Sensor not found" in response.text

def test_temporals_get_sensor_data_not_exists():
    response = client.get("/sensors/4/data")
    assert response.status_code == 404
    assert "Sensor not found" in response.text
