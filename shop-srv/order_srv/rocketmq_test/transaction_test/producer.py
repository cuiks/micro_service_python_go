import time

from rocketmq.client import TransactionMQProducer, Message, TransactionStatus

topic = "testTopic"


def create_message():
    msg = Message(topic)
    msg.set_keys("imooc")
    msg.set_tags("python")
    msg.set_property("name", "python-services")
    msg.set_body("hello mq")
    return msg


def check_callback(msg):
    # 消息回查
    # TransactionStatus.COMMIT, TransactionStatus.ROLLBACK, TransactionStatus.UNKNOWN
    print(f"事务消息回查：{msg.body.decode('utf-8')}")
    return TransactionStatus.COMMIT

def local_exec(msg, user_args):
    # TransactionStatus.COMMIT, TransactionStatus.ROLLBACK, TransactionStatus.UNKNOWN
    # 添加业务逻辑。此处返回UNKNOWN，才会执行上面的回查函数
    print("执行本地业务逻辑")
    return TransactionStatus.UNKNOWN



def send_message_transaction(count):
    # 发送事务消息
    producer = TransactionMQProducer("test", checker_callback=check_callback)
    producer.set_name_server_address("127.0.0.1:9876")

    # 首先启动producer
    producer.start()
    for n in range(count):
        msg = create_message()
        ret = producer.send_message_in_transaction(msg, local_exec)
        print(f"发送状态:{ret.status}, 消息id:{ret.msg_id}")
    print("finished")
    # 此处不能关闭
    while True:
        time.sleep(3600)

if __name__ == '__main__':
    send_message_transaction(5)