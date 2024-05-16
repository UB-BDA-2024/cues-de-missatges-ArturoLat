import json

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from shared.cassandra_client import CassandraClient
from shared.database import SessionLocal
from shared.publisher import Publisher
from shared.redis_client import RedisClient
from shared.mongodb_client import MongoDBClient
from shared.elasticsearch_client import ElasticsearchClient
from shared.sensors.repository import DataCommand
from shared.timescale import Timescale
from shared.sensors import repository, schemas


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_timescale():
    ts = Timescale()
    try:
        yield ts
    finally:
        ts.close()

# Dependency to get redis client

def get_redis_client():
    redis = RedisClient(host="redis")
    try:
        yield redis
    finally:
        redis.close()

# Dependency to get mongodb client

def get_mongodb_client():
    mongodb = MongoDBClient(host="mongodb")
    try:
        yield mongodb
    finally:
        mongodb.close()



publisher = Publisher()

def get_elastic_search():
    es = ElasticsearchClient(host="elasticsearch")
    try:
        yield es
    finally:
        es.close()

# Dependency to get cassandra client
def get_cassandra_client():
    cassandra = CassandraClient(hosts=["cassandra"])
    try:
        yield cassandra
    finally:
        cassandra.close()


router = APIRouter(
    prefix="/sensors",
    responses={404: {"description": "Not found"}},
    tags=["sensors"],
)


# 🙋🏽‍♀️ Add here the route to get a list of sensors near to a given location
# 🙋🏽‍♀️ Add here the route to get a list of sensors near to a given location
@router.get("/near")
def get_sensors_near(latitude: float, longitude: float, radius: float, db: Session = Depends(get_db),mongodb_client: MongoDBClient = Depends(get_mongodb_client), redis_client: RedisClient = Depends(get_redis_client)):
    db_sensors_near = repository.get_sensors_near(mongodb=mongodb_client, latitude=latitude, longitude=longitude, radius=radius, redis=redis_client, db=db)
    if db_sensors_near == None:
        raise HTTPException(status_code=404, detail="Not sensors near")
    return db_sensors_near

# 🙋🏽‍♀️ Add here the route to search sensors by query to Elasticsearch
# Parameters:
# - query: string to search
# - size (optional): number of results to return
# - search_type (optional): type of search to perform
# - db: database session
# - mongodb_client: mongodb client
@router.get("/search")
def search_sensors(query: str, size: int = 10, search_type: str = "match", db: Session = Depends(get_db), mongodb_client: MongoDBClient = Depends(get_mongodb_client), elasticdb_client: ElasticsearchClient = Depends(get_elastic_search)):
    search_sensors = repository.search_sensors(db=db,mongodb=mongodb_client, elasticdb=elasticdb_client, query=query, size=size, search_type=search_type)
    if not search_sensors:
        raise HTTPException(status_code=404, detail="There are no sensors that matches your query")
    return search_sensors
# 🙋🏽‍♀️ Add here the route to get the temperature values of a sensor

@router.get("/temperature/values")
def get_temperature_values(db: Session = Depends(get_db), mongodb_client: MongoDBClient = Depends(get_mongodb_client), cassandra_client: CassandraClient = Depends(get_cassandra_client)):
    return repository.get_cassandra_values(db, cassandra_client, "temperature", mongodb_client)

@router.get("/quantity_by_type")
def get_sensors_quantity(db: Session = Depends(get_db), mongodb_client: MongoDBClient = Depends(get_mongodb_client), cassandra_client: CassandraClient = Depends(get_cassandra_client)):
    return repository.get_cassandra_values(db, cassandra_client, "quantity", mongodb_client)

@router.get("/low_battery")
def get_low_battery_sensors(db: Session = Depends(get_db), mongodb_client: MongoDBClient = Depends(get_mongodb_client), cassandra_client: CassandraClient = Depends(get_cassandra_client)):
    return repository.get_cassandra_values(db, cassandra_client, "battery", mongodb_client)


@router.get("")
def get_sensors(db: Session = Depends(get_db)):
    return repository.get_sensors(db)


# 🙋🏽‍♀️ Add here the route to create a sensor
@router.post("")
def create_sensor(sensor: schemas.SensorCreate, db: Session = Depends(get_db), mongodb_client: MongoDBClient = Depends(get_mongodb_client), elasticdb_client: ElasticsearchClient = Depends(get_elastic_search), cassandra_client: CassandraClient = Depends(get_cassandra_client)):
    db_sensor = repository.get_sensor_by_name(db, sensor.name)
    if db_sensor:
        raise HTTPException(status_code=400, detail="Sensor with same name already registered")


    return repository.create_sensor(db=db, sensor=sensor, mongodb=mongodb_client, elasticdb=elasticdb_client, cassandra=cassandra_client)



@router.get("/{sensor_id}")
def get_sensor(sensor_id: int, db: Session = Depends(get_db), mongodb_client: MongoDBClient = Depends(get_mongodb_client)):
    db_sensor = repository.get_sensor(db, sensor_id)
    if db_sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return repository.get_sensor_mongo(mongodb=mongodb_client, db_sensor=db_sensor)



# 🙋🏽‍♀️ Add here the route to delete a sensor
@router.delete("/{sensor_id}")
def delete_sensor(sensor_id: int, db: Session = Depends(get_db), mongodb_client: MongoDBClient = Depends(get_mongodb_client), redis_client: RedisClient = Depends(get_redis_client), timescale_client: Timescale = Depends(get_timescale), elasticdb_client: ElasticsearchClient = Depends(get_elastic_search)):

    db_sensor = repository.get_sensor(db, sensor_id)
    if db_sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")

    db_data = repository.get_data(redis=redis_client, db_sensor=db_sensor)
    if db_data is None:
        raise HTTPException(status_code=404, detail="Sensor has no data")

    return repository.delete_sensor(db=db, sensor_id=sensor_id, mongodb=mongodb_client, redis=redis_client, timescale=timescale_client, elasticdb=elasticdb_client)

# 🙋🏽‍♀️ Add here the route to update a sensor


@router.post("/{sensor_id}/data")
def record_data(sensor_id: int, data: schemas.SensorData,db: Session = Depends(get_db), redis_client: RedisClient = Depends(get_redis_client), timescale_client: Timescale = Depends(get_timescale), cassandra_client: CassandraClient = Depends(get_cassandra_client)):
    db_sensor = repository.get_sensor(db, sensor_id)
    if db_sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return repository.record_data(redis=redis_client, sensor_id=sensor_id, data=data, timescale=timescale_client, cassandra=cassandra_client)


# 🙋🏽‍♀️ Add here the route to get data from a sensor
@router.get("/{sensor_id}/data")
def get_data(sensor_id: int, db: Session = Depends(get_db) ,redis_client: RedisClient = Depends(get_redis_client), timescale_client: Timescale = Depends(get_timescale),
        from_date: str = Query(None, alias='from'),
        to_date: str = Query(None, alias='to'),
        bucket: str = Query(None, alias='bucket')):

    db_sensor = repository.get_sensor(db, sensor_id)
    if db_sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")

    if from_date is not None and to_date and not None and bucket is not None:
        return repository.get_data_timescale(timescale_client, db_sensor, from_date=from_date, to_date = to_date, bucket=bucket)
    else:
        return repository.get_data(redis=redis_client, db_sensor=db_sensor)


class ExamplePayload():
    def __init__(self, example):
        self.example = example

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
@router.post("/exemple/queue")
def exemple_queue():
    # Publish here the data to the queue
    publisher.publish(ExamplePayload("holaaaaa"))
    return {"message": "Data published to the queue"}