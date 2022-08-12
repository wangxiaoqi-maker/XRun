
class PublicResponseInformation(object):
    # 储存公共响应信息和状态码
    def __init__(self):
        self.status_code = None
        self.message = None

    def set_status_code(self, status_code):
        self.status_code = status_code

