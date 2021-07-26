import json
import grpc
import consul

from google.protobuf import empty_pb2

from inventory_srv.proto import inventory_pb2, inventory_pb2_grpc
from inventory_srv.settings import settings


class InventoryTest:
    def __init__(self):
        # 连接grpc服务器
        c = consul.Consul(host="127.0.0.1", port=8500)
        services = c.agent.services()
        ip = ""
        port = ""
        for key, value in services.items():
            if value["Service"] == settings.SERVICE_NAME:
                ip = value["Address"]
                port = value["Port"]
                break
        if not ip:
            raise Exception()
        channel = grpc.insecure_channel(f"{ip}:{port}")
        self.inventory_stub = inventory_pb2_grpc.InventoryStub(channel)

    def setInv_test(self):
        rsp = self.inventory_stub.SetInv(inventory_pb2.GoodsInvInfo(goodsId=12, num=30))
        print(rsp)

    def invDetail_test(self):
        rsp = self.inventory_stub.InvDetail(inventory_pb2.GoodsInvInfo(goodsId=10))
        print(rsp.num)

    def sell_test(self):
        goods_list = [(10, 5), (11, 100)]
        request = inventory_pb2.SellInfo()
        for _id, num in goods_list:
            request.goodsInfo.append(inventory_pb2.GoodsInvInfo(goodsId=_id, num=num))
        self.inventory_stub.Sell(request)

    def reback_test(self):
        goods_list = [(10, 3), (11, 100)]
        request = inventory_pb2.SellInfo()
        for _id, num in goods_list:
            request.goodsInfo.append(inventory_pb2.GoodsInvInfo(goodsId=_id, num=num))
        self.inventory_stub.Reback(request)



if __name__ == '__main__':
    inv = InventoryTest()
    # inv.setInv_test()
    # inv.invDetail_test()
    # inv.sell_test()
    inv.sell_test()
    # inv.reback_test()