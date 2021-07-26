import argparse
import logging
import os
import signal
import sys
import socket
from concurrent import futures
from functools import partial

import grpc
from loguru import logger

BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, BASE_DIR)

from user_srv.proto import user_pb2_grpc
from user_srv.handler.user import UserService
from common.grpc_health.v1 import health_pb2_grpc
from common.grpc_health.v1 import health
from common.register import consul
from user_srv.settings import settings


def on_exit(signal, frame, service_id):
    logger.info(f"注销{service_id}服务")
    consul.ConsulRegister(host=settings.CONSUL_HOST, port=settings.CONSUL_PORT).deregister(service_id=service_id)
    logger.info(f"注销{service_id}成功")
    logger.info("进程中断", signal, frame)
    sys.exit(0)


def get_free_tcp_port():
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind(("", 0))
    _, port = tcp.getsockname()
    tcp.close()
    return port


def get_ip():
    print(socket.gethostbyname_ex(socket.getfqdn(socket.gethostname())))


def server():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ip",
        nargs="?",
        type=str,
        default="192.168.204.1",
        help="binding ip"
    )
    parser.add_argument(
        "--port",
        nargs="?",
        type=int,
        default=0,
        help="the listing port"
    )
    args = parser.parse_args()
    if args.port == 0:
        args.port = get_free_tcp_port()

    logger.add("logs/user_srv.log", encoding="utf-8")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # 注册用户服务
    user_pb2_grpc.add_UserServicer_to_server(UserService(), server)
    # 注册健康检查
    health_pb2_grpc.add_HealthServicer_to_server(health.HealthServicer(), server)

    server.add_insecure_port(f'{args.ip}:{args.port}')
    import uuid
    service_id = str(uuid.uuid1())

    # 主进程退出信号监听
    """
    windows下支持的信号有限
        SIGINT  ctrl+c中断
        SIGTERM kill发出的软件终止
    """
    signal.signal(signal.SIGINT, partial(on_exit, service_id=service_id))
    signal.signal(signal.SIGTERM, partial(on_exit, service_id=service_id))

    logger.info(f"启动服务：{args.ip}:{args.port}")
    server.start()

    logger.info("服务注册开始")
    register = consul.ConsulRegister(host=settings.CONSUL_HOST, port=settings.CONSUL_PORT)
    if not register.register(
            name=settings.SERVICE_NAME, id=service_id, address=args.ip, port=args.port, tags=settings.SERVICE_TAGS
    ):
        logger.info("服务注册失败")
        sys.exit(0)
    logger.info("服务注册成功")

    server.wait_for_termination()


if __name__ == '__main__':
    get_ip()
    logging.basicConfig()
    # 监听配置文件变化
    settings.client.add_config_watcher(settings.NACOS["DataId"], settings.NACOS["Group"], settings.update_cfg)
    server()
