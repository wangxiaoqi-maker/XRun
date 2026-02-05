"""
TypeScript 编译器

门面模式（Facade），整合解析器和生成器，提供完整的编译流程
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from apps.ui_automation.execution.compiler.resolvers.variable_resolver import VariableResolver
from apps.ui_automation.execution.compiler.resolvers.element_resolver import ElementResolver
from apps.ui_automation.execution.compiler.emitters.step_emitter import StepEmitter
from apps.ui_automation.execution.models.enums import Platform


class CompileContext:
    """编译上下文，携带编译过程中的所有信息"""
    
    def __init__(self) -> None:
        self.case_id: str = ""
        self.case_name: str = ""
        self.case_description: str = ""
        self.platform: Platform = Platform.ANDROID
        self.test_name: str = ""
        
        # 变量
        self.input_variables: list[dict[str, Any]] = []
        self.resolved_variables: dict[str, Any] = {}
        self.resolved_elements: dict[str, str] = {}
        
        # 配置
        self.config: dict[str, Any] = {}
        self.model_config: dict[str, Any] | None = None
        self.cache_id: str | None = None
        self.cache_strategy: str | None = None
        
        # 启动
        self.launch_target: str | None = None
        self.launch_wait_ms: int = 3000
        
        # 数据驱动
        self.data_driven: bool = False
        self.test_data: list[dict[str, Any]] | None = None
        self.data_fields: list[str] | None = None
        self.data_label_field: str | None = None
        
        # 报告
        self.enable_report_merger: bool = False
        
        # 生成的步骤代码
        self.steps_code: str = ""


class CompileResult:
    """编译结果"""
    
    def __init__(self) -> None:
        self.success: bool = False
        self.output_path: str = ""
        self.output_content: str = ""
        self.content_hash: str = ""  # 内容 hash，用于缓存判断
        self.errors: list[str] = []
        self.warnings: list[str] = []


class TypeScriptCompiler:
    """
    TypeScript 编译器
    
    将 JSON 用例定义编译为 TypeScript 测试文件
    
    使用门面模式整合:
    - VariableResolver: 变量解析
    - ElementResolver: 元素引用解析
    - StepEmitter: 步骤代码生成
    - Jinja2: 模板渲染
    """
    
    def __init__(
        self,
        templates_dir: str | None = None,
        output_dir: str | None = None,
    ) -> None:
        """
        初始化编译器
        
        Args:
            templates_dir: 模板目录路径（默认使用内置模板）
            output_dir: 输出目录路径
        """
        # 模板目录
        if templates_dir:
            self._templates_dir = Path(templates_dir)
        else:
            self._templates_dir = Path(__file__).parent / "templates"
        
        # 输出目录
        if output_dir:
            self._output_dir = Path(output_dir)
        else:
            # 默认输出到项目根目录的 midscene-executor/tests
            project_root = Path(__file__).parent.parent.parent.parent.parent.parent
            self._output_dir = project_root / "midscene-executor" / "tests"
        
        # 初始化 Jinja2 环境
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(self._templates_dir)),
            autoescape=select_autoescape(enabled_extensions=()),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        # 初始化组件
        self._variable_resolver = VariableResolver()
        self._element_resolver = ElementResolver()
        self._step_emitter = StepEmitter()
    
    def set_knowledge_service(self, service: Any) -> None:
        """设置知识库服务"""
        self._element_resolver.set_knowledge_service(service)
    
    async def compile(
        self,
        case: dict[str, Any],
        config: dict[str, Any] | None = None,
        global_variables: list[dict[str, Any]] | None = None,
        runtime_variables: dict[str, Any] | None = None,
        data_row: dict[str, Any] | None = None,
        write_to_file: bool = False,  # 是否写入文件（执行时使用）
    ) -> CompileResult:
        """
        编译用例
        
        Args:
            case: 用例定义（JSON）
            config: 执行配置
            global_variables: 全局变量列表
            runtime_variables: 运行时变量覆盖
            data_row: 数据驱动当前行
            
        Returns:
            编译结果
        """
        result = CompileResult()
        
        try:
            # 1. 构建编译上下文
            context = await self._build_context(
                case, config, global_variables, runtime_variables, data_row
            )
            
            # 2. 解析元素引用
            steps = case.get("steps_json", [])
            context.resolved_elements = await self._element_resolver.resolve_all(steps)
            
            # 3. 生成步骤代码
            compile_ctx = {
                "platform": context.platform.value,
                "variables": context.resolved_variables,
                "resolved_elements": context.resolved_elements,
            }
            context.steps_code = self._step_emitter.emit_all(steps, compile_ctx)
            
            # 4. 渲染模板
            template_name = self._get_template_name(context.platform)
            template = self._jinja_env.get_template(template_name)
            
            output_content = template.render(
                # 基本信息
                case_id=context.case_id,
                case_name=context.case_name,
                case_description=context.case_description,
                test_name=context.test_name or context.case_name,
                generated_at=datetime.now().isoformat(),
                
                # 变量
                input_variables=context.input_variables,
                
                # 配置
                test_timeout_ms=context.config.get("test_timeout_ms", 240000),
                step_timeout_ms=context.config.get("step_timeout_ms", 720000),
                hook_timeout_ms=context.config.get("hook_timeout_ms", 240000),
                wait_after_action_ms=context.config.get("wait_after_action_ms", 300),
                auto_dismiss_keyboard=context.config.get("auto_dismiss_keyboard", True),
                replanning_cycle_limit=context.config.get("replanning_cycle_limit", 20),
                generate_report=context.config.get("generate_report", True),
                ai_context=context.config.get("ai_action_context", ""),
                
                # 模型配置
                model_config=context.model_config,
                
                # 缓存
                cache_id=context.cache_id,
                cache_strategy=context.cache_strategy,
                
                # 启动
                launch_target=context.launch_target,
                launch_wait_ms=context.launch_wait_ms,
                
                # iOS 特定
                wda_host=context.config.get("wda_host", "localhost"),
                wda_port=context.config.get("wda_port", 8100),
                
                # 数据驱动
                data_driven=context.data_driven,
                test_data=context.test_data,
                data_fields=context.data_fields,
                data_label_field=context.data_label_field,
                
                # 报告合并
                enable_report_merger=context.enable_report_merger,
                
                # 步骤代码
                steps=context.steps_code,
            )
            
            # 5. 计算内容 hash
            import hashlib
            result.content_hash = hashlib.sha256(output_content.encode()).hexdigest()[:16]
            result.output_content = output_content
            result.success = True
            
            # 6. 可选：写入文件（执行时使用）
            if write_to_file:
                output_path = self._get_output_path(context)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(output_content, encoding="utf-8")
                result.output_path = str(output_path)
            
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
        
        return result
    
    async def _build_context(
        self,
        case: dict[str, Any],
        config: dict[str, Any] | None,
        global_variables: list[dict[str, Any]] | None,
        runtime_variables: dict[str, Any] | None,
        data_row: dict[str, Any] | None,
    ) -> CompileContext:
        """构建编译上下文"""
        context = CompileContext()
        
        # 基本信息
        context.case_id = case.get("id", "")
        context.case_name = case.get("name", "Unnamed Case")
        context.case_description = case.get("description", "")
        context.platform = Platform(case.get("platform", "android"))
        context.test_name = case.get("test_name", context.case_name)
        
        # 变量解析
        self._variable_resolver.set_global_variables(global_variables or [])
        self._variable_resolver.set_case_variables(case.get("input_variables"))
        self._variable_resolver.set_data_row(data_row)
        self._variable_resolver.set_runtime_variables(runtime_variables)
        
        context.input_variables = self._variable_resolver.get_variable_definitions()
        context.resolved_variables = self._variable_resolver.resolve_all()
        
        # 配置
        base_config = config or {}
        override_config = case.get("config_override") or {}
        context.config = {**base_config, **{k: v for k, v in override_config.items() if v is not None}}
        
        # 模型配置
        model_config = context.config.get("model_config")
        if model_config:
            context.model_config = model_config
        elif any(k in context.config for k in ["model_name", "model_base_url", "model_family"]):
            context.model_config = {
                "name": context.config.get("model_name", ""),
                "base_url": context.config.get("model_base_url", ""),
                "family": context.config.get("model_family", ""),
            }
        
        # 缓存配置
        cache_config = context.config.get("cache_config")
        if cache_config:
            context.cache_id = cache_config.get("cache_id")
            context.cache_strategy = cache_config.get("strategy")
        
        # 启动配置
        context.launch_target = case.get("launch_target")
        context.launch_wait_ms = context.config.get("launch_wait_ms", 3000)
        if context.platform == Platform.IOS:
            context.launch_wait_ms = context.config.get("launch_wait_ms", 5000)
        
        # 数据驱动
        data_set = case.get("data_set")
        if data_set and isinstance(data_set, list) and len(data_set) > 0:
            context.data_driven = True
            context.test_data = data_set
            context.data_fields = list(data_set[0].keys()) if data_set else []
            context.data_label_field = "_index"
        
        # 套件执行时启用报告合并
        context.enable_report_merger = context.config.get("suite_execution", False)
        
        return context
    
    def _get_template_name(self, platform: Platform) -> str:
        """获取平台对应的模板名称"""
        if platform == Platform.IOS:
            return "ios_case.ts.j2"
        return "android_case.ts.j2"
    
    def _get_output_path(self, context: CompileContext) -> Path:
        """获取输出文件路径"""
        platform_dir = "android" if context.platform == Platform.ANDROID else "ios"
        filename = f"case_{context.case_id}.test.ts"
        return self._output_dir / platform_dir / filename
    
    def get_env_variables(
        self,
        config: dict[str, Any] | None = None,
        runtime_variables: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """
        获取执行时需要的环境变量
        
        Args:
            config: 执行配置
            runtime_variables: 运行时变量
            
        Returns:
            环境变量字典
        """
        env = {}
        
        # 从系统环境变量继承 Midscene 配置（作为默认值）
        midscene_env_keys = [
            "MIDSCENE_MODEL_NAME",
            "MIDSCENE_MODEL_BASE_URL",
            "MIDSCENE_MODEL_API_KEY",
            "MIDSCENE_MODEL_FAMILY",
            "MIDSCENE_CACHE",
            "MIDSCENE_DEBUG_MODE",
        ]
        for key in midscene_env_keys:
            if os.environ.get(key):
                env[key] = os.environ[key]
        
        # 变量
        if runtime_variables:
            for name, value in runtime_variables.items():
                env[f"VAR_{name.upper()}"] = str(value) if value is not None else ""
        
        # 模型配置（覆盖默认值）
        if config:
            model_family = config.get("model_family", "")
            
            if config.get("model_name"):
                env["MIDSCENE_MODEL_NAME"] = config["model_name"]
            if config.get("model_api_key"):
                env["MIDSCENE_MODEL_API_KEY"] = config["model_api_key"]
            if model_family:
                env["MIDSCENE_MODEL_FAMILY"] = model_family
            # 所有模型都可以使用自定义 base_url（包括通过代理访问的 Gemini）
            if config.get("model_base_url"):
                env["MIDSCENE_MODEL_BASE_URL"] = config["model_base_url"]
            
            # AI 上下文
            if config.get("ai_action_context"):
                env["AI_CONTEXT"] = config["ai_action_context"]
            
            # 缓存 ID
            cache_config = config.get("cache_config")
            if cache_config and cache_config.get("cache_id"):
                env["CACHE_ID"] = cache_config["cache_id"]
            
            # iOS WDA 配置
            if config.get("wda_host"):
                env["WDA_HOST"] = str(config["wda_host"])
            if config.get("wda_port"):
                env["WDA_PORT"] = str(config["wda_port"])
        
        return env
