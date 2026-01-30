"""
知识库枚举定义
"""
from enum import Enum


class Platform(str, Enum):
    """设备平台"""
    ANDROID = "android"
    IOS = "ios"


class PageType(str, Enum):
    """页面类型"""
    LOGIN = "login"           # 登录页
    HOME = "home"             # 首页
    LIST = "list"             # 列表页
    DETAIL = "detail"         # 详情页
    FORM = "form"             # 表单页
    SEARCH = "search"         # 搜索页
    SETTINGS = "settings"     # 设置页
    PROFILE = "profile"       # 个人中心
    WEBVIEW = "webview"       # WebView 页面
    MODAL = "modal"           # 弹窗
    UNKNOWN = "unknown"       # 未知


class ElementType(str, Enum):
    """页面元素类型"""
    
    # 按钮类
    BUTTON = "button"
    SUBMIT_BUTTON = "submit_button"
    ICON_BUTTON = "icon_button"
    FAB = "fab"  # Floating Action Button
    
    # 输入类
    TEXT_INPUT = "text_input"
    PASSWORD_INPUT = "password_input"
    SEARCH_INPUT = "search_input"
    TEXTAREA = "textarea"
    
    # 选择类
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SWITCH = "switch"
    PICKER = "picker"
    SLIDER = "slider"
    
    # 导航类
    LINK = "link"
    TAB = "tab"
    TAB_BAR = "tab_bar"
    MENU_ITEM = "menu_item"
    LIST_ITEM = "list_item"
    NAVIGATION_BAR = "navigation_bar"
    BACK_BUTTON = "back_button"
    
    # 展示类
    IMAGE = "image"
    ICON = "icon"
    AVATAR = "avatar"
    CARD = "card"
    BANNER = "banner"
    
    # 特殊类
    UPLOAD = "upload"
    LOADING = "loading"
    TOAST = "toast"
    DIALOG = "dialog"


class RelationType(str, Enum):
    """元素空间关系类型"""
    RIGHT_OF = "right_of"        # 在...右方
    LEFT_OF = "left_of"          # 在...左方
    ABOVE = "above"              # 在...上方
    BELOW = "below"              # 在...下方
    INSIDE = "inside"            # 在...内部
    BESIDE = "beside"            # 在...旁边
    SAME_ROW = "same_row"        # 同一行
    SAME_COLUMN = "same_column"  # 同一列


class TransitionType(str, Enum):
    """页面跳转类型"""
    PUSH = "push"         # 压栈跳转
    POP = "pop"           # 出栈返回
    REPLACE = "replace"   # 替换当前页
    MODAL = "modal"       # 弹出模态框
    TAB = "tab"           # Tab 切换


class InteractionState(str, Enum):
    """元素交互状态"""
    CLICKABLE = "clickable"
    DISABLED = "disabled"
    HIDDEN = "hidden"
    READONLY = "readonly"


class TestPriority(str, Enum):
    """测试优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
