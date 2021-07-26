import time

from rocketmq.client import PushConsumer, ConsumeStatus

topic = "testTopic"


def callback(msg):
    print(msg.id, msg.body, msg.get_property("name"))
    return ConsumeStatus.CONSUME_SUCCESS


def start_consume_message():
    consumer = PushConsumer("python_consumer")
    consumer.set_name_server_address("127.0.0.1:9876")
    consumer.subscribe(topic, callback=callback)
    print("开始消费消息")
    consumer.start()

    while True:
        time.sleep(3600)


if __name__ == '__main__':
    start_consume_message()
