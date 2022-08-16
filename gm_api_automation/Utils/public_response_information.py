from enum import Enum


class StatusCodeEnum(Enum):
    """
    Enum for status codes
    """
    Ok = (200, '操作成功', True)
    Project_Create_Success = (200, '项目创建成功', True)
    Project_Create_Failed = (400, '项目创建失败', False)
    Project_Update_Success = (200, '项目更新成功', True)
    Project_Update_Failed = (400, '项目更新失败', False)
    Project_Delete_Success = (200, '项目删除成功', True)
    Project_Delete_Failed = (400, '项目删除失败', False)
    Project_Not_Found = (404, '项目不存在', False)
    Project_Not_Found_Or_Deleted = (404, '项目不存在或已删除', False)
    Project_Not_Found_Or_Deleted_Or_Not_Owner = (404, '项目不存在或已删除或不是项目所有者', False)
    TestCase_Directory_Create_Success = (200, '目录创建成功', True)
    TestCase_Directory_Create_Failed = (400, '目录创建失败', False)
    TestCase_Directory_Update_Success = (200, '目录更新成功', True)
    TestCase_Directory_Update_Failed = (400, '目录更新失败', False)
    TestCase_Directory_Delete_Success = (200, '目录删除成功', True)
    TestCase_Directory_Delete_Failed = (400, '目录删除失败', False)
    TestCase_Directory_Not_Found = (404, '目录不存在', False)
    Auth_Failed = (401, '认证失败', False)
    Token_Expired = (401, 'token过期', False)
    Pwd_Error = (400, '密码错误', False)
    CPwd_Error = (400, '两次密码不一致', False)
    User_Not_Found = (404, '用户不存在', False)
    REGISTER_FAILED_ERROR = (400, '注册失败', False)
    REGISTER_SUCCESS = (200, '注册成功', True)
    USER_EXIST = (400, '用户已存在', False)
    InterFaces_Create_Success = (200, '接口创建成功', True)
    InterFaces_Create_Failed = (400, '接口创建失败', False)
    InterFaces_Update_Success = (200, '接口更新成功', True)
    InterFaces_Update_Failed = (400, '接口更新失败', False)
    InterFaces_Delete_Success = (200, '接口删除成功', True)
    InterFaces_Delete_Failed = (400, '接口删除失败', False)
    InterFaces_Not_Found = (404, '接口不存在', False)

    @property
    def code(self):
        """
        获取状态码
        """
        return self.value[0]

    @property
    def message(self):
        """
        获取状态码对应的提示信息
        """
        return self.value[1]

    @property
    def is_success(self):
        """
        获取状态码对应的是否成功标识
        """
        return self.value[2]
