"""
执行引擎枚举定义

提供类型安全的状态和配置选项
"""
import enum


class Platform(str, enum.Enum):
    """目标平台"""
    ANDROID = "android"
    IOS = "ios"


class CaseStatus(str, enum.Enum):
    """用例状态"""
    DRAFT = "draft"          # 草稿
    ACTIVE = "active"        # 已激活
    ARCHIVED = "archived"    # 已归档


class ExecutionStatus(str, enum.Enum):
    """执行状态"""
    PENDING = "pending"      # 等待中
    COMPILING = "compiling"  # 编译中
    RUNNING = "running"      # 执行中
    PASSED = "passed"        # 通过
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消
    TIMEOUT = "timeout"      # 超时


class ConfigScope(str, enum.Enum):
    """配置作用域"""
    GLOBAL = "global"        # 全局
    PROJECT = "project"      # 项目级
    APP = "app"              # 应用级
    CASE = "case"            # 用例级


class DataSourceType(str, enum.Enum):
    """数据源类型"""
    INLINE = "inline"        # 内联数据
    CSV = "csv"              # CSV 文件
    API = "api"              # API 端点


class CacheStrategy(str, enum.Enum):
    """缓存策略"""
    DISABLED = "disabled"        # 禁用
    READ_ONLY = "read-only"      # 只读
    READ_WRITE = "read-write"    # 读写
    WRITE_ONLY = "write-only"    # 只写


class VariableType(str, enum.Enum):
    """变量类型"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    JSON = "json"


class OnErrorAction(str, enum.Enum):
    """错误处理动作"""
    FAIL = "fail"            # 失败停止
    RETRY = "retry"          # 重试
    SKIP = "skip"            # 跳过继续
    CONTINUE = "continue"    # 继续执行


class StepType(str, enum.Enum):
    """步骤类型 - 支持的所有 Midscene API"""
    # 即时操作 (Instant Action)
    AI_TAP = "aiTap"
    AI_INPUT = "aiInput"
    AI_SCROLL = "aiScroll"
    AI_KEYBOARD_PRESS = "aiKeyboardPress"
    AI_DOUBLE_CLICK = "aiDoubleClick"
    AI_HOVER = "aiHover"
    AI_RIGHT_CLICK = "aiRightClick"
    
    # 自动规划 (Auto Planning)
    AI_ACT = "aiAct"
    AI = "ai"
    
    # 数据提取
    AI_QUERY = "aiQuery"
    AI_ASK = "aiAsk"
    AI_BOOLEAN = "aiBoolean"
    AI_NUMBER = "aiNumber"
    AI_STRING = "aiString"
    
    # 断言与等待
    AI_ASSERT = "aiAssert"
    AI_WAIT_FOR = "aiWaitFor"
    AI_LOCATE = "aiLocate"
    
    # 报告与调试
    RECORD_TO_REPORT = "recordToReport"
    SLEEP = "sleep"
    
    # 页面上下文
    FREEZE_PAGE_CONTEXT = "freezePageContext"
    UNFREEZE_PAGE_CONTEXT = "unfreezePageContext"
    
    # 平台特定 - Android
    BACK = "back"
    HOME = "home"
    RECENT_APPS = "recentApps"
    ADB_SHELL = "adbShell"
    
    # 平台特定 - iOS
    APP_SWITCHER = "appSwitcher"
    WDA_REQUEST = "wdaRequest"
    
    # 流程控制
    LAUNCH = "launch"
    CONDITION = "condition"
    LOOP = "loop"
    TRY_CATCH = "tryCatch"
    REF_CASE = "refCase"


class Priority(str, enum.Enum):
    """优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
