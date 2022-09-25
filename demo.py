from functools import wraps
import unittest


class ParametrizedTestCase(unittest.TestCase):
    """ TestCase classes that want to be parametrized should
        inherit from this class.
    """

    def __init__(self, methodname='runtest', query_set=None, case_id=None):
        super(ParametrizedTestCase, self).__init__(methodname)
        self.query_set = query_set
        self.case_id = case_id

    @staticmethod
    def parametrize(testcase_klass, query_set=None, case_id=None):
        """ Create a suite containing all tests taken from the given
            subclass, passing them the parameter 'param'.
        """
        testloader = unittest.TestLoader()
        testnames = testloader.getTestCaseNames(testcase_klass)
        suite = unittest.TestSuite()
        for name in testnames:
            suite.addTest(testcase_klass(name, query_set=query_set, case_id=case_id))
        return suite


def data1(*args):
    def dec(func):
        @wraps(func)
        def wrapper(func):
            print(888888)
            setattr(func, "PARAMS", args)

        return wrapper

    return dec


def datas(*args):
    def dec(func):
        @wraps(func)
        def wrapper(self):
            print(self)
            return self

        return wrapper

    return dec


def get_test_data(func):
    @wraps(func)
    def wrapper(self):
        print(444)
        return func

    return wrapper


def data(*args):
    def wrapper(func):
        print(777)
        setattr(func, "PARAMS", args)
        return func

    return wrapper


def update_test_func(test_func, case_data):
    @wraps(test_func)
    def wrapper(self):
        print(444)
        return test_func(self, case_data)

    return wrapper


def ddt(cls):
    for name, func in list(cls.__dict__.items()):
        print(2222)
        if hasattr(func, "PARAMS"):
            for index, case_data in enumerate(getattr(func, "PARAMS")):
                # 生成一个用例方法名
                new_test_name = "{}_{}".format(name, index)
                # 修改原有的测试方法，设置用例数据为测试方法的参数
                test_func = update_test_func(func, case_data)
                setattr(cls, new_test_name, test_func)
            else:
                delattr(cls, name)
    return cls


@ddt
class ExecutorTest(ParametrizedTestCase):

    def setUp(self) -> None:
        print(111)

    def get_case(self):
        return 1, 2, 3

    def test_run(self):
        print("这是data", data)


if __name__ == '__main__':
    print(dir(ExecutorTest))
