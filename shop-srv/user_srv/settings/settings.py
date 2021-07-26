import json

import nacos
from playhouse.pool import PooledMySQLDatabase
from playhouse.shortcuts import ReconnectMixin
from loguru import logger


class ReconnectMysqlDatabase(ReconnectMixin, PooledMySQLDatabase):
    pass


NACOS = {
    "Host": "127.0.0.1",
    "Port": 8848,
    "NameSpace": "e26ed00c-80cb-4277-982e-8156b8ee06f0",
    "User": "nacos",
    "Password": "nacos",
    "DataId": "user-srv.json",
    "Group": "dev"
}

client = nacos.NacosClient(f"{NACOS['Host']}:{NACOS['Port']}", namespace=NACOS["NameSpace"], username=NACOS["User"],
                           password=NACOS["Password"])
# get config
data = client.get_config(NACOS["DataId"], NACOS["Group"])
data = json.loads(data)

logger.info(data)

MYSQL_DB = data["mysql"]["db"]
MYSQL_HOST = data["mysql"]["host"]
MYSQL_PORT = data["mysql"]["port"]
MYSQL_USER = data["mysql"]["user"]
MYSQL_PASSWORD = data["mysql"]["password"]

# consul配置
CONSUL_HOST = data["consul"]["host"]
CONSUL_PORT = data["consul"]["port"]

# 服务相关的配置
SERVICE_NAME = data["name"]
SERVICE_TAGS = data["tags"]

DB = ReconnectMysqlDatabase(MYSQL_DB, host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD)


def update_cfg(args):
    logger.info(f"配置文件变化: {args}")
