import sys
import os
import logging
import signal
import argparse
import socket
from concurrent import futures
from functools import partial

import grpc
from loguru import logger

BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, BASE_DIR)

from userop_srv.proto import message_pb2, message_pb2_grpc
from userop_srv.proto import address_pb2, address_pb2_grpc
from userop_srv.proto import userfav_pb2, userfav_pb2_grpc
from userop_srv.handler.message import MessageServicer
from userop_srv.handler.address import AddressServicer
from userop_srv.handler.user_fav import UserFavServicer

from common.grpc_health.v1 import health_pb2_grpc, health_pb2
from common.grpc_health.v1 import health
from common.register import consul
from userop_srv.settings import settings


def on_exit(signo, frame, service_id):
    register = consul.ConsulRegister(settings.CONSUL_HOST, settings.CONSUL_PORT)
    logger.info(f"注销 {service_id} 服务")
    register.deregister(service_id=service_id)
    logger.info("注销成功")
    sys.exit(0)


def get_free_tcp_port():
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind(("", 0))
    _, port = tcp.getsockname()
    tcp.close()
    return port


def serve():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip',
                        nargs="?",
                        type=str,
                        default="192.168.204.1",
                        help="binding ip"
                        )
    parser.add_argument('--port',
                        nargs="?",
                        type=int,
                        default=0,
                        help="the listening port"
                        )
    args = parser.parse_args()
    
    if args.port == 0:
        port = get_free_tcp_port()
    else:
        port = args.port

    logger.add("logs/userop_srv_{time}.log")

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    #注册服务
    message_pb2_grpc.add_MessageServicer_to_server(MessageServicer(), server)
    address_pb2_grpc.add_AddressServicer_to_server(AddressServicer(), server)
    userfav_pb2_grpc.add_UserFavServicer_to_server(UserFavServicer(), server)

    #注册健康检查
    health_pb2_grpc.add_HealthServicer_to_server(health.HealthServicer(), server)

    server.add_insecure_port(f'{args.ip}:{port}')

    import uuid
    service_id = str(uuid.uuid1())

    #主进程退出信号监听
    """
        windows下支持的信号是有限的：
            SIGINT ctrl+C终端
            SIGTERM kill发出的软件终止
    """
    signal.signal(signal.SIGINT, partial(on_exit, service_id=service_id))
    signal.signal(signal.SIGTERM, partial(on_exit, service_id=service_id))

    logger.info(f"启动服务: {args.ip}:{port}")
    server.start()

    logger.info(f"服务注册开始")
    register = consul.ConsulRegister(settings.CONSUL_HOST, settings.CONSUL_PORT)
    if not register.register(name=settings.SERVICE_NAME, id=service_id,
                      address=args.ip, port=port, tags=settings.SERVICE_TAGS, check=None):
        logger.info(f"服务注册失败")

        sys.exit(0)
    logger.info(f"服务注册成功")
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    settings.client.add_config_watcher(settings.NACOS["DataId"], settings.NACOS["Group"], settings.update_cfg)
    serve()