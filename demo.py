import inspect

# 获取在函数中谁调取了该函数
import uuid


def get_caller_name():
    """
    获取调用者的名字
    :param n: 调用者的层级
    :return:
    """
    frame = inspect.currentframe()
    caller_name = frame.f_back.f_code.co_name
    print(frame.f_back.f_locals, caller_name)


def faweaas():
    a = 1
    print(get_caller_name())


if __name__ == '__main__':
    print(uuid.uuid4())
