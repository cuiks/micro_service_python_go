from rocketmq.client import Producer, Message

topic = "testTopic"


def create_message():
    msg = Message(topic)
    msg.set_keys("imooc")
    msg.set_tags("python")
    msg.set_delay_time_level(3) #延时消息。参数为延时level
    msg.set_property("name", "python-services")
    msg.set_body("hello mq")
    return msg


def send_message_sync(count):
    producer = Producer("test")
    producer.set_name_server_address("127.0.0.1:9876")

    # 首先启动producer
    producer.start()
    for n in range(count):
        msg = create_message()
        ret = producer.send_sync(msg)
        print(f"发送状态:{ret.status}, 消息id:{ret.msg_id}")
    print("finished")
    producer.shutdown()


if __name__ == '__main__':
    # 发送普通消息
    send_message_sync(5)
