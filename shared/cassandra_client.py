from cassandra.cluster import Cluster

class CassandraClient:
    def __init__(self, hosts):
        self.cluster = Cluster(hosts,protocol_version=4)
        self.session = self.cluster.connect()
        self.init_tables()

    def init_tables(self):
        #Crea el keyspace para el cassandra
        keyspace_query = """
            CREATE KEYSPACE IF NOT EXISTS sensor 
            WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
            """
        self.session.execute(keyspace_query)

        table_query_temperature = """
            CREATE TABLE IF NOT EXISTS sensor.temperature (
                sensor_id int,
                temperature float,
                timestamp timestamp,
                PRIMARY KEY (sensor_id, timestamp)
            );
            """
        self.session.execute(table_query_temperature)

        table_query_quantity = """
            CREATE TABLE IF NOT EXISTS sensor.quantity (
                type text,
                quantity counter,
                PRIMARY KEY (type)
            );
            """
        self.session.execute(table_query_quantity)

        table_query_battery = """
            CREATE TABLE IF NOT EXISTS sensor.battery (
                sensor_id int,
                battery_level float,
                timestamp timestamp,
                PRIMARY KEY (sensor_id, timestamp)
            );
            """
        self.session.execute(table_query_battery)


    def get_session(self):
        return self.session

    def close(self):
        self.cluster.shutdown()

    def execute(self, query):
        return self.get_session().execute(query)

    def get_values(self, query, type):

        results = self.session.execute(query)

        sensors = []

        if type == "temperature":
            for row in results:
                sensor = {}
                sensor['id'] = row.sensor_id
                sensor['values'] = [
                    {'max_temperature': row.max_temp,
                     'min_temperature': row.min_temp,
                     'average_temperature': row.avg_temp
                     }]
                sensors.append(sensor)
        elif type == "quantity":
            for row in results:
                sensor = {}
                sensor['type'] = row.type
                sensor['quantity'] = row.quantity
                sensors.append(sensor)
        elif type == "battery":
            for row in results:
                sensor = {}
                sensor['id'] = row.sensor_id
                sensor['battery_level'] = round(row.battery_level, 2)
                sensors.append(sensor)


        result_json = {'sensors': sensors}

        return result_json