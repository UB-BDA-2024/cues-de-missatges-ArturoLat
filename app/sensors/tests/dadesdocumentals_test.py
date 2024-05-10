import time
from fastapi.testclient import TestClient
import pytest
from app.main import app
from shared.cassandra_client import CassandraClient
from shared.elasticsearch_client import ElasticsearchClient
from shared.redis_client import RedisClient
from shared.mongodb_client import MongoDBClient
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

def test_documentals_create_sensor_temperatura():
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


def test_documentals_create_sensor_velocitat():
    response = client.post("/sensors", json={"name": "Sensor Velocitat 1", "latitude": 1.0, "longitude": 1.0, "type": "Velocitat", "mac_address": "00:00:00:00:00:01", "manufacturer": "Dummy", "model":"Dummy Vel", "serie_number": "0000 0000 0000 0000", "firmware_version": "1.0", "description": "Sensor de velocitat model Dummy Vel del fabricant Dummy cruïlla 1"})
    assert response.status_code == 200
    assert response.json() == {"id": 2, "name": "Sensor Velocitat 1", "latitude": 1.0, "longitude": 1.0, "type": "Velocitat", "mac_address": "00:00:00:00:00:01", "manufacturer": "Dummy", "model":"Dummy Vel", "serie_number": "0000 0000 0000 0000", "firmware_version": "1.0", "description": "Sensor de velocitat model Dummy Vel del fabricant Dummy cruïlla 1"}


def test_documentals_redis_connection():
    redis_client = RedisClient(host="redis")
    assert redis_client.ping()
    redis_client.close()

def test_documentals_mongodb_connection():
    mongodb_client = MongoDBClient(host="mongodb")
    assert mongodb_client.ping()
    mongodb_client.close()

def test_documentals_post_sensor_1_data_():
    response = client.post("/sensors/1/data", json={"temperature": 1.0, "humidity": 1.0, "battery_level": 1.0, "last_seen": "2020-01-01T00:00:00.000Z"})
    assert response.status_code == 200

def test_documentals_post_sensor_2_data():
    response = client.post("/sensors/2/data", json={"velocity": 45.0,"battery_level": 1.0, "last_seen": "2020-01-01T00:00:00.000Z"})
    assert response.status_code == 200

def test_documentals_get_sensor_1_data():
    """We can get a sensor by its id"""
    response = client.get("/sensors/1/data")
    assert response.status_code == 200
    json = response.json()
    assert json["id"] == 1
    assert json["name"] == "Sensor Temperatura 1"
    assert json["temperature"] == 1.0
    assert json["humidity"] == 1.0
    assert json["battery_level"] == 1.0
    assert json["last_seen"] == "2020-01-01T00:00:00.000Z"

def test_documentals_get_sensor_2_data():
    """We can get a sensor by its id"""
    response = client.get("/sensors/2/data")
    assert response.status_code == 200
    json = response.json()
    assert json["id"] == 2
    assert json["name"] == "Sensor Velocitat 1"
    assert json["velocity"] == 45.0
    assert json["battery_level"] == 1.0
    assert json["last_seen"] == "2020-01-01T00:00:00.000Z"

def test_documentals_post_sensor_data_not_exists():
    response = client.post("/sensors/3/data", json={"temperature": 1.0, "humidity": 1.0, "battery_level": 1.0, "last_seen": "2020-01-01T00:00:00.000Z"})
    assert response.status_code == 404
    assert "Sensor not found" in response.text

def test_documentals_get_sensor_data_not_exists():
    response = client.get("/sensors/3/data")
    assert response.status_code == 404
    assert "Sensor not found" in response.text

def test_documentals_update_sensor_1_data():
    response = client.post("/sensors/1/data", json={"temperature": 2.0, "humidity": 2.0, "battery_level": 1.9, "last_seen": "2020-01-01T00:00:01.000Z"})
    assert response.status_code == 200

def test_documentals_update_sensor_2_data():
    response = client.post("/sensors/2/data", json={"velocity": 46.0,"battery_level": 1.9, "last_seen": "2020-01-01T00:00:01.000Z"})
    assert response.status_code == 200

def test_documentals_get_sensor_1_data_updated():
    """We can get a sensor by its id"""
    response = client.get("/sensors/1/data")
    assert response.status_code == 200
    json = response.json()
    assert json["id"] == 1
    assert json["name"] == "Sensor Temperatura 1"
    assert json["temperature"] == 2.0
    assert json["humidity"] == 2.0
    assert json["battery_level"] == 1.9
    assert json["last_seen"] == "2020-01-01T00:00:01.000Z"


def test_documentals_get_sensor_2_data_updated():
    """We can get a sensor by its id"""
    response = client.get("/sensors/2/data")
    assert response.status_code == 200
    json = response.json()
    assert json["id"] == 2
    assert json["name"] == "Sensor Velocitat 1"
    assert json["velocity"] == 46.0
    assert json["battery_level"] == 1.9
    assert json["last_seen"] == "2020-01-01T00:00:01.000Z"


def test_documentals_get_near():
    response = client.get("/sensors/near?latitude=1.0&longitude=1.0&radius=1")
    assert response.status_code == 200
    assert response.json() == {
        {
            "id": 1,
            "name": "Sensor Temperatura 1",
            "temperature": 2.0,
            "humidity": 2.0,
            "battery_level": 1.9,
            "last_seen": "2020-01-01T00:00:01.000Z"
        },
        {
            "id": 2,
            "name": "Sensor Velocitat 1",
            "velocity": 46.0,
            "battery_level": 1.9,
            "last_seen": "2020-01-01T00:00:01.000Z"
        }}
