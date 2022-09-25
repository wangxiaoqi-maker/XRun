import unittest

import ddt

from gm_api_automation.Utils.loguru_util import logger
from gm_api_automation.middleware import ddt_util


class Test(unittest.TestCase):
    pass


test_case = [1, 2, 34]
for i in test_case:
    def test(self, data=i):
        try:
            self.assertEqual(data, 1)
        except AssertionError as e:
            logger.info(f"失败用例报错为{e}")
            raise e


    setattr(Test, f'test_{i}', test)

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(Test('test'))
    unittest.TextTestRunner().run(suite)
