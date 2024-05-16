import json

from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from shared.cassandra_client import CassandraClient
from shared.mongodb_client import MongoDBClient
from shared.redis_client import RedisClient
from shared.sensors import models, schemas
from shared.timescale import Timescale
from shared.elasticsearch_client import ElasticsearchClient


class DataCommand():
    def __init__(self, from_time, to_time, bucket):
        if not from_time or not to_time:
            raise ValueError("from_time and to_time must be provided")
        if not bucket:
            bucket = 'day'
        self.from_time = from_time
        self.to_time = to_time
        self.bucket = bucket


def get_sensor(db: Session, sensor_id: int) -> Optional[models.Sensor]:
    return db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()


def get_sensor_mongo(mongodb: MongoDBClient, db_sensor: models.Sensor) -> schemas.SensorCreate:
    sensor_dict = mongodb.getCollection('Sensors').find_one({'name': db_sensor.name}, {'_id': 0})
    sensor_dict.update({'id': db_sensor.id})
    return sensor_dict

def get_sensor_by_name(db: Session, name: str) -> Optional[models.Sensor]:
    return db.query(models.Sensor).filter(models.Sensor.name == name).first()

def get_sensors(db: Session, skip: int = 0, limit: int = 100) -> List[models.Sensor]:
    return db.query(models.Sensor).offset(skip).limit(limit).all()


def create_sensor(db: Session, sensor: schemas.SensorCreate, mongodb: MongoDBClient, elasticdb: ElasticsearchClient, cassandra: CassandraClient) -> models.Sensor:
    db_sensor = models.Sensor(name=sensor.name)

    db.add(db_sensor)
    db.commit()
    db.refresh(db_sensor)

    db_sensor_data = sensor.dict()
    # Guardem a MONGODB
    mongodb.insertDoc(db_sensor_data)

    elastic_data = {
        'name': sensor.name,
        'type': sensor.type,
        'description': sensor.description
    }

    elasticdb.index_document('sensors', elastic_data)

    db_sensor_dict = sensor.dict()
    db_sensor_dict.update({'id': db_sensor.id})

    cassandra.execute(f"""
                    UPDATE sensor.quantity
                    SET quantity = quantity + 1 
                    WHERE type = '{sensor.type}';
                    """
                      )

    return db_sensor_dict



def record_data(redis: RedisClient, sensor_id: int, data: schemas.SensorData, timescale: Timescale, cassandra: CassandraClient) -> schemas.SensorData:
    ts_query = """
                INSERT INTO sensor_data 
                (sensor_id, velocity, temperature, humidity, battery_level, last_seen) 
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (sensor_id, last_seen) DO UPDATE SET
                velocity = EXCLUDED.velocity,
                temperature = EXCLUDED.temperature,
                humidity = EXCLUDED.humidity,
                battery_level = EXCLUDED.battery_level;
                """
    db_sensordata = data
    ts_values =(sensor_id, data.velocity, data.temperature, data.humidity, data.battery_level, data.last_seen)
    redis.set(sensor_id, json.dumps(data.dict()))
    timescale.insert(ts_query, ts_values)
    timescale.refresh_tables()



    if data.temperature is not None:
        cassandra.execute(f"""
            INSERT INTO sensor.temperature
            (sensor_id, temperature, timestamp)
            VALUES ({sensor_id}, {data.temperature}, toTimestamp(now()))
            """
        )

    if data.battery_level is not None:
        cassandra.execute(f"""
            INSERT INTO sensor.battery
            (sensor_id, battery_level, timestamp)
            VALUES ({sensor_id}, {data.battery_level}, toTimestamp(now()))
            """
        )

    return db_sensordata


def getView(bucket: str) -> str:
    if bucket == 'year':
        return 'sensor_data_yearly'
    if bucket == 'month':
        return 'sensor_data_monthly'
    if bucket == 'week':
        return 'sensor_data_weekly'
    if bucket == 'day':
        return 'sensor_data_daily'
    elif bucket == 'hour':
        return 'sensor_data_hourly'
    else:
        raise ValueError("Invalid bucket size")


def get_data(redis: RedisClient, db_sensor: models.Sensor):
    db_data = redis.get(db_sensor.id)

    if db_data is None:
        raise HTTPException(status_code=404, detail="Sensor data not found")
    json_data = json.loads(db_data)
    # Create the dictionary for return with id or name if exists
    db_data = {
        'id': db_sensor.id,
        'name': db_sensor.name
    }
    # We add the information of get_Data at id and name
    db_data.update(json_data)
    return db_data

def get_sensors_near(mongodb: MongoDBClient, latitude: float, longitude: float, radius: float, redis: RedisClient, db: Session):
    list_near = []
    query = {"latitude": {"$gte": latitude - radius, "$lte": latitude + radius},
     "longitude": {"$gte": longitude - radius, "$lte": longitude + radius}}

    sensors = mongodb.collection.find(query)
    for sensor in sensors:
        db_sensor = get_sensor_by_name(db, sensor['name'])
        db_sensor_data = get_data(redis, db_sensor)
        list_near.append(db_sensor_data)

    return list_near

def get_data_timescale(ts: Timescale, db_sensor: models.Sensor, from_date: str, to_date: str, bucket: str) -> schemas.SensorData:
    # Query Get_Data
    ts_query = f"""
            SELECT *
            FROM {bucket}
            WHERE sensor_id = %s
                AND {bucket} BETWEEN
                    time_bucket('1 {bucket}', %s::timestamp) AND
                    time_bucket('1 {bucket}', %s::timestamp)
            ORDER BY {bucket} ASC;
        """
    ts_values = (db_sensor.id, from_date, to_date)
    return ts.getDataNear(ts_query, ts_values)

def get_cassandra_values(db:Session, cassandra:CassandraClient, type:str, mongodb:MongoDBClient):
    query_temperature = """SELECT sensor_id, AVG(temperature) AS avg_temp, MIN(temperature) AS min_temp, MAX(temperature) AS max_temp
                FROM sensor.temperature 
                GROUP BY sensor_id;"""

    query_quantity = """
            SELECT * FROM sensor.quantity;
            """

    query_battery = """
            SELECT sensor_id, battery_level
            FROM sensor.battery
            WHERE battery_level < 0.2
            ALLOW FILTERING;
            """

    result_json = {}

    if type == "temperature":
        result_json = cassandra.get_values(query_temperature, type)
    elif type == "quantity":
        result_json = cassandra.get_values(query_quantity, type)
    elif type == "battery":
        result_json = cassandra.get_values(query_battery, type)

    if type != "quantity":
        for sensor in result_json['sensors']:
            db_sensor = get_sensor(db, sensor['id'])
            mongo_sensor = get_sensor_mongo(mongodb, db_sensor)
            sensor.update(mongo_sensor)


    return result_json

def delete_sensor(db: Session, sensor_id: int, mongodb: MongoDBClient, redis: RedisClient, elasticdb: ElasticsearchClient, timescale: Timescale):
    db_sensor = db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()
    if db_sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")
    db.delete(db_sensor)
    db.commit()
    mongodb.deleteDoc(db_sensor.name)
    redis.delete(sensor_id)
    #Query per fer el delete de la id
    ts_delete_query = f"""DELETE FROM {'sensor_data'} WHERE sensor_id={sensor_id}"""
    timescale.execute(ts_delete_query)
    return db_sensor

def search_sensors(db: Session, mongodb: MongoDBClient, elasticdb: ElasticsearchClient, query:str, size:int, search_type:str):
    search_sensors_dict = []
    #We get the final query
    final_query = get_query(query, search_type)
    #We search it in Elastic DB
    query_results = elasticdb.search('sensors', final_query, size)

    # We see in the hits of the query_results
    for doc in query_results['hits']['hits']:
        db_sensor = get_sensor_by_name(db, doc['_source']['name'])
        mongo_sensor = get_sensor_mongo(mongodb, db_sensor)
        search_sensors_dict.append(mongo_sensor)

    return search_sensors_dict

#Method for get the query for search sensors that depends on the type of search
#Match and prefix have the same type of query and Similar is diferent.
def get_query(query:str, search_type:str):
    final_query = {}
    query = json.loads(query.lower())
    if search_type in ['match', 'prefix']:
        final_query = {
            'query': {
                search_type: query
            }
        }
    elif search_type == 'similar':
        key = list(query)[0]
        final_query = {
            "query": {
                "match": {
                    key: {
                        "query": query[key],
                        "fuzziness": 'auto',
                        'operator': 'and'
                    }
                }
            }
        }

    return final_query
