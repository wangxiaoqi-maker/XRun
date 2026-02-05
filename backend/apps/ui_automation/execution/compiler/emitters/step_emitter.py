"""
步骤代码生成器

使用策略模式和工厂方法，支持所有 Midscene API 的代码生成
"""
from typing import Any
from apps.ui_automation.execution.compiler.emitters.base import BaseStepStrategy
from apps.ui_automation.execution.models.enums import StepType, OnErrorAction


class StepEmitter:
    """
    步骤代码生成器
    
    使用策略模式管理不同类型步骤的代码生成
    """
    
    def __init__(self) -> None:
        """初始化并注册所有策略"""
        self._strategies: dict[str, BaseStepStrategy] = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self) -> None:
        """注册默认策略"""
        # 即时操作
        self.register(AiTapStrategy())
        self.register(AiInputStrategy())
        self.register(AiScrollStrategy())
        self.register(AiKeyboardPressStrategy())
        self.register(AiDoubleClickStrategy())
        self.register(AiHoverStrategy())
        self.register(AiRightClickStrategy())
        
        # 自动规划
        self.register(AiActStrategy())
        self.register(AiStrategy())
        
        # 数据提取
        self.register(AiQueryStrategy())
        self.register(AiAskStrategy())
        self.register(AiBooleanStrategy())
        self.register(AiNumberStrategy())
        self.register(AiStringStrategy())
        
        # 断言与等待
        self.register(AiAssertStrategy())
        self.register(AiWaitForStrategy())
        self.register(AiLocateStrategy())
        
        # 报告与调试
        self.register(RecordToReportStrategy())
        self.register(SleepStrategy())
        
        # 页面上下文
        self.register(FreezePageContextStrategy())
        self.register(UnfreezePageContextStrategy())
        
        # 平台特定 - Android
        self.register(BackStrategy())
        self.register(HomeStrategy())
        self.register(RecentAppsStrategy())
        self.register(AdbShellStrategy())
        
        # 平台特定 - iOS
        self.register(AppSwitcherStrategy())
        self.register(WdaRequestStrategy())
        
        # 流程控制
        self.register(LaunchStrategy())
        self.register(ConditionStrategy())
        self.register(LoopStrategy())
        self.register(TryCatchStrategy())
    
    def register(self, strategy: BaseStepStrategy) -> None:
        """注册步骤策略"""
        self._strategies[strategy.step_type] = strategy
    
    def emit(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        """
        生成步骤代码
        
        Args:
            step: 步骤定义
            context: 编译上下文
            
        Returns:
            生成的 TypeScript 代码
        """
        step_type = step.get("type", "")
        strategy = self._strategies.get(step_type)
        
        if not strategy:
            # 未知步骤类型，生成注释
            return f"// TODO: Unknown step type: {step_type}"
        
        # 生成基础代码
        code = strategy.generate(step, context)
        
        # 包装重试逻辑
        code = self._wrap_with_retry(step, code)
        
        # 添加步骤注释和日志
        code = self._add_step_comment(step, code, context)
        
        return code
    
    def emit_all(self, steps: list[dict[str, Any]], context: dict[str, Any]) -> str:
        """
        生成所有步骤代码
        
        Args:
            steps: 步骤列表
            context: 编译上下文
            
        Returns:
            生成的 TypeScript 代码（多行）
        """
        lines = []
        for i, step in enumerate(steps):
            # 更新上下文中的步骤索引
            ctx = {**context, "step_index": i}
            code = self.emit(step, ctx)
            lines.append(code)
        
        return "\n\n".join(lines)
    
    def _wrap_with_retry(self, step: dict[str, Any], code: str) -> str:
        """包装重试逻辑"""
        on_error = step.get("onError", OnErrorAction.FAIL.value)
        retry_count = step.get("retryCount", 0)
        
        if on_error != OnErrorAction.RETRY.value or retry_count <= 0:
            return code
        
        retry_delay = step.get("retryDelayMs", 1000)
        retry_backoff = step.get("retryBackoff", True)
        
        # 生成重试包装代码
        indent = "  "
        wrapped = f"for (let _retry = 0; _retry < {retry_count}; _retry++) {{\n"
        wrapped += f"{indent}try {{\n"
        
        # 缩进原始代码
        for line in code.split("\n"):
            wrapped += f"{indent}{indent}{line}\n"
        
        wrapped += f"{indent}{indent}break; // 成功则退出\n"
        wrapped += f"{indent}}} catch (error) {{\n"
        wrapped += f"{indent}{indent}console.warn(`Step failed, retry ${{_retry + 1}}/{retry_count}:`, error);\n"
        wrapped += f"{indent}{indent}if (_retry === {retry_count - 1}) throw error;\n"
        
        if retry_backoff:
            wrapped += f"{indent}{indent}await sleep({retry_delay} * (_retry + 1));\n"
        else:
            wrapped += f"{indent}{indent}await sleep({retry_delay});\n"
        
        wrapped += f"{indent}}}\n"
        wrapped += "}"
        
        return wrapped
    
    def _add_step_comment(self, step: dict[str, Any], code: str, context: dict[str, Any] = None) -> str:
        """添加步骤注释和日志输出"""
        step_id = step.get("id", "")
        step_name = step.get("name", "")
        step_index = context.get("step_index", 0) if context else 0
        step_num = step_index + 1  # 1-based 步骤编号
        
        # 生成步骤描述
        if step_name:
            desc = f"{step_name}"
        else:
            step_type = step.get("type", "unknown")
            target = step.get("target", "")
            desc = f"{step_type}"
            if target:
                desc += f" - {target[:50]}"
        
        # 添加 console.log 输出步骤信息，方便前端解析
        log_line = f'console.log("[Step {step_num}] {desc}");'
        
        if step_name:
            return f"// Step {step_num}: {step_name} (id: {step_id})\n{log_line}\n{code}"
        elif step_id:
            return f"// Step {step_num}: {step_id}\n{log_line}\n{code}"
        
        return f"// Step {step_num}\n{log_line}\n{code}"


# ==================== 具体策略实现 ====================

class AiTapStrategy(BaseStepStrategy):
    """aiTap 步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.AI_TAP.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        locator = self._resolve_locator(step, context)
        options = self._generate_options(step, ["deepThink", "cacheable"])
        
        if options:
            return f"await agent.aiTap('{locator}', {options});"
        return f"await agent.aiTap('{locator}');"


class AiInputStrategy(BaseStepStrategy):
    """aiInput 步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.AI_INPUT.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        locator = self._resolve_locator(step, context)
        value = step.get("value", "")
        mode = step.get("mode", "replace")
        
        # 处理变量引用
        if value.startswith("${") and value.endswith("}"):
            var_name = value[2:-1]
            value_expr = var_name
        else:
            value_expr = f"'{self._escape_string(value)}'"
        
        options_parts = [f"value: {value_expr}"]
        
        if mode != "replace":
            options_parts.append(f"mode: '{mode}'")
        
        # 添加其他选项
        for key in ["deepThink", "cacheable", "autoDismissKeyboard"]:
            if key in step.get("options", {}):
                val = step["options"][key]
                if isinstance(val, bool):
                    options_parts.append(f"{key}: {str(val).lower()}")
                else:
                    options_parts.append(f"{key}: {val}")
        
        options = "{ " + ", ".join(options_parts) + " }"
        return f"await agent.aiInput('{locator}', {options});"


class AiScrollStrategy(BaseStepStrategy):
    """aiScroll 步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.AI_SCROLL.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        locator = step.get("locator", "")
        scroll_type = step.get("scrollType", "singleAction")
        direction = step.get("direction", "down")
        distance = step.get("distance")
        
        options_parts = [f"scrollType: '{scroll_type}'"]
        
        if scroll_type == "singleAction":
            options_parts.append(f"direction: '{direction}'")
            if distance is not None:
                options_parts.append(f"distance: {distance}")
        
        options = "{ " + ", ".join(options_parts) + " }"
        
        if locator:
            return f"await agent.aiScroll('{self._escape_string(locator)}', {options});"
        return f"await agent.aiScroll(undefined, {options});"


class AiKeyboardPressStrategy(BaseStepStrategy):
    """aiKeyboardPress 步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.AI_KEYBOARD_PRESS.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        locator = self._resolve_locator(step, context)
        key_name = step.get("keyName", "Enter")
        
        options = f"{{ keyName: '{key_name}' }}"
        return f"await agent.aiKeyboardPress('{locator}', {options});"


class AiDoubleClickStrategy(BaseStepStrategy):
    """aiDoubleClick 步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.AI_DOUBLE_CLICK.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        locator = self._resolve_locator(step, context)
        options = self._generate_options(step, ["deepThink", "cacheable"])
        
        if options:
            return f"await agent.aiDoubleClick('{locator}', {options});"
        return f"await agent.aiDoubleClick('{locator}');"


class AiHoverStrategy(BaseStepStrategy):
    """aiHover 步骤策略（仅 Web）"""
    
    @property
    def step_type(self) -> str:
        return StepType.AI_HOVER.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        locator = self._resolve_locator(step, context)
        return f"await agent.aiHover('{locator}');"


class AiRightClickStrategy(BaseStepStrategy):
    """aiRightClick 步骤策略（仅 Web）"""
    
    @property
    def step_type(self) -> str:
        return StepType.AI_RIGHT_CLICK.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        locator = self._resolve_locator(step, context)
        return f"await agent.aiRightClick('{locator}');"


class AiActStrategy(BaseStepStrategy):
    """aiAct 步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.AI_ACT.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        prompt = step.get("prompt", "")
        options = self._generate_options(step, ["cacheable", "deepThink"])
        
        if options:
            return f"await agent.aiAct('{self._escape_string(prompt)}', {options});"
        return f"await agent.aiAct('{self._escape_string(prompt)}');"


class AiStrategy(BaseStepStrategy):
    """ai 步骤策略（aiAct 简写）"""
    
    @property
    def step_type(self) -> str:
        return StepType.AI.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        prompt = step.get("prompt", "")
        return f"await agent.ai('{self._escape_string(prompt)}');"


class AiQueryStrategy(BaseStepStrategy):
    """aiQuery 步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.AI_QUERY.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        query = step.get("query", "")
        output_var = step.get("outputVar", "_queryResult")
        
        return f"const {output_var} = await agent.aiQuery('{self._escape_string(query)}');"


class AiAskStrategy(BaseStepStrategy):
    """aiAsk 步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.AI_ASK.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        prompt = step.get("prompt", "")
        output_var = step.get("outputVar", "_askResult")
        
        return f"const {output_var} = await agent.aiAsk('{self._escape_string(prompt)}');"


class AiBooleanStrategy(BaseStepStrategy):
    """aiBoolean 步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.AI_BOOLEAN.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        prompt = step.get("prompt", "")
        output_var = step.get("outputVar", "_boolResult")
        
        return f"const {output_var} = await agent.aiBoolean('{self._escape_string(prompt)}');"


class AiNumberStrategy(BaseStepStrategy):
    """aiNumber 步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.AI_NUMBER.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        prompt = step.get("prompt", "")
        output_var = step.get("outputVar", "_numResult")
        
        return f"const {output_var} = await agent.aiNumber('{self._escape_string(prompt)}');"


class AiStringStrategy(BaseStepStrategy):
    """aiString 步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.AI_STRING.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        prompt = step.get("prompt", "")
        output_var = step.get("outputVar", "_strResult")
        
        return f"const {output_var} = await agent.aiString('{self._escape_string(prompt)}');"


class AiAssertStrategy(BaseStepStrategy):
    """aiAssert 步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.AI_ASSERT.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        assertion = step.get("assertion", "")
        error_msg = step.get("errorMsg", "")
        
        if error_msg:
            return f"await agent.aiAssert('{self._escape_string(assertion)}', '{self._escape_string(error_msg)}');"
        return f"await agent.aiAssert('{self._escape_string(assertion)}');"


class AiWaitForStrategy(BaseStepStrategy):
    """aiWaitFor 步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.AI_WAIT_FOR.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        assertion = step.get("assertion", "")
        timeout_ms = step.get("timeoutMs", 30000)
        interval_ms = step.get("checkIntervalMs", 3000)
        
        options = f"{{ timeoutMs: {timeout_ms}, checkIntervalMs: {interval_ms} }}"
        return f"await agent.aiWaitFor('{self._escape_string(assertion)}', {options});"


class AiLocateStrategy(BaseStepStrategy):
    """aiLocate 步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.AI_LOCATE.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        locator = self._resolve_locator(step, context)
        output_var = step.get("outputVar", "_locateResult")
        options = self._generate_options(step, ["deepThink", "cacheable"])
        
        if options:
            return f"const {output_var} = await agent.aiLocate('{locator}', {options});"
        return f"const {output_var} = await agent.aiLocate('{locator}');"


class RecordToReportStrategy(BaseStepStrategy):
    """recordToReport 步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.RECORD_TO_REPORT.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        title = step.get("title", "untitled")
        content = step.get("content", "")
        
        if content:
            return f"await agent.recordToReport('{self._escape_string(title)}', {{ content: '{self._escape_string(content)}' }});"
        return f"await agent.recordToReport('{self._escape_string(title)}');"


class SleepStrategy(BaseStepStrategy):
    """sleep 步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.SLEEP.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        duration_ms = step.get("durationMs", 1000)
        return f"await sleep({duration_ms});"


class FreezePageContextStrategy(BaseStepStrategy):
    """freezePageContext 步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.FREEZE_PAGE_CONTEXT.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        return "await agent.freezePageContext();"


class UnfreezePageContextStrategy(BaseStepStrategy):
    """unfreezePageContext 步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.UNFREEZE_PAGE_CONTEXT.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        return "await agent.unfreezePageContext();"


# ==================== 平台特定策略 ====================

class BackStrategy(BaseStepStrategy):
    """back 步骤策略（Android）"""
    
    @property
    def step_type(self) -> str:
        return StepType.BACK.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        return "await agent.back();"


class HomeStrategy(BaseStepStrategy):
    """home 步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.HOME.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        return "await agent.home();"


class RecentAppsStrategy(BaseStepStrategy):
    """recentApps 步骤策略（Android）"""
    
    @property
    def step_type(self) -> str:
        return StepType.RECENT_APPS.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        return "await agent.recentApps();"


class AdbShellStrategy(BaseStepStrategy):
    """adbShell 步骤策略（Android）"""
    
    @property
    def step_type(self) -> str:
        return StepType.ADB_SHELL.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        command = step.get("command", "")
        output_var = step.get("outputVar")
        
        if output_var:
            return f"const {output_var} = await agent.runAdbShell('{self._escape_string(command)}');"
        return f"await agent.runAdbShell('{self._escape_string(command)}');"


class AppSwitcherStrategy(BaseStepStrategy):
    """appSwitcher 步骤策略（iOS）"""
    
    @property
    def step_type(self) -> str:
        return StepType.APP_SWITCHER.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        return "await agent.appSwitcher();"


class WdaRequestStrategy(BaseStepStrategy):
    """wdaRequest 步骤策略（iOS）"""
    
    @property
    def step_type(self) -> str:
        return StepType.WDA_REQUEST.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        method = step.get("method", "GET")
        endpoint = step.get("endpoint", "")
        output_var = step.get("outputVar")
        
        if output_var:
            return f"const {output_var} = await agent.runWdaRequest('{method}', '{self._escape_string(endpoint)}');"
        return f"await agent.runWdaRequest('{method}', '{self._escape_string(endpoint)}');"


class LaunchStrategy(BaseStepStrategy):
    """
    launch/scheme 步骤策略
    
    区分两种场景：
    1. Bundle ID 启动（如 com.xxx.app）-> 使用 Midscene agent.launch()
    2. Scheme URL 跳转（如 myapp://page）-> 使用 WDA 原生 API
    """
    
    @property
    def step_type(self) -> str:
        return StepType.LAUNCH.value
    
    def _is_scheme_url(self, target: str) -> bool:
        """判断是否为 Scheme URL"""
        if not target:
            return False
        # Scheme URL 通常包含 :// 或以 http/https 开头
        return "://" in target
    
    def _is_bundle_id(self, target: str) -> bool:
        """判断是否为 Bundle ID"""
        if not target:
            return False
        # Bundle ID 通常是点分隔的标识符，如 com.xxx.app
        # 不包含 :// 且包含至少一个点
        return "://" not in target and "." in target
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        # 获取跳转目标（支持多个字段名）
        target = step.get("target", "") or step.get("url", "") or step.get("value", "") or step.get("locator", "")
        wait_ms = step.get("waitMs", 2000)
        platform = context.get("platform", "ios").lower()
        
        if not target:
            return "// ERROR: launch target is empty"
        
        # 根据目标类型生成不同代码
        if self._is_scheme_url(target):
            # Scheme URL 跳转 - 使用 WDA 原生 API（参考 IOSSchemeService）
            if platform == "ios":
                code = self._generate_ios_scheme_jump(target, wait_ms)
            else:
                # Android 使用 adb shell am start
                code = self._generate_android_scheme_jump(target, wait_ms)
        elif self._is_bundle_id(target):
            # Bundle ID 启动 - 使用 Midscene agent.launch()
            code = f"await agent.launch('{self._escape_string(target)}');\n"
            code += f"await sleep({wait_ms});"
        else:
            # 无法识别，尝试使用 agent.launch()
            code = f"await agent.launch('{self._escape_string(target)}');\n"
            code += f"await sleep({wait_ms});"
        
        return code
    
    def _generate_ios_scheme_jump(self, url: str, wait_ms: int) -> str:
        """生成 iOS Scheme 跳转代码（使用 WDA 原生 API）"""
        # 参考 IOSSchemeService 的实现，直接调用 WDA HTTP API
        code = f"""// iOS Scheme 跳转 - 使用 WDA 原生 API
const wdaHost = process.env.WDA_HOST || 'localhost';
const wdaPort = process.env.WDA_PORT || '8100';
const wdaUrl = `http://${{wdaHost}}:${{wdaPort}}`;

// 1. 创建 WDA Session
const sessionResp = await fetch(`${{wdaUrl}}/session`, {{
  method: 'POST',
  headers: {{ 'Content-Type': 'application/json' }},
  body: JSON.stringify({{ capabilities: {{}} }})
}});
const sessionData = await sessionResp.json();
const sessionId = sessionData.sessionId || sessionData.value?.sessionId;

if (sessionId) {{
  // 2. 发送 Scheme 跳转指令
  await fetch(`${{wdaUrl}}/session/${{sessionId}}/url`, {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ url: '{self._escape_string(url)}' }})
  }});
  console.log('[Scheme] 跳转成功: {self._escape_string(url)}');
}} else {{
  console.error('[Scheme] 无法获取 WDA Session ID');
}}
await sleep({wait_ms});"""
        return code
    
    def _generate_android_scheme_jump(self, url: str, wait_ms: int) -> str:
        """生成 Android Scheme 跳转代码"""
        # Android 使用 adb shell am start 命令
        code = f"""// Android Scheme 跳转
const {{ execSync }} = require('child_process');
try {{
  execSync(`adb shell am start -a android.intent.action.VIEW -d "{self._escape_string(url)}"`);
  console.log('[Scheme] Android 跳转成功: {self._escape_string(url)}');
}} catch (e) {{
  console.error('[Scheme] Android 跳转失败:', e.message);
}}
await sleep({wait_ms});"""
        return code


# ==================== 流程控制策略 ====================

class ConditionStrategy(BaseStepStrategy):
    """条件执行步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.CONDITION.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        condition = step.get("condition", "")
        then_steps = step.get("thenSteps", [])
        else_steps = step.get("elseSteps", [])
        
        # 解析条件表达式
        # 支持 ${varName} 和 aiQuery 条件
        if condition.startswith("${"):
            # 变量条件
            var_name = condition[2:-1]
            cond_expr = var_name
        else:
            # AI 查询条件
            cond_expr = f"await agent.aiBoolean('{self._escape_string(condition)}')"
        
        code = f"if ({cond_expr}) {{\n"
        
        # 生成 then 分支
        emitter = StepEmitter()
        for s in then_steps:
            step_code = emitter.emit(s, context)
            for line in step_code.split("\n"):
                code += f"  {line}\n"
        
        code += "}"
        
        # 生成 else 分支
        if else_steps:
            code += " else {\n"
            for s in else_steps:
                step_code = emitter.emit(s, context)
                for line in step_code.split("\n"):
                    code += f"  {line}\n"
            code += "}"
        
        return code


class LoopStrategy(BaseStepStrategy):
    """循环执行步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.LOOP.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        loop_count = step.get("count", 1)
        loop_var = step.get("loopVar", "_i")
        body_steps = step.get("bodySteps", [])
        
        code = f"for (let {loop_var} = 0; {loop_var} < {loop_count}; {loop_var}++) {{\n"
        
        emitter = StepEmitter()
        for s in body_steps:
            step_code = emitter.emit(s, context)
            for line in step_code.split("\n"):
                code += f"  {line}\n"
        
        code += "}"
        return code


class TryCatchStrategy(BaseStepStrategy):
    """try-catch 步骤策略"""
    
    @property
    def step_type(self) -> str:
        return StepType.TRY_CATCH.value
    
    def generate(self, step: dict[str, Any], context: dict[str, Any]) -> str:
        try_steps = step.get("trySteps", [])
        catch_steps = step.get("catchSteps", [])
        finally_steps = step.get("finallySteps", [])
        
        code = "try {\n"
        
        emitter = StepEmitter()
        for s in try_steps:
            step_code = emitter.emit(s, context)
            for line in step_code.split("\n"):
                code += f"  {line}\n"
        
        code += "} catch (error) {\n"
        code += "  console.error('Step failed:', error);\n"
        
        for s in catch_steps:
            step_code = emitter.emit(s, context)
            for line in step_code.split("\n"):
                code += f"  {line}\n"
        
        code += "}"
        
        if finally_steps:
            code += " finally {\n"
            for s in finally_steps:
                step_code = emitter.emit(s, context)
                for line in step_code.split("\n"):
                    code += f"  {line}\n"
            code += "}"
        
        return code
