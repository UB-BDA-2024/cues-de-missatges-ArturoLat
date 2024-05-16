import redis


class RedisClient:
    def __init__(self, host='localhost', port=6379, db=0):
        self._host = host
        self._port = port
        self._db = db
        self._client = redis.Redis(host=self._host, port=self._port, db=self._db)

    def close(self):
        self._client.close()

    def ping(self):
        return self._client.ping()

    def get(self, key):
        return self._client.get(key)

    def set(self, key, value):
        return self._client.set(key, value)

    def delete(self, key):
        return self._client.delete(key)

    def keys(self, pattern):
        return self._client.keys(pattern)

    def clearAll(self):
        for key in self._client.keys("*"):
            self._client.delete(key)

