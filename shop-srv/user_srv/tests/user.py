import time

import grpc

from user_srv.proto import user_pb2, user_pb2_grpc


class UserTest:
    def __init__(self):
        channel = grpc.insecure_channel("127.0.0.1:50051")
        self.stub = user_pb2_grpc.UserStub(channel)

    def user_list(self):
        rsp: user_pb2.UserListResponse = self.stub.GetUserList(user_pb2.PageInfo(pn=2, pSize=2))
        print(rsp.total)
        for user in rsp.data:
            print(user.mobile, user.birthDay)

    def get_user_by_id(self, id):
        rsp: user_pb2.UserInfoResponse = self.stub.GetUserById(user_pb2.IdRequest(id=id))
        print(rsp.mobile, rsp.nickName)

    def get_user_by_mobile(self, mobile):
        rsp: user_pb2.UserInfoResponse = self.stub.GetUserByMobile(user_pb2.MobileRequest(mobile=mobile))
        print(rsp.mobile)

    def create_user(self, nick_name, mobile, password):
        rsp: user_pb2.UserInfoResponse = self.stub.CreateUser(
            user_pb2.CreateUserInfo(
                nickName=nick_name,
                mobile=mobile,
                passWord=password
            )
        )
        print(rsp.id)
        print(rsp.mobile)

    def update_user(self, id, nick_name, gender, birth_day):
        rsq = self.stub.UpdateUser(
            user_pb2.UpdateUserInfo(
                id=id,
                nickName=nick_name,
                gender=gender,
                birthDay=birth_day
            )
        )


if __name__ == '__main__':
    user = UserTest()
    user.user_list()
    print("##" * 10)
    user.get_user_by_id(1)
    # user.get_user_by_id(100)
    print("##" * 10)
    user.get_user_by_mobile("18782222220")
    print("##" * 10)
    # user.create_user("test", "13611111111", "123456")
    print("##" * 10)
    user.update_user(1, "test123", "male", int(time.time()))
    user.get_user_by_id(1)
