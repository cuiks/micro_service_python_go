import grpc
from common.grpc_health.v1 import health_pb2_grpc, health_pb2


class HealthTest:
    def __init__(self):
        channel = grpc.insecure_channel("127.0.0.1:50051")
        self.stub = health_pb2_grpc.HealthStub(channel)

    def test_check(self):
        res = self.stub.Check(health_pb2.HealthCheckRequest())
        print(res)


if __name__ == '__main__':
    health_test = HealthTest()
    health_test.test_check()
