import psycopg2
import os


class Timescale:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.environ.get("TS_HOST"),
            port=os.environ.get("TS_PORT"),
            user=os.environ.get("TS_USER"),
            password=os.environ.get("TS_PASSWORD"),
            database=os.environ.get("TS_DBNAME"))
        self.cursor = self.conn.cursor()

    def getCursor(self):
        return self.cursor

    def close(self):
        self.cursor.close()
        self.conn.close()

    def ping(self):
        return self.conn.ping()

    def execute(self, query):
        return self.cursor.execute(query)

    def getDataNear(self, query, values):
        self.cursor.execute(query, values)
        return self.cursor.fetchall()

    def delete(self, table):
        self.cursor.execute("DELETE FROM " + table)
        self.conn.commit()

    def refresh_tables(self):
        self.conn.autocommit = True
        self.execute("CALL refresh_continuous_aggregate('hour', NULL, NULL)")
        self.execute("CALL refresh_continuous_aggregate('day', NULL, NULL)")
        self.execute("CALL refresh_continuous_aggregate('week', NULL, NULL)")
        self.execute("CALL refresh_continuous_aggregate('month', NULL, NULL)")
        self.conn.autocommit = False

    def insert(self, query, values):
        result = self.cursor.execute(query, values)
        self.conn.commit()
        return result

    def delete_sensor(self, table, sensor_id):
        self.cursor.execute(f"DELETE FROM {table} WHERE sensor_id={sensor_id}")
        self.conn.commit()
