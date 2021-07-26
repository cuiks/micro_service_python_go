import json

import grpc
from loguru import logger
from peewee import DoesNotExist
from google.protobuf import empty_pb2
from rocketmq.client import ConsumeStatus

from inventory_srv.model.models import Inventory, InventoryHistory
from inventory_srv.proto import inventory_pb2, inventory_pb2_grpc
from inventory_srv.settings import settings
from common.lock.redis_lock import Lock


class InventoryServicer(inventory_pb2_grpc.InventoryServicer):
    @logger.catch
    def SetInv(self, request: inventory_pb2.GoodsInvInfo, context):
        """
        设置库存或修改库存
        :param request:
        :param context:
        :return:
        """
        force_insert = False
        invs = Inventory.select().where(Inventory.goods == request.goodsId)
        if not invs:
            inv = Inventory()
            inv.goods = request.goodsId
            force_insert = True
        else:
            inv = invs[0]

        inv.stocks = request.num
        inv.save(force_insert=force_insert)

        return empty_pb2.Empty()

    @logger.catch
    def InvDetail(self, request, context):
        try:
            inv = Inventory.get(Inventory.goods == request.goodsId)
            return inventory_pb2.GoodsInvInfo(goodsId=inv.goods, num=inv.stocks)
        except DoesNotExist as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("没有库存记录")
            return inventory_pb2.GoodsInvInfo()

    @logger.catch
    def Sell(self, request, context):
        inv_detail = []
        inv_history = InventoryHistory(order_sn=request.orderSn)
        with settings.DB.atomic() as txn:
            for item in request.goodsInfo:
                lock = Lock(settings.REDIS_CLIENT, f"lock:goods_{item.goodsId}", auto_renewal=True, expire=10)
                lock.acquire()
                try:
                    goods_inv = Inventory.get(Inventory.goods == item.goodsId)
                except DoesNotExist as e:
                    txn.rollback()
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    return empty_pb2.Empty()
                if goods_inv.stocks < item.num:
                    txn.rollback()
                    context.set_code(grpc.StatusCode.RESOURCE_EXHAUSTED)
                    context.set_details("库存不足")
                    return empty_pb2.Empty()
                else:
                    inv_detail.append({
                        "goods_id": item.goodsId,
                        "num": item.num
                    })
                    goods_inv.stocks -= item.num
                    goods_inv.save()
                lock.release()
            inv_history.order_inv_detail = json.dumps(inv_detail)
            inv_history.save()
            return empty_pb2.Empty()

    @logger.catch
    def Reback(self, request, context):
        """
        库存的归还：1、订单超时 2、订单创建失败 3、手动归还
        :param request:
        :param context:
        :return:
        """
        with settings.DB.atomic() as txn:
            for item in request.goodsInfo:
                try:
                    goods_inv = Inventory.get(Inventory.goods == item.goodsId)
                except DoesNotExist as e:
                    txn.rollback()
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    return empty_pb2.Empty()
                goods_inv.stocks += item.num
                goods_inv.save()
            return empty_pb2.Empty()


def reback_inv(msg):
    # 通过msg的body中的order_sn来确定库存的归还
    msg_body_str = msg.body.decode("utf-8")
    print(f"收到消息：{msg_body_str}")
    msg_body = json.loads(msg_body_str)
    order_sn = msg_body["orderSn"]
    # 为了防止没有扣减库存反而归还库存的情况
    # 使用事务，因为可能存在多个商品归还记录
    with settings.DB.atomic() as txn:
        try:
            order_inv = InventoryHistory.get(InventoryHistory.order_sn == order_sn, InventoryHistory.status == 1)
            inv_details = json.loads(order_inv.order_inv_detail)
            for item in inv_details:
                good_id = item["goods_id"]
                num = item["num"]
                Inventory.update(stocks=Inventory.stocks + num).where(Inventory.goods == good_id).execute()
            order_inv.status = 2
            order_inv.save()
            return ConsumeStatus.CONSUME_SUCCESS
        except DoesNotExist as e:
            return ConsumeStatus.CONSUME_SUCCESS
        except Exception as e:
            txn.rollback()
            return ConsumeStatus.RECONSUME_LATER
