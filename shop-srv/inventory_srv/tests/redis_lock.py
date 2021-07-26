import redis


class Lock:
    def __init__(self, name):
        self.redis_client = redis.Redis(host="127.0.0.1")
        self.name = name

    def acquire(self):
        while True:
            import time

            if self.redis_client.get(self.name):
                return True
            time.sleep(1)

    def release(self):
        self.redis_client.delete(self.name)


if __name__ == '__main__':
    pass